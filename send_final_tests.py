#!/usr/bin/env python3

import csv
import pathlib
import sys
import logging # For type hinting
import urllib.parse # Added for JQL link generation
import uuid # Add this import
import json # Added for parsing ManualTestSteps

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

from jira_client import JiraClient # Assuming jira_client.py is in the same directory or PYTHONPATH
from logger_setup import setup_logger # Assuming logger_setup.py is available

# Setup logger for this script
logger = setup_logger(__name__, log_file="send_final_tests.log")

# Generate a unique ID for this run, similar to send_figma_tests_all_tests.py
RUN_ID = uuid.uuid4().hex[:8]

# --- Constants for column names from final_tests.txt ---
COL_TEST_CASE_IDENTIFIER = "TestCaseIdentifier"
COL_SUMMARY = "Summary"
COL_DESCRIPTION = "Description"
COL_PRIORITY = "Priority"
COL_LABELS_FILE = "Labels" # Renamed to avoid conflict with 'labels' variable
COL_MANUAL_TEST_STEPS = "ManualTestSteps" # New field for test steps
COL_BOARD = "Board"
COL_TEST_REPOSITORY_PATH = "testRepositoryPath"
COL_TEST_CASE_TYPE = "testCaseType"

# Path to the input file
FINAL_TESTS_FILE_PATH = pathlib.Path("create_final_tests/artifacts/final_tests.txt")

# Custom Field IDs from config (optional, will be None if not set)
CUSTOMFIELD_TEST_REPOSITORY_PATH = getattr(config, "CUSTOMFIELD_TEST_REPOSITORY_PATH", None)
CUSTOMFIELD_TEST_CASE_TYPE = getattr(config, "CUSTOMFIELD_TEST_CASE_TYPE", None)

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

