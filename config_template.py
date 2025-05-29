# Jira settings
JIRA_URL = "YOUR_JIRA_URL"  # Example: "https://your-jira-instance.com"
JIRA_PROJECT_KEY = "YOUR_PROJECT_KEY"  # Example: "PROJ"
JIRA_USERNAME = "YOUR_JIRA_USERNAME"
JIRA_PASSWORD = "YOUR_JIRA_PASSWORD_OR_API_TOKEN"
JIRA_LABELS = []  # User-defined labels for Jira issues, e.g., ["frontend", "release-feature"]
ISSUE_TYPE = "Test"
XRAY_STEPS_FIELD = "customfield_10204"

# Figma settings
FIGMA_TOKEN = "YOUR_FIGMA_PERSONAL_ACCESS_TOKEN"
FIGMA_FILE_URL = "YOUR_FIGMA_FILE_URL"  # Example: "https://www.figma.com/file/your-file-id/file-name"
FIGMA_SCALE = 1  # Adjust as needed, usually 1 or 2 for retina

# Frame filters (for _collect_top_frames)
# These settings help filter which frames are processed from Figma.
# Adjust these based on how your Figma files are structured.
FRAME_LIMIT = 10  # Max number of top-level frames to process, adjust as needed
FRAME_BANNED = ("frame", "form", "icon")  # Names of frames to skip (substring match, case-insensitive)
FRAME_INCLUDE = ("screen",)  # Only include frames whose names start with these (prefix match, case-insensitive)

# Element filters
# These settings help filter which elements within a frame are considered.
ELEMENT_BANNED  = ("icon", "decoration")  # Names of elements to ignore (substring match, case-insensitive)
ELEMENT_INCLUDE = ("section",) # Only include elements whose names contain these strings (substring match, case-insensitive)

# Operational Mode
OPERATIONAL_MODE = "FILE_EXPORT"  # "JIRA_EXPORT" or "FILE_EXPORT"
# --- Settings for FILE_EXPORT mode ---
# Path where the TXT test case file will be saved.
TEXT_EXPORT_PATH = "create_final_tests/artifacts"
# Filename template for the exported TXT file. {RUN_ID} will be replaced.
TEXT_EXPORT_FILENAME_TEMPLATE = "tests_from_figma_runid_{RUN_ID}.txt"
# Template/prefix for TestCaseIdentifier in FILE_EXPORT mode.
# If you set this to "Test-01", identifiers will look like "Test-01_screenname_layout".
# Set to "" (empty string) if no prefix is desired (this is the default).
TEXT_EXPORT_TESTCASEIDENTIFIER_TEMPLATE = "Test"
# Default priority for test cases in the TXT file.
TEXT_EXPORT_DEFAULT_PRIORITY = "Normal"
# Default board/category for test cases in the TXT file.
TEXT_EXPORT_DEFAULT_BOARD = "QA"
# Delimiter for the TXT/CSV file.
TEXT_EXPORT_CSV_DELIMITER = ";"