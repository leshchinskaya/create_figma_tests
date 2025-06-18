# Инструкция по Генерации Тестов

Этот документ описывает два основных рабочих процесса: создание компонентных тестов и создание сценарных тестов.

---

## Workflow 1: Генерация Компонентных Тестов

**Цель:** Создать детальные компонентные тесты на основе дизайна в Figma, требований и Swagger. Результат этого
воркфлоу (`component_tests.csv`) является входными данными для генерации сценарных тестов.

**Шаг 1: Получение тестов из Figma (если требуется обновление)**

* Убедитесь, что в `config.py` установлен `OPERATIONAL_MODE = "FILE_EXPORT"`.
* Запустите скрипт для анализа Figma:
  ```bash
  python3 send_figma_tests_all_tests.py
  ```
* **Результат:** В папке `create_final_tests/artifacts/` будет создан или обновлен файл `tests_from_figma.csv`.

**Шаг 2: Сбор требований через GUI (или подготовка из PDF/Confluence)**

*   **Основной метод (через GUI для `req.md`):**
    Запустите графический интерфейс, чтобы выбрать нужные разделы ТЗ из структурированных текстовых файлов и обновить единый файл `req.md`:
    ```bash
    python3 create_final_tests/folder_structure/gui_update_file_structure.py
    ```
    *   **Результат:** Файл `create_final_tests/artifacts/req.md` будет создан или обновлён. Этот файл используется на последующих шагах.

*   **Альтернативный метод (подготовка из PDF/Confluence):**
    Если ваши требования находятся в PDF-документах или на страницах Confluence, вы можете использовать скрипт `convert_pdf_to_req.py` для их извлечения в локальную структуру папок с Markdown файлами и вложениями.
    ```bash
    # Пример для Confluence (скачает страницу, дочерние страницы и вложения):
    python3 convert_pdf_to_req.py "https://wiki.example.com/pages/viewpage.action?pageId=12345"
    # Пример для локального PDF:
    python3 convert_pdf_to_req.py /путь/к/вашему/файлу.pdf
    ```
    *   **Результат:** Будет создана структура папок в `create_final_tests/folder_structure/имя_документа/` с файлами `content.md` (и `attachments/` для Confluence).
    *   **Важно:** Этот скрипт *не создает* напрямую файл `req.md`. Полученные Markdown файлы из этой структуры необходимо будет **вручную проанализировать и консолидировать** в основной файл `req.md` (или использовать для обновления `task_list_configuration.md` и последующего запуска `gui_update_file_structure.py`, если это применимо к вашему процессу).
    *   Для деталей по `convert_pdf_to_req.py` (настройка Confluence, все возможности) см. `README.md` или `USAGE.md`.

**Шаг 3: Генерация промпта для AI**

* Запустите скрипт, который соберет все артефакты (требования, swagger, тесты из Figma) в один промпт.
  ```bash
  ./generate_component_prompt.sh
  ```
* **Результат:** Будет создан файл `create_final_tests/artifacts/final_prompt_component.txt`.
* Если в `config.py` установлено `AUTOLAUNCH_FILES = True`, файл промпта и `component_tests.json` откроются
  автоматически.

**Шаг 4: Работа с AI и получение JSON**

1. Скопируйте всё содержимое файла `final_prompt_component.txt` и передайте его AI.
2. Полученный от AI ответ в формате JSON сохраните в файл: `create_final_tests/artifacts/component_tests.json`.

**Шаг 5: Отправка в Jira и/или конвертация в CSV**

* Запустите скрипт, чтобы отправить созданные компонентные тесты в Jira и сохранить CSV с созданными задачами.
  ```bash
  python3 -m create_final_tests.jira_sender --input create_final_tests/artifacts/component_tests.json --download-csv
  ```
* **Результат:** В каталоге `create_final_tests/artifacts/` появится файл `component_tests.csv`.

---

## Workflow 2: Генерация Сценарных Тестов

**Цель:** Создать высокоуровневые end-to-end сценарии на основе уже готовых компонентных тестов, требований и Swagger.

**Обязательное условие:** У вас должен быть актуальный файл `create_final_tests/artifacts/component_tests.csv`. Он
создается на предыдущем этапе.

**Шаг 1: Генерация промпта для AI**

* Запустите скрипт, который соберет все необходимые артефакты.
  ```bash
  ./generate_scenario_prompt.sh
  ```
* **Результат:** Будет создан файл `create_final_tests/artifacts/final_prompt_scenario.txt`.
* Если в `config.py` установлено `AUTOLAUNCH_FILES = True`, файл промпта и `scenario_tests.json` откроются
  автоматически.

**Шаг 2 (опционально): Сбор требований через GUI**

* Если требуется уточнить требования отдельно от компонентных тестов,
  запустите графический интерфейс:
  ```bash
  python3 create_final_tests/folder_structure/gui_update_file_structure.py
  ```
* Используйте его для выбора разделов ТЗ, которые следует включить в сценарные тесты.
  Если требования такие же, как в компонентных тестах, этот шаг можно пропустить.

**Шаг 3: Работа с AI и получение JSON**

1. Скопируйте всё содержимое файла `final_prompt_scenario.txt` и передайте его AI.
2. Полученный от AI ответ в формате JSON сохраните в файл: `create_final_tests/artifacts/scenario_tests.json`.

**Шаг 4: Отправка сценарных тестов в Jira**

* Запустите скрипт для отправки тестов.
  ```bash
  python3 send_final_tests.py
  ```
* **Результат:** Сценарные тесты будут созданы в Jira. Ссылка на созданные задачи появится в консоли.