def parse_test_cases(file_path: pathlib.Path) -> list[dict]:
    """Parses test cases from the CSV file."""
    if not file_path.exists():
        logger.error(f"❌ Input file not found: {file_path}")
        return []

    test_cases: list[dict] = []
    try:
        # Use 'utf-8-sig' to handle potential BOM (Byte Order Mark)
        # newline='' is important for csv module to handle line endings correctly
        with file_path.open(mode='r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            
            if not reader.fieldnames: # Check if the file is empty or has no header
                logger.warning(f"⚠️ File {file_path} is empty or contains no header row.")
                return []

            for i, row in enumerate(reader):
                # Basic validation: ensure essential fields like summary are present
                if not row.get(COL_SUMMARY, "").strip():
                    logger.warning(
                        f"Skipping row {i+2} in {file_path} (1-based index, including header): "
                        f"{COL_SUMMARY} is empty or missing."
                    )
                    continue
                test_cases.append(row)
        
        if test_cases:
            logger.info(f"✅ Successfully parsed {len(test_cases)} test cases from {file_path}.")
        else:
            logger.info(f"❌ No valid test cases found in {file_path} after parsing (or file was empty/header-only).")

    except Exception as e:
        logger.error(f"❌ Failed to read or parse CSV file {file_path}: {e}")
        return [] 
    return test_cases

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
    created_issue_keys = [] # To store keys of created issues

    for tc_data in test_cases:
        summary = tc_data.get(COL_SUMMARY, "No Summary Provided").strip()
        description_original = tc_data.get(COL_DESCRIPTION, "").strip()
        
        tc_identifier_from_file = tc_data.get(COL_TEST_CASE_IDENTIFIER, "N/A").strip()
        description_final = f"{description_original}\n\n--- Source Test Case Details ---\n{COL_TEST_CASE_IDENTIFIER}: {tc_identifier_from_file}"

        test_repo_path_val = tc_data.get(COL_TEST_REPOSITORY_PATH, "").strip()
        test_case_type_val = tc_data.get(COL_TEST_CASE_TYPE, "").strip()

        labels_from_file_str = tc_data.get(COL_LABELS_FILE, "").strip()
        labels_from_file_list = [label.strip() for label in labels_from_file_str.split(',') if label.strip()]
        
        board_label = tc_data.get(COL_BOARD, "").strip()
        
        priority_val = tc_data.get(COL_PRIORITY, "").strip()
        priority_label = f"Priority_{priority_val.replace(' ', '_')}" if priority_val else ""

        all_labels_set = set(jira_labels_from_config) # Start with labels from config
        all_labels_set.update(labels_from_file_list) # Add labels from file
        if board_label:
            all_labels_set.add(board_label) # Add board as a label
        if priority_label:
            all_labels_set.add(priority_label) # Add priority as a label
        all_labels_set.add(f"runid_{RUN_ID}") # Add runid label
        
        final_labels = [str(lbl) for lbl in all_labels_set if lbl] # Ensure all are non-empty strings

        # --- Updated logic for processing ManualTestSteps ---
        manual_test_steps_str = tc_data.get(COL_MANUAL_TEST_STEPS, "").strip()
        steps_data = []

        if manual_test_steps_str:
            try:
                parsed_json_list = json.loads(manual_test_steps_str)
                if isinstance(parsed_json_list, list):
                    for item in parsed_json_list:
                        if isinstance(item, dict) and "fields" in item and isinstance(item["fields"], dict):
                            action = str(item["fields"].get("Action", "N/A")).strip()
                            data_val = str(item["fields"].get("Data", "N/A")).strip()
                            expected_result = str(item["fields"].get("Expected Result", "N/A")).strip()
                            steps_data.append({
                                "fields": {
                                    "Action": action,
                                    "Data": data_val,
                                    "Expected Result": expected_result
                                }
                            })
                        else:
                            logger.warning(f"Skipping malformed step item in ManualTestSteps for '{summary}': {item}")
                    
                    if not steps_data and parsed_json_list: # JSON was a list but all items were malformed
                        logger.warning(f"ManualTestSteps for '{summary}' contained a list but no valid step structures. Raw: '{manual_test_steps_str}'. Creating a placeholder step.")
                        steps_data = [{"fields": {"Action": "Malformed steps data in list", "Data": "Review ManualTestSteps field", "Expected Result": "No valid steps extracted"}}]
                
                else: # Parsed JSON is not a list
                    logger.warning(f"ManualTestSteps for '{summary}' is not a JSON list. Raw: '{manual_test_steps_str}'. Creating a placeholder step.")
                    steps_data = [{"fields": {"Action": "ManualTestSteps not a JSON list", "Data": "Review ManualTestSteps field", "Expected Result": "Format error"}}]
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse ManualTestSteps JSON for '{summary}': {e}. Raw data: '{manual_test_steps_str}'. Creating a placeholder step.")
                steps_data = [{"fields": {"Action": "Invalid JSON in ManualTestSteps", "Data": "Review ManualTestSteps field", "Expected Result": "JSON parse error"}}]
        
        if not steps_data: # If ManualTestSteps was empty, or parsing failed to produce any steps
            logger.info(f"No ManualTestSteps provided or parsed for '{summary}'. Creating with a default placeholder step.")
            steps_data = [{"fields": {"Action": "No steps defined", "Data": "", "Expected Result": ""}}]
        # --- End of updated logic for processing ManualTestSteps ---

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
            if issue_key := issue.get('key'): # Store the key if present
                created_issue_keys.append(issue_key)
        except Exception as e:
            logger.error(f"❌ Failed to create Jira issue for summary '{summary}' (ID: {tc_identifier_from_file}). Error: {e}")
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
    elif created_issue_count > 0: # Should not happen if keys were captured correctly
        logger.warning("Issues were created, but their keys could not be retrieved for the JQL link.")
    else:
        logger.info("No Jira issues were created in this run.")

if __name__ == "__main__":
    create_jira_issues_from_final_tests() 