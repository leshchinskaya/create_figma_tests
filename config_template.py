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

# Настройки Figma
FIGMA_TOKEN = "YOUR_FIGMA_PERSONAL_ACCESS_TOKEN"
FIGMA_FILE_URL = "YOUR_FIGMA_FILE_URL"  # Пример: "https://www.figma.com/file/your-file-id/file-name"
FIGMA_SCALE = 1  # Отрегулируйте по мере необходимости, обычно 1 или 2 для retina
# Ссылка на swagger файл
SWAGGER_URL = "YOUR_SWAGGER_URL"  # Пример: "https://example.com/swagger.yaml"
# Локальный путь к swagger файлу (можно указывать относительный путь к репозиторию)
SWAGGER_LOCAL_PATH = ""  # Например: "../external_repo/swagger.yaml"

# Фильтры фреймов (для _collect_top_frames)
# Эти настройки помогают фильтровать, какие фреймы из Figma обрабатываются.
# Отрегулируйте их в зависимости от структуры ваших файлов Figma.
FRAME_LIMIT = 10  # Максимальное количество фреймов верхнего уровня для обработки, отрегулируйте по мере необходимости
FRAME_BANNED = ("frame", "form", "icon")  # Имена фреймов, которые нужно пропустить (поиск по подстроке, без учета регистра)
FRAME_INCLUDE = ("screen",)  # Включать только фреймы, имена которых начинаются с этих (поиск по префиксу, без учета регистра)

# Фильтры элементов
# Эти настройки помогают фильтровать, какие элементы внутри фрейма учитываются.
ELEMENT_BANNED  = ("icon", "decoration")  # Имена элементов, которые нужно игнорировать (поиск по подстроке, без учета регистра)
ELEMENT_INCLUDE = ("section",) # Включать только элементы, имена которых содержат эти строки (поиск по подстроке, без учета регистра)

# Режим работы
OPERATIONAL_MODE = "FILE_EXPORT"  # "JIRA_EXPORT" или "FILE_EXPORT"

# --- Настройки для режима FILE_EXPORT ---
# Путь, по которому будет сохранен файл тест-кейса в формате TXT.
TEXT_EXPORT_PATH = "create_final_tests/artifacts"
# Шаблон имени файла для экспортируемого TXT-файла. {RUN_ID} будет заменен.
TEXT_EXPORT_FILENAME_TEMPLATE = "tests_from_figma.txt"
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
