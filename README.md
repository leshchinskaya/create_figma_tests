# Project Automation Scripts

This project provides a suite of Python scripts designed to automate various tasks, primarily focusing on interactions with Figma and Jira.

## Initial Setup (Required for most scripts)

1.  **Create Configuration File**:
    Copy the template to create your local configuration:
    ```bash
    cp config_template.py config.py
    ```
    Then, edit `config.py` and fill in all required values (API keys, Jira URL, project keys, etc.). Refer to `config_template.py` for details on the variables needed for each script.

2.  **Install Dependencies and Set Permissions**:
    Run the setup script. This will install necessary Python packages (like `requests`, `urllib3`) and make the main Python scripts executable.
    ```bash
    ./setup.sh
    ```

## Available Scripts and Workflows

### 1. Figma Designs to Jira Test Cases (`send_figma_tests_all_tests.py`)

This script processes a Figma file, extracts information about screens and elements, and automatically creates corresponding Test issues in Jira.

**Key Configuration (in `config.py`):**
*   `FIGMA_FILE_URL`: The URL of your Figma file.
*   `FIGMA_TOKEN`: Your Figma personal access token.
*   `JIRA_URL`, `JIRA_PROJECT_KEY`, `JIRA_USERNAME`, `JIRA_PASSWORD`: Your Jira instance details.
*   `ISSUE_TYPE`: The Jira issue type for the tests (e.g., "Test").
*   `XRAY_STEPS_FIELD`: Custom field ID for Xray test steps if you use Xray.
*   `OPERATIONAL_MODE`: Determines the script's output.
    *   `"JIRA_EXPORT"` (Default): Creates issues directly in Jira and attaches images.
    *   `"FILE_EXPORT"`: Does not create Jira issues. Instead, it generates a semicolon-delimited text file with test case data (summary, description, steps, etc.). Images are still downloaded.
        *   `TEXT_EXPORT_PATH`: Directory where the text file will be saved (default: `create_final_tests/artifacts`).
        *   `TEXT_EXPORT_FILENAME_TEMPLATE`: Filename pattern for the exported text file (default: `tests_from_figma_runid_{RUN_ID}.txt`).
*   `JIRA_LABELS`: Optional list of global labels to add to Jira issues.
*   Filtering options like `FRAME_LIMIT`, `ELEMENT_BANNED`, `FRAME_BANNED`, etc., to control which Figma items are processed.

**How to Run:**
After completing the initial setup and configuring `config.py` with your Figma token and Jira details:
```bash
./send_figma_tests_all_tests.py
```
or
```bash
python3 send_figma_tests_all_tests.py
```

**Outputs:**
*   **If `OPERATIONAL_MODE` is `"JIRA_EXPORT"`:**
    *   Test issues created in your Jira project.
    *   A text file (`figma_screens/<RUN_ID>/jira_issues_run_<RUN_ID>.txt`) containing direct links to the created Jira issues.
*   **If `OPERATIONAL_MODE` is `"FILE_EXPORT"`:**
    *   A semicolon-delimited text file containing test case data, saved to the path defined by `TEXT_EXPORT_PATH` and `TEXT_EXPORT_FILENAME_TEMPLATE`.
*   **Common to both modes:**
    *   Images of Figma screens/elements saved in the `figma_screens/<RUN_ID>/` directory.
    *   Execution logs are written to `figma_to_jira.log` and also printed to the console.

### 2. Prompt Generation from Artifacts (`create_final_tests/create_final_promt.py`)

This utility script generates a text file (e.g., a detailed prompt for an LLM or a complex configuration) by populating a template file with content from various specified artifact files.

