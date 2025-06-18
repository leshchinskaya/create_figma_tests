# Инструкция по Генерации Тестов

Этот документ описывает два основных рабочих процесса: создание компонентных тестов и создание сценарных тестов.

---

## Workflow 1: Генерация Компонентных Тестов

**Цель:** Создать детальные компонентные тесты на основе дизайна в Figma, требований и Swagger. Результат этого
воркфлоу (`component_tests.csv`) является входными данными для генерации сценарных тестов.

**Шаг 1: Сбор требований **

Соберите PDF файлы для фичи. Их не должно быть больше 9 штук. Если нужно больше - воспользуйтесь конвертацией в MD и
сложите их в одну папку, потом воспользуйтесь 
```bash
  python3 create_final_tests/folder_structure/gui_update_file_structure.py
  ```
который создаст `create_final_tests/artifacts/req.md` и его можно будет взять для LLM.

**Шаг 2: Генерация промпта для AI**

* Запустите скрипт, который соберет все артефакты в один промпт.
  ```bash
  ./generate_component_prompt.sh
  ```
* **Результат:** Будет создан файл `create_final_tests/artifacts/final_prompt_component.txt`.
* Если в `config.py` установлено `AUTOLAUNCH_FILES = True`, файл промпта и `component_tests.json` откроются
  автоматически.

**Шаг 3: Работа с AI и получение JSON**

1. Скопируйте всё содержимое файла `final_prompt_component.txt` и передайте его AI.
2. Полученный от AI ответ в формате JSON сохраните в файл: `create_final_tests/artifacts/component_tests.json`.

**Шаг 4: Отправка в Jira и/или конвертация в CSV**

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

**Шаг 2: Работа с AI и получение JSON**

1. Скопируйте всё содержимое файла `final_prompt_scenario.txt` и передайте его AI.
2. Полученный от AI ответ в формате JSON сохраните в файл: `create_final_tests/artifacts/scenario_tests.json`.

**Шаг 3: Отправка сценарных тестов в Jira**

* Запустите скрипт для отправки тестов.
  ```bash
  python3 send_final_tests.py
  ```
* **Результат:** Сценарные тесты будут созданы в Jira. Ссылка на созданные задачи появится в консоли.
