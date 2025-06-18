# Настройки Jira
JIRA_URL = "YOUR_JIRA_URL"  # Пример: "https://your-jira-instance.com"
JIRA_PROJECT_KEY = "YOUR_PROJECT_KEY"  # Пример: "PROJ"
JIRA_USERNAME = "YOUR_JIRA_USERNAME"
JIRA_PASSWORD = "YOUR_JIRA_PASSWORD_OR_API_TOKEN"
JIRA_LABELS = []  # Пользовательские метки для задач Jira, например, ["frontend", "release-feature"]
ISSUE_TYPE = "Test"
XRAY_STEPS_FIELD = "customfield_10204"
CUSTOMFIELD_TEST_REPOSITORY_PATH = "customfield_10211"
CUSTOMFIELD_TEST_CASE_TYPE = "customfield_12501"
CUSTOMFIELD_TEST_BOARD = "customfield_10703"

# --- Настройки для режима FILE_EXPORT ---
# Путь, по которому будет сохранен файл тест-кейса в формате TXT.
TEXT_EXPORT_PATH = "create_final_tests/artifacts"
# Шаблон/префикс для TestCaseIdentifier в режиме FILE_EXPORT.
# Если вы установите это значение "Test-01", идентификаторы будут выглядеть как "Test-01_screenname_layout".
# Установите "" (пустая строка), если префикс не нужен (это значение по умолчанию).
TEXT_EXPORT_TESTCASEIDENTIFIER_TEMPLATE = ""
# Приоритет по умолчанию для тест-кейсов в TXT-файле.
TEXT_EXPORT_DEFAULT_PRIORITY = "Normal"
# Доска/категория по умолчанию для тест-кейсов в TXT-файле.
TEXT_EXPORT_DEFAULT_BOARD = "QA"
# Разделитель для TXT/CSV-файла.
TEXT_EXPORT_CSV_DELIMITER = ";"

# Автоматически открывать созданные файлы промптов и JSON при генерации
AUTOLAUNCH_FILES = False
