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
FRAME_BANNED = ("frame", "form", "icon")  # Names of frames to skip
FRAME_INCLUDE = ("screen",)  # Only include frames whose names start with these

# Element filters
# These settings help filter which elements within a frame are considered.
ELEMENT_BANNED  = ("icon", "decoration")  # Names of elements to ignore
ELEMENT_INCLUDE = ("section",) # Only include elements whose names contain these strings 