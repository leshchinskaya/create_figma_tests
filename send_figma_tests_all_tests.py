#!/usr/bin/env python3

import pathlib
import requests # Keep for requests.exceptions used in some places
from collections import defaultdict
import urllib.parse
import datetime # Add this import
import uuid # Add this import
import csv # Add this import
import subprocess # Add this import
import os # Add this import

from logger_setup import setup_logger # Import the setup function
import config # Assuming config.py is in the same directory or PYTHONPATH
from figma_client import FigmaClient, parse_file_key, sanitize # Import necessary items
from jira_client import JiraClient # Import JiraClient

# -------- Logging Setup ---------------------------------------------------- #
logger = setup_logger(__name__) # Use the setup function

# -------- Figma Configuration (some might be directly used) ---------------- #
FIGMA_FILE_URL = config.FIGMA_FILE_URL
FIGMA_TOKEN = config.FIGMA_TOKEN # Used to init FigmaClient
FIGMA_SCALE = config.FIGMA_SCALE

# === Jira Configuration (some might be directly used) ===
JIRA_URL = config.JIRA_URL # Used to init JiraClient
JIRA_PROJECT_KEY = config.JIRA_PROJECT_KEY
JIRA_USERNAME = config.JIRA_USERNAME # Used to init JiraClient
JIRA_PASSWORD = config.JIRA_PASSWORD # Used to init JiraClient
JIRA_LABELS = getattr(config, "JIRA_LABELS", []) # User-defined labels, default to empty list
ISSUE_TYPE = config.ISSUE_TYPE # Or keep as "Test" if not in config
XRAY_STEPS_FIELD = config.XRAY_STEPS_FIELD

# Custom Field IDs from config
CUSTOMFIELD_TEST_REPOSITORY_PATH = getattr(config, "CUSTOMFIELD_TEST_REPOSITORY_PATH", None)
CUSTOMFIELD_TEST_CASE_TYPE = getattr(config, "CUSTOMFIELD_TEST_CASE_TYPE", None)

# ---------- Filtering Configuration ---------------------------------------- #
FRAME_LIMIT = config.FRAME_LIMIT # Default to 1 if not in config, or set here
ELEMENT_BANNED = config.ELEMENT_BANNED
ELEMENT_INCLUDE = config.ELEMENT_INCLUDE
FRAME_BANNED = [x.lower() for x in config.FRAME_BANNED]
FRAME_INCLUDE = [x.lower() for x in config.FRAME_INCLUDE]

# ---------- Output Directory ----------------------------------------------- #
RUN_ID = uuid.uuid4().hex[:8] # Generate a unique ID for this run
OUT_DIR = pathlib.Path(f"figma_screens/{RUN_ID}")
OUT_DIR.mkdir(parents=True, exist_ok=True) # Ensure parent directories are created

# ---------- Operational Mode & File Export Config ------------------------- #
OPERATIONAL_MODE = getattr(config, "OPERATIONAL_MODE", "JIRA_EXPORT")
TEXT_EXPORT_PATH = getattr(config, "TEXT_EXPORT_PATH", "create_final_tests/artifacts")
TEXT_EXPORT_FILENAME_TEMPLATE = getattr(config, "TEXT_EXPORT_FILENAME_TEMPLATE", "tests_from_figma_runid_{RUN_ID}.csv")
TEXT_EXPORT_DEFAULT_PRIORITY = getattr(config, "TEXT_EXPORT_DEFAULT_PRIORITY", "Medium")
TEXT_EXPORT_DEFAULT_BOARD = getattr(config, "TEXT_EXPORT_DEFAULT_BOARD", "Default Board")
TEXT_EXPORT_CSV_DELIMITER = getattr(config, "TEXT_EXPORT_CSV_DELIMITER", ";")
TEXT_EXPORT_TESTCASEIDENTIFIER_TEMPLATE = getattr(config, "TEXT_EXPORT_TESTCASEIDENTIFIER_TEMPLATE", "")

# ---------- Figma File Key ------------------------------------------------- #
try:
    FILE_KEY = parse_file_key(FIGMA_FILE_URL)
except ValueError as e:
    logger.critical(f"Critical error: {e}. Exiting.")
    exit(1) # Or raise SystemExit(1)

# --------------------------------------------------------------------------- #
#                      DATA COLLECTION (FRAMES & ELEMENTS)                     #
# --------------------------------------------------------------------------- #
def _collect_top_frames(figma_client: FigmaClient, file_key: str, limit: int) -> list[tuple[str,str,str]]:
    try:
        tree = figma_client.get_file_tree(file_key)
    except requests.exceptions.RequestException:
        logger.error("❌ Failed to get Figma file tree. Aborting frame collection.")
        return []

    dup_cnt = defaultdict(int)
    frames_data  = [] 

    def get_node_area(node_dict) -> float:
        box = node_dict.get("absoluteBoundingBox")
        return float(box["width"] * box["height"]) if box and box.get("width") is not None and box.get("height") is not None else 0.0

    def walk_frames(node_dict):
        if node_dict.get("type") == "FRAME":
            raw_name = node_dict.get("name", "").strip()
            if not raw_name: 
                return

            raw_lower  = raw_name.lower()

            if any(b in raw_lower for b in FRAME_BANNED):
                return
            if FRAME_INCLUDE and not any(raw_lower.startswith(pref) for pref in FRAME_INCLUDE):
                return

            clean_name = sanitize(raw_lower) # sanitize is from figma_client
            dup_cnt[clean_name] += 1
            safe_name = f"{dup_cnt[clean_name]:02d}_{clean_name}" if dup_cnt[clean_name] > 1 else clean_name
            
            node_id = node_dict["id"]
            current_area = get_node_area(node_dict)
            frames_data.append((safe_name, node_id, raw_name, current_area))

        for child_node in node_dict.get("children", []):
            walk_frames(child_node)

    for page in tree.get("document", {}).get("children", []):
        walk_frames(page)

    frames_data.sort(key=lambda t: t[3], reverse=True) 
    return [(f[0], f[1], f[2]) for f in frames_data[:limit]]

def _collect_elements(figma_client: FigmaClient, file_key: str, frame_id: str) -> list[tuple[str,str,str]]:
    try:
        res = figma_client.get_nodes(file_key, ids=frame_id)
    except requests.exceptions.RequestException:
        logger.error(f"❌ Failed to get nodes for frame {frame_id}. Aborting element collection.")
        return []
        
    root_node_data = res.get("nodes", {}).get(frame_id)
    if not root_node_data or "document" not in root_node_data:
        logger.warning(f"⚠️ No document data found for frame_id {frame_id}")
        return []
    
    document_root = root_node_data["document"]

    elements = []
    dup_cnt = defaultdict(int)

    def process_node_recursive(node_dict):
        raw_name = node_dict.get("name", "").strip()

        if raw_name: 
            raw_lower = raw_name.lower()
            is_banned = any(b in raw_lower for b in ELEMENT_BANNED)
            is_not_included = ELEMENT_INCLUDE and not any(inc in raw_lower for inc in ELEMENT_INCLUDE)

            if not is_banned and not is_not_included:
                clean_name = sanitize(raw_lower) # sanitize is from figma_client
                dup_cnt[clean_name] += 1
                safe_name = f"{dup_cnt[clean_name]:02d}_{clean_name}" if dup_cnt[clean_name] > 1 else clean_name
                elements.append((safe_name, node_dict["id"], raw_name))

        for child_node in node_dict.get("children", []):
            process_node_recursive(child_node)
    
    for child_of_document_root in document_root.get("children", []):
        process_node_recursive(child_of_document_root)
        
    return elements

# --------------------------------------------------------------------------- #
#                            PNG RENDERING                                    #
# --------------------------------------------------------------------------- #
def _download_png(figma_client: FigmaClient, file_key: str, node_id: str, name: str, scale: float | int) -> pathlib.Path | None:
    try:
        image_url = figma_client.get_image_url(file_key, node_id, scale)
        if not image_url:
            logger.warning(f"⚠️ No image URL returned for node {node_id} ('{name}')")
            return None

        image_data = figma_client.download_image_data(image_url)
        path = OUT_DIR / f"{name}.png"
        path.write_bytes(image_data)
        logger.info(f"✅ Successfully downloaded PNG for '{name}' to {path}")
        return path
    except requests.exceptions.RequestException as e: # Catch specific Figma client exceptions if defined, or general
        logger.error(f"❌ Failed to download PNG for node {node_id} ('{name}'): {e}")
        return None
    except IOError as e:
        logger.error(f"❌ Failed to write PNG file for '{name}': {e}")
        return None

# --------------------------------------------------------------------------- #
#                               JIRA INTEGRATION                              #
# --------------------------------------------------------------------------- #
def _create_test_issue(jira_client: JiraClient, summary: str, description: str,
                       png_path: pathlib.Path, project_key: str, issue_type_name: str, xray_custom_field: str,
                       labels: list[str],
                       test_repository_path: str | None = None,
                       test_case_type: str | None = None) -> str | None:
    steps = [{
        "fields": {
            "Action": summary, 
            "Data": "", 
            "Expected Result": f"!{png_path.name}|width=600!" 
        }
    }]
    
    logger.info(f"📝 Attempting to create Jira issue with summary '{summary}' and labels: {labels}")
    try:
        created_issue = jira_client.create_issue(
            project_key=project_key,
            summary=summary,
            description=description,
            issue_type=issue_type_name,
            xray_steps_field=xray_custom_field,
            steps_data=steps,
            labels=labels,
            custom_field_test_repository_path_id=CUSTOMFIELD_TEST_REPOSITORY_PATH,
            test_repository_path_value=test_repository_path,
            custom_field_test_case_type_id=CUSTOMFIELD_TEST_CASE_TYPE,
            test_case_type_value=test_case_type
        )
        issue_key = created_issue["key"]
        logger.info(f"✅ Successfully created Jira issue {issue_key}: {summary}")
        
        jira_client.attach_file(issue_key, png_path)
        logger.info(f"📎 Successfully attached {png_path.name} to {issue_key}")
        return issue_key
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to create Jira issue or attach file for summary '{summary}': {e}")
        return None
    except KeyError:
        logger.error(f"❌ Failed to parse Jira response for summary '{summary}' (KeyError, likely 'key' missing from issue creation response)")
        return None

def _create_screen_test_issue(jira_client: JiraClient, screen_raw_name: str, node_id: str,
                              png_path: pathlib.Path) -> str | None:
    summary = f"{screen_raw_name} - компоновка"
    figma_link = f"{FIGMA_FILE_URL}&node-id={node_id}"
    description = f"*Figma:* [{screen_raw_name}|{figma_link}]"
    final_labels = list(JIRA_LABELS) + [f"runid_{RUN_ID}"]
    
    test_repo_path_val = screen_raw_name
    test_case_type_val = "component"
    
    return _create_test_issue(
        jira_client, summary, description, png_path,
        JIRA_PROJECT_KEY, ISSUE_TYPE, XRAY_STEPS_FIELD, final_labels,
        test_repository_path=test_repo_path_val, test_case_type=test_case_type_val
    )

def _create_element_test_issue(jira_client: JiraClient, screen_raw_name: str, elem_raw_name: str,
                               node_id: str, png_path: pathlib.Path) -> str | None:
    summary = f"{screen_raw_name}. {elem_raw_name} - логика работы"
    figma_link = f"{FIGMA_FILE_URL}&node-id={node_id}"
    description = f"*Figma:* [{elem_raw_name}|{figma_link}]"
    final_labels = list(JIRA_LABELS) + [f"runid_{RUN_ID}"]

    test_repo_path_val = f"{screen_raw_name}/{elem_raw_name}"
    test_case_type_val = "component"

    return _create_test_issue(
        jira_client, summary, description, png_path,
        JIRA_PROJECT_KEY, ISSUE_TYPE, XRAY_STEPS_FIELD, final_labels,
        test_repository_path=test_repo_path_val, test_case_type=test_case_type_val
    )

