#!/usr/bin/env python3

import json
import sys
import urllib.parse
import uuid
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError

# Attempt to import config and handle if not found
try:
    import config
except ImportError:
    print(
        "ERROR: config.py not found. "
        "Please create it from config_template.py and fill in your details.",
        file=sys.stderr
    )
    sys.exit(1)

from jira_client import JiraClient  # Assuming jira_client.py is in the same directory or PYTHONPATH
from logger_setup import setup_logger  # Assuming logger_setup.py is available

# Setup logger for this script
logger = setup_logger(__name__, log_file="send_final_tests.log")

# Generate a unique ID for this run, similar to send_figma_tests_all_tests.py
RUN_ID = uuid.uuid4().hex[:8]

# Path to the input file
FINAL_TESTS_FILE_PATH = Path("create_final_tests/artifacts/final_tests.json")
SCHEMA_PATH = Path("create_final_tests/artifacts/json_scheme.yml")

# Custom Field IDs from config (optional, will be None if not set)
CUSTOMFIELD_TEST_REPOSITORY_PATH = getattr(config, "CUSTOMFIELD_TEST_REPOSITORY_PATH", None)
CUSTOMFIELD_TEST_CASE_TYPE = getattr(config, "CUSTOMFIELD_TEST_CASE_TYPE", None)

with SCHEMA_PATH.open("r", encoding="utf-8") as f:
    TEST_SCHEMA = yaml.safe_load(f)["components"]["schemas"]["TestCase"]


def check_core_config_settings() -> bool:
    """Validates that essential Jira connection settings are present in config.py."""
    required_configs = [
        "JIRA_URL", "JIRA_PROJECT_KEY", "JIRA_USERNAME", "JIRA_PASSWORD",
        "ISSUE_TYPE", "XRAY_STEPS_FIELD"
    ]
    missing_configs = []
    for attr in required_configs:
        if not hasattr(config, attr) or not getattr(config, attr):
            missing_configs.append(attr)

    if missing_configs:
        logger.error(
            f"❌ Missing or empty required configurations in config.py: {', '.join(missing_configs)}. "
            "Please ensure these are set for Jira connection and issue creation."
        )
        return False
    return True


def parse_test_cases(file_path: Path = FINAL_TESTS_FILE_PATH) -> list[dict]:
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
            validate(tc, TEST_SCHEMA)  # raises ValidationError on mismatch
            valid_tests.append(tc)
        except ValidationError as ve:
            logger.warning(f"⚠️ Test #{i} schema violation: {ve.message} — skipped.")

    logger.info(f"✅ Parsed {len(valid_tests)}/{len(tests)} valid test cases from {file_path}.")
    return valid_tests


def create_jira_issues_from_final_tests():
    """Main function to read test cases and create Jira issues."""
    logger.info("🚀 Starting script to send final tests to Jira...")

    if not check_core_config_settings():
        logger.error("❌ Halting script due to missing or invalid core Jira configuration.")
        return

    # Get JIRA_LABELS from config, defaulting to an empty list if not found or wrong type
    jira_labels_from_config = []
    if hasattr(config, "JIRA_LABELS"):
        if isinstance(config.JIRA_LABELS, list):
            jira_labels_from_config = config.JIRA_LABELS
        else:
            logger.warning(
                "JIRA_LABELS in config.py is not a list. It will be ignored. "
                "Please define it as a list of strings, e.g., ['label1', 'label2']."
            )
    else:
        logger.info("⚠️ JIRA_LABELS not found in config.py. No additional global labels will be added from config.")

    jira_client = JiraClient(
        base_url=config.JIRA_URL,
        username=config.JIRA_USERNAME,
        password=config.JIRA_PASSWORD
    )

    test_cases = parse_test_cases(FINAL_TESTS_FILE_PATH)
    if not test_cases:
        logger.info("❌ No test cases to process. Exiting.")
        return

    created_issue_count = 0
    failed_issue_count = 0
    created_issue_keys = []  # To store keys of created issues

    for tc_data in test_cases:
        summary = tc_data.get("summary", "No Summary Provided").strip()

        description_original = tc_data.get("description", "")
        tc_identifier_from_file = tc_data.get("testCaseIdentifier", "N/A")
        # todo use only if present
        description_final = (
            f"{description_original}\n\n--- Source Test Case Details ---\n"
            f"TestCaseIdentifier: {tc_identifier_from_file}"
        )

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
                        "Expected Result": step.get("result", "").strip()
                    }
                }
            )
        # If for some reason the JSON had no steps (violating minItems:1), you could fallback:
        if not steps_data:
            logger.warning(
                f"No 'steps' found in JSON for '{summary}'. Injecting a placeholder step.")
            steps_data = [
                {
                    "fields": {
                        "Action": "No steps defined",
                        "Data": f"{{code:json}}{tc_data}{{code}}",
                        "Expected Result": ""
                    }
                }
            ]

        logger.info(f"Attempting to create Jira issue for: '{summary}' (ID from file: {tc_identifier_from_file})")
        try:
            issue = jira_client.create_issue(
                project_key=config.JIRA_PROJECT_KEY,
                summary=summary,
                description=description_final,
                issue_type=config.ISSUE_TYPE,
                xray_steps_field=config.XRAY_STEPS_FIELD,
                steps_data=steps_data,
                labels=final_labels,
                custom_field_test_repository_path_id=CUSTOMFIELD_TEST_REPOSITORY_PATH,
                test_repository_path_value=test_repo_path_val,
                custom_field_test_case_type_id=CUSTOMFIELD_TEST_CASE_TYPE,
                test_case_type_value=test_case_type_val
            )
            logger.success(f"✅ Successfully created Jira issue {issue.get('key', 'UNKNOWN_KEY')} for: '{summary}'")
            created_issue_count += 1
            if issue_key := issue.get('key'):
                created_issue_keys.append(issue_key)
        except Exception as e:
            logger.error(
                f"❌ Failed to create Jira issue for summary '{summary}' (ID: {tc_identifier_from_file}). Error: {e}"
            )
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
    elif created_issue_count > 0:
        logger.warning("Issues were created, but their keys could not be retrieved for the JQL link.")
    else:
        logger.info("No Jira issues were created in this run.")


if __name__ == "__main__":
    create_jira_issues_from_final_tests()
