import json
import urllib.parse
import uuid
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError

# Attempt to import config and handle if not found
try:
    import config
except ImportError:
    raise SystemExit(
        "ERROR: config.py not found. Please create it from config_template.py and fill in your details."
    )

from jira_client import JiraClient
from logger_setup import setup_logger

logger = setup_logger(__name__, log_file="send_final_tests.log")

RUN_ID = uuid.uuid4().hex[:8]
SCHEMA_PATH = Path("create_final_tests/artifacts/json_scheme.yml")
CSV_OUTPUT_PATH = Path("create_final_tests/artifacts/component_tests.csv")

CUSTOMFIELD_TEST_REPOSITORY_PATH = getattr(config, "CUSTOMFIELD_TEST_REPOSITORY_PATH", None)
CUSTOMFIELD_TEST_CASE_TYPE = getattr(config, "CUSTOMFIELD_TEST_CASE_TYPE", None)

with SCHEMA_PATH.open("r", encoding="utf-8") as f:
    TEST_SCHEMA = yaml.safe_load(f)["components"]["schemas"]["TestCase"]


def check_core_config_settings() -> bool:
    required_configs = [
        "JIRA_URL",
        "JIRA_PROJECT_KEY",
        "JIRA_USERNAME",
        "JIRA_PASSWORD",
        "ISSUE_TYPE",
        "XRAY_STEPS_FIELD",
    ]
    missing = [attr for attr in required_configs if not getattr(config, attr, None)]
    if missing:
        logger.error(
            f"❌ Missing or empty required configurations in config.py: {', '.join(missing)}. "
            "Please ensure these are set for Jira connection and issue creation."
        )
        return False
    return True


def parse_test_cases(file_path: Path) -> list[dict]:
    if not file_path.exists():
        logger.error(f"❌ Input file not found: {file_path}")
        return []
    try:
        tests = json.loads(file_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in {file_path}: {e}")
        return []
    if not isinstance(tests, list):
        logger.error("❌ Root JSON element must be an array of test cases.")
        return []

    valid_tests: list[dict] = []
    for i, tc in enumerate(tests, 1):
        try:
            validate(tc, TEST_SCHEMA)
            valid_tests.append(tc)
        except ValidationError as ve:
            logger.warning(f"⚠️ Test #{i} schema violation: {ve.message} — skipped.")

    logger.info(f"✅ Parsed {len(valid_tests)}/{len(tests)} valid test cases from {file_path}.")
    return valid_tests


def send_tests_from_json(json_file_path: str, download_csv: bool = False) -> bool:
    """Parse test cases from json_file_path and create Jira issues.

    Args:
        json_file_path: Path to JSON file with test cases.
        download_csv: If True, export created issues as CSV to
            ``create_final_tests/artifacts/component_tests.csv``.
    """
    logger.info("🚀 Starting script to send final tests to Jira...")

    if not check_core_config_settings():
        logger.error("❌ Halting script due to missing or invalid core Jira configuration.")
        return False

    jira_labels_from_config = []
    if hasattr(config, "JIRA_LABELS"):
        if isinstance(config.JIRA_LABELS, list):
            jira_labels_from_config = config.JIRA_LABELS
        else:
            logger.warning(
                "JIRA_LABELS in config.py is not a list. It will be ignored. Please define it as a list of strings, e.g., ['label1', 'label2']."
            )
    else:
        logger.info("⚠️ JIRA_LABELS not found in config.py. No additional global labels will be added from config.")

    jira_client = JiraClient(
        base_url=config.JIRA_URL,
        username=config.JIRA_USERNAME,
        password=config.JIRA_PASSWORD,
    )

    file_path = Path(json_file_path)
    test_cases = parse_test_cases(file_path)
    if not test_cases:
        logger.info("❌ No test cases to process. Exiting.")
        return False

    created_issue_count = 0
    failed_issue_count = 0
    created_issue_keys = []

    for tc_data in test_cases:
        summary = tc_data.get("summary", "No Summary Provided").strip()
        description = tc_data.get("description", "")
        test_repo_path_val = tc_data.get("testRepositoryPath", "").strip()
        test_case_type_val = tc_data.get("testCaseType", "").strip()
        labels_from_file_list = tc_data.get("labels", [])

        all_labels_set = set(jira_labels_from_config)
        all_labels_set.update(labels_from_file_list)
        all_labels_set.add(f"runid_{RUN_ID}")

        final_labels = [str(lbl) for lbl in all_labels_set if lbl]

        steps_data = []
        for step in tc_data.get("steps", []):
            steps_data.append(
                {
                    "fields": {
                        "Action": step.get("action", "").strip(),
                        "Data": step.get("data", "").strip(),
                        "Expected Result": step.get("result", "").strip(),
                    }
                }
            )
        if not steps_data:
            logger.warning(
                f"No 'steps' found in JSON for '{summary}'. Injecting a placeholder step."
            )
            steps_data = [
                {
                    "fields": {
                        "Action": "No steps defined",
                        "Data": f"{{code:json}}{tc_data}{{code}}",
                        "Expected Result": "",
                    }
                }
            ]

        logger.info(f"Attempting to create Jira issue for: '{summary}'")
        try:
            issue = jira_client.create_issue(
                project_key=config.JIRA_PROJECT_KEY,
                summary=summary,
                description=description,
                issue_type=config.ISSUE_TYPE,
                xray_steps_field=config.XRAY_STEPS_FIELD,
                steps_data=steps_data,
                labels=final_labels,
                priority=tc_data.get("priority", "Normal"),
                custom_field_test_repository_path_id=CUSTOMFIELD_TEST_REPOSITORY_PATH,
                test_repository_path_value=test_repo_path_val,
                custom_field_test_case_type_id=CUSTOMFIELD_TEST_CASE_TYPE,
                test_case_type_value=test_case_type_val,
            )
            logger.success(
                f"✅ Successfully created Jira issue {issue.get('key', 'UNKNOWN_KEY')} for: '{summary}'"
            )
            created_issue_count += 1
            if issue_key := issue.get("key"):
                created_issue_keys.append(issue_key)
        except Exception as e:
            logger.error(f"❌ Failed to create Jira issue for summary '{summary}'. Error: {e}")
            failed_issue_count += 1

    logger.info("--- Script Finished ---")
    logger.info(f"✅ Successfully created issues: {created_issue_count}")
    logger.info(f"❌ Failed to create issues: {failed_issue_count}")

    if created_issue_keys:
        jql = "issuekey in (" + ", ".join(f'"{key}"' for key in created_issue_keys) + ")"
        encoded_jql = urllib.parse.quote(jql)
        jira_url_base = config.JIRA_URL.rstrip('/')
        jira_link = f"{jira_url_base}/issues/?jql={encoded_jql}"
        logger.info("🔗 Link to created Jira issues:")
        logger.info(jira_link)
        if download_csv:
            logger.info("-" * 20)
            jira_client.download_issues_csv(jql=jql, output_path=CSV_OUTPUT_PATH)
    elif created_issue_count > 0:
        logger.warning("Issues were created, but their keys could not be retrieved for the JQL link.")
    else:
        logger.info("No Jira issues were created in this run.")

    return failed_issue_count == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Send test cases from a JSON file to Jira"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the JSON file containing test cases"
    )
    parser.add_argument(
        "--download-csv",
        action="store_true",
        help="Download created issues as CSV to artifacts/component_tests.csv",
    )
    args = parser.parse_args()

    if send_tests_from_json(args.input, download_csv=args.download_csv):
        print("✅ Tests successfully sent to Jira")
    else:
        print("❌ Failed to send tests to Jira")
        exit(1)