# --------------------------------------------------------------------------- #
#                                   MAIN ORCHESTRATION                        #
# --------------------------------------------------------------------------- #
def main():
    logger.info("🚀 Starting Figma to Jira test case generation process...")
    logger.info(f"📄 runid_{RUN_ID}")
    
    # Initialize API clients
    figma_client = FigmaClient(token=FIGMA_TOKEN)
    jira_client = None
    if OPERATIONAL_MODE == "JIRA_EXPORT":
        logger.info(f"⚙️ Operational mode: JIRA_EXPORT. Connecting to Jira instance: {JIRA_URL}")
        jira_client = JiraClient(base_url=JIRA_URL, username=JIRA_USERNAME, password=JIRA_PASSWORD)
    elif OPERATIONAL_MODE == "FILE_EXPORT":
        logger.info(f"⚙️ Operational mode: FILE_EXPORT. Test cases will be saved to a CSV file.")
    else:
        logger.critical(f"❌ Invalid OPERATIONAL_MODE: '{OPERATIONAL_MODE}'. Must be 'JIRA_EXPORT' or 'FILE_EXPORT'. Exiting.")
        return

    logger.info(f"📄 Processing Figma file: {FIGMA_FILE_URL} (Key: {FILE_KEY})")

    screens = _collect_top_frames(figma_client, FILE_KEY, FRAME_LIMIT)
    logger.info(f"✅ Selected {len(screens)} screens for processing.")

    if not screens:
        logger.info("ℹ️ No screens selected based on current filters and limit. Exiting.")
        return

    created_issues_keys = []
    txt_export_data = []
    txt_export_header = [
        "TestCaseIdentifier", "Summary", "Description", "Priority", "Labels",
        "Action", "Data", "ExpectedResult", "Board",
        "testRepositoryPath", "testCaseType"
    ]

    # Common labels for both modes
    run_specific_label = f"runid_{RUN_ID}"
    common_labels_list = list(JIRA_LABELS) + [run_specific_label]

    for screen_safe_name, screen_id, screen_raw_name in screens:
        logger.info(f"🖥️ Processing screen: «{screen_raw_name}» (ID: {screen_id})")
        
        png_screen_path = _download_png(figma_client, FILE_KEY, screen_id, screen_safe_name, FIGMA_SCALE)
        if not png_screen_path:
            logger.warning(f"⚠️ Skipping screen «{screen_raw_name}» due to PNG download failure.")
            continue

        if OPERATIONAL_MODE == "JIRA_EXPORT":
            if jira_client: # Ensure jira_client is initialized
                key_screen = _create_screen_test_issue(jira_client, screen_raw_name, screen_id, png_screen_path)
                if key_screen:
                    created_issues_keys.append(key_screen)
                else:
                    logger.error(f"❌ Failed to create Jira issue for screen «{screen_raw_name}».")
        elif OPERATIONAL_MODE == "FILE_EXPORT":
            base_test_case_id = f"{screen_safe_name}_layout"
            if TEXT_EXPORT_TESTCASEIDENTIFIER_TEMPLATE:
                test_case_id = f"{TEXT_EXPORT_TESTCASEIDENTIFIER_TEMPLATE}_{base_test_case_id}"
            else:
                test_case_id = base_test_case_id
            summary = f"{screen_raw_name} - компоновка"
            figma_link = f"{FIGMA_FILE_URL}&node-id={screen_id}"
            description = f"*Figma:* [{screen_raw_name}|{figma_link}]"
            priority = TEXT_EXPORT_DEFAULT_PRIORITY
            labels_str = ",".join(common_labels_list)
            action = summary # Per plan, action is same as summary for XRay steps
            data_field = ""
            expected_result = f"!{png_screen_path.name}|width=600!" # PNGs are in OUT_DIR
            board = TEXT_EXPORT_DEFAULT_BOARD
            
            test_repo_path_val_file = screen_raw_name
            test_case_type_val_file = "component"
            
            txt_export_data.append([
                test_case_id, summary, description, priority, labels_str,
                action, data_field, expected_result, board,
                test_repo_path_val_file, test_case_type_val_file
            ])
        
        elements = _collect_elements(figma_client, FILE_KEY, screen_id)
        if not elements:
            logger.info(f"  ℹ️ └─ No elements found for screen «{screen_raw_name}» matching filters.")
            continue
        logger.info(f"  🔍 Found {len(elements)} element(s) for screen «{screen_raw_name}».")

        for elem_safe_name, elem_id, elem_raw_name in elements:
            logger.info(f"  ✨ Processing element: «{elem_raw_name}» (ID: {elem_id}) on screen «{screen_raw_name}»")
            
            # Create a unique name for the element PNG to avoid overwrites if multiple elements have same sanitized name
            element_png_name = f"{screen_safe_name}__{elem_safe_name}"
            png_elem_path = _download_png(
                figma_client, FILE_KEY, elem_id, element_png_name, FIGMA_SCALE
            )
            if not png_elem_path:
                logger.warning(f"    ⚠️ Skipping element «{elem_raw_name}» due to PNG download failure.")
                continue
            
            if OPERATIONAL_MODE == "JIRA_EXPORT":
                if jira_client: # Ensure jira_client is initialized
                    key_elem = _create_element_test_issue(
                        jira_client, screen_raw_name, elem_raw_name, elem_id, png_elem_path
                    )
                    if key_elem:
                        created_issues_keys.append(key_elem)
                    else:
                        logger.error(f"    ❌ Failed to create Jira issue for element «{elem_raw_name}» on screen «{screen_raw_name}».")
            elif OPERATIONAL_MODE == "FILE_EXPORT":
                base_test_case_id = f"{screen_safe_name}__{elem_safe_name}_logic"
                if TEXT_EXPORT_TESTCASEIDENTIFIER_TEMPLATE:
                    test_case_id = f"{TEXT_EXPORT_TESTCASEIDENTIFIER_TEMPLATE}_{base_test_case_id}"
                else:
                    test_case_id = base_test_case_id
                summary = f"{screen_raw_name}. {elem_raw_name} - логика работы"
                figma_link = f"{FIGMA_FILE_URL}&node-id={elem_id}"
                description = f"*Figma:* [{elem_raw_name}|{figma_link}]"
                priority = TEXT_EXPORT_DEFAULT_PRIORITY
                labels_str = ",".join(common_labels_list)
                action = summary # Per plan
                data_field = ""
                expected_result = f"!{png_elem_path.name}|width=600!" # PNGs are in OUT_DIR
                board = TEXT_EXPORT_DEFAULT_BOARD

                test_repo_path_val_file = f"{screen_raw_name}/{elem_raw_name}"
                test_case_type_val_file = "component"

                txt_export_data.append([
                    test_case_id, summary, description, priority, labels_str,
                    action, data_field, expected_result, board,
                    test_repo_path_val_file, test_case_type_val_file
                ])

    # --- Finalizing based on OPERATIONAL_MODE ---
    logger.info("🏁 --- Process Completed ---")
    if OPERATIONAL_MODE == "JIRA_EXPORT":
        if created_issues_keys:
            jql = "issuekey in (" + ", ".join(f'"{key}"' for key in created_issues_keys) + ")"
            encoded_jql = urllib.parse.quote(jql, safe='(),') # Encode JQL
            jira_link = f"{JIRA_URL.rstrip('/')}/issues/?jql={encoded_jql}"
            
            link_file_path = OUT_DIR / f"jira_issues_run_{RUN_ID}.txt"
            try:
                with open(link_file_path, "w", encoding="utf-8") as f:
                    f.write(jira_link)
                logger.info(f"🔗 Jira link saved to: {link_file_path.resolve()}")
            except IOError as e:
                logger.error(f"❌ Failed to write Jira link to file {link_file_path}: {e}")

            logger.info("🔗 Link to created Jira issues:")
            logger.info(jira_link)
        else:
            logger.info("ℹ️ No Jira issues were created in this run.")
    elif OPERATIONAL_MODE == "FILE_EXPORT":
        if txt_export_data:
            filename = TEXT_EXPORT_FILENAME_TEMPLATE.format(RUN_ID=RUN_ID)
            output_dir = pathlib.Path(TEXT_EXPORT_PATH)
            output_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists
            file_path = output_dir / filename
            
            try:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f, delimiter=TEXT_EXPORT_CSV_DELIMITER)
                    writer.writerow(txt_export_header)
                    writer.writerows(txt_export_data)
                logger.success(f"✅ Successfully generated TXT file: {file_path.resolve()}")
                logger.info(f"📄 TXT file contains {len(txt_export_data)} test cases.")
            except IOError as e:
                logger.error(f"❌ Failed to write TXT file to {file_path}: {e}")
        else:
            logger.info("ℹ️ No test data was generated for the TXT file in this run.")

        # --- Added logic to run secondary script and open its output ---
        logger.info(f"⚙️ Proceeding to run secondary script for FILE_EXPORT mode...")
        
        secondary_script_relative_path = "create_final_tests/create_final_promt.py"
        # Assuming send_figma_tests_all_tests.py runs from workspace root
        secondary_script_full_path = pathlib.Path(secondary_script_relative_path)
        secondary_script_dir = secondary_script_full_path.parent

        # Define the expected generated file path using TEXT_EXPORT_PATH
        # TEXT_EXPORT_PATH defaults to "create_final_tests/artifacts"
        generated_file_to_open = pathlib.Path(TEXT_EXPORT_PATH) / "final_promt.txt"

        try:
            if not secondary_script_full_path.is_file():
                logger.error(f"❌ Secondary script {secondary_script_full_path} not found. Skipping execution.")
            else:
                logger.info(f"🐍 Executing Python script: python3 {secondary_script_full_path.name} (from {secondary_script_dir})")
                
                # Prepare environment variables for the secondary script
                script_env = os.environ.copy()
                script_env["FIGMA_RUN_ID"] = RUN_ID
                script_env["FIGMA_TEXT_EXPORT_PATH"] = TEXT_EXPORT_PATH # TEXT_EXPORT_PATH is relative to workspace root

                result = subprocess.run(
                    ["python3", secondary_script_full_path.name], # Run script by name, from its directory
                    capture_output=True, 
                    text=True, 
                    check=False, # Manually check returncode to log details
                    cwd=secondary_script_dir, # Run from the script's own directory
                    env=script_env
                )

                if result.stdout:
                    logger.info(f"Output from {secondary_script_full_path.name}:\n{result.stdout}")
                if result.stderr: # Log stderr as warning as it might contain non-fatal errors or verbose logs
                    logger.warning(f"Stderr from {secondary_script_full_path.name}:\n{result.stderr}")

                if result.returncode == 0:
                    logger.success(f"✅ Successfully executed {secondary_script_full_path.name}.")
                    
                    # Attempt to open the generated file
                    if generated_file_to_open.exists():
                        logger.info(f"📂 Attempting to open generated file: {generated_file_to_open.resolve()}")
                        try:
                            # For macOS (user's OS is darwin), 'open' command.
                            subprocess.run(["open", str(generated_file_to_open.resolve())], check=True)
                            logger.success(f"✅ Successfully requested to open {generated_file_to_open.resolve()}.")
                        except subprocess.CalledProcessError as e_open:
                            logger.error(f"❌ Failed to open {generated_file_to_open.resolve()}: {e_open}")
                        except FileNotFoundError: # If 'open' command itself is not found
                            logger.error(f"❌ 'open' command not found. Cannot open {generated_file_to_open.resolve()}.")
                    else:
                        logger.error(f"❌ Expected generated file {generated_file_to_open.resolve()} not found after running {secondary_script_full_path.name}.")
                else:
                    logger.error(f"❌ Failed to execute {secondary_script_full_path.name}. Return code: {result.returncode}.")

        except FileNotFoundError: # This handles if python3 or the script itself (if full path used in Popen) is not found
            logger.error(f"❌ Script {secondary_script_full_path} or python3 interpreter not found. Please ensure it exists and python3 is in PATH.")
        except Exception as e_script_run_exc: 
            logger.error(f"❌ An unexpected error occurred while trying to run {secondary_script_full_path.name} or open its file: {e_script_run_exc}")
        # --- End of added logic ---

if __name__ == "__main__":
    main()