**Configuration (`config_artifacts.json`):**
This script requires a separate JSON configuration file, typically named `config_artifacts.json`, placed in the project's root directory. This file defines:
    *   `prompt_template_path`: Path to the template file.
    *   `output_prompt_path`: Path where the generated file will be saved.
    *   `artifacts`: A dictionary mapping keys to paths of content files (artifacts).
    *   `placeholders`: A dictionary mapping the same keys (from `artifacts`) to placeholder strings within the template file that will be replaced by the content of the corresponding artifact.

    *Example `config_artifacts.json` structure:*
    ```json
    {
        "prompt_template_path": "create_final_tests/templates/my_template.txt",
        "output_prompt_path": "create_final_tests/generated_output/final_document.txt",
        "artifacts": {
            "section_one_content": "create_final_tests/source_material/section1_data.txt",
            "section_two_content": "create_final_tests/source_material/section2_data.md"
        },
        "placeholders": {
            "section_one_content": "{{SECTION_ONE_PLACEHOLDER}}",
            "section_two_content": "{{SECTION_TWO_PLACEHOLDER}}"
        }
    }
    ```
    *(Ensure the paths and placeholder names match your actual files and template.)*

**How to Run:**
1.  Create and configure your `config_artifacts.json`.
2.  Ensure your template file and all artifact files exist at the specified paths.
3.  Execute the script:
    ```bash
    python3 create_final_tests/create_final_promt.py
    ```

**Outputs:**
*   The generated text file at the path specified by `output_prompt_path` in `config_artifacts.json`.
*   Informative messages (success or error) printed to the console.

### 3. Sending Test Cases to Jira from File (`send_final_tests.py`)

This script reads test cases from a structured text file (CSV-like, using semicolons as delimiters) and creates corresponding issues in Jira. It is designed to integrate with Xray Test Management by populating test steps if the relevant Xray custom field is configured in `config.py`.

**Configuration (in `config.py`):**
Ensure the following are correctly set in your `config.py` for this script:
*   `JIRA_URL`
*   `JIRA_PROJECT_KEY`
*   `JIRA_USERNAME`
*   `JIRA_PASSWORD`
*   `ISSUE_TYPE` (e.g., "Test", or your Xray Test issue type)
*   `XRAY_STEPS_FIELD` (The custom field ID for Xray test steps, e.g., `customfield_10001`. This is crucial for Xray integration.)
*   Optionally, `JIRA_LABELS`: A list of default labels to be added to every created issue (e.g., `["q3-release", "smoke-test"]`).

**Input File Format (`create_final_tests/artifacts/final_tests.txt`):**
The script expects a text file at `create_final_tests/artifacts/final_tests.txt`. This file should:
*   Be semicolon-delimited (`;`).
*   Include a header row as the first line.
*   Contain the following columns (column names are case-sensitive as used in the script):
    *   `TestCaseIdentifier`: A unique identifier for the test case (e.g., "TC-001").
    *   `Summary`: The title of the Jira issue (Mandatory for each test case).
    *   `Description`: Detailed description for the Jira issue.
    *   `Priority`: Test priority (e.g., "High", "Medium"). This will be converted into a label (e.g., `Priority_High`).
    *   `Labels`: Comma-separated list of additional custom labels.
    *   `Action`: The "Action" or "Step" description for an Xray test step.
    *   `Data`: The "Data" for an Xray test step.
    *   `ExpectedResult`: The "Expected Result" for an Xray test step.
    *   `Board`: A value that will be used as an additional label (e.g., a sprint or team board name).

**How to Run:**
After completing the initial setup and configuring `config.py` appropriately:
```bash
./send_final_tests.py
```
or
```bash
python3 send_final_tests.py
```
*(Ensure `send_final_tests.py` is executable if using the `./` method; `setup.sh` should handle this.)*

**Outputs:**
*   Jira issues created in the project specified in `config.py`.
*   A JQL query link to all successfully created issues is logged to the console and also written to `send_final_tests.log`. This allows for easy viewing of the created issues in Jira.
*   Detailed execution logs are written to `send_final_tests.log` and also printed to the console.

## Frameworks and Libraries Used
* Python 3.9+
* requests 2.31+
* urllib3 1.26.17+
