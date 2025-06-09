# Порядок работы

1. В `task_list_configuration.md` задайте `SCAN_BASE_DIR` и перечислите нужные папки. Склонируйте репозиторий с требованиями на один уровень выше данного проекта. Затем выполните `update_file_structure.py` и скопируйте содержимое `file_structure.md` в `req_showcase.md`.
2. В `config.py` укажите `FRAME_INCLUDE` и оставьте `OPERATIONAL_MODE = "FILE_EXPORT"`. Настройте ссылку на Figma и токен. Запустите `send_figma_tests_all_tests.py`. После выполнения сохраните `tests_from_figma_runid_{RUN_ID}.csv` как `tests_from_figma.csv`.
3. Обновите `swagger.yaml`, скопировав свежий файл из репозитория со swagger схемой.
4. В начале `prompt.md` пропишите желаемые функции и запустите `create_final_prompt.py`.
5. Содержимое `final_prompt.txt` передайте в LLM с CoT.
6. Получив ответ, попросите модель сверить его с исходным запросом и указать возможные ошибки. Проверьте результат вручную.
7. Попросите модель внести правки и вернуть JSON. Поместите его в `final_tests.json`.
8. В `config.py` установите `JIRA_PROJECT_KEY` и `JIRA_LABELS`, затем выполните `send_final_tests.py`. Ссылка на созданные задачи появится в выводе. Проверьте их вручную.

*`update_file_structure.py` пропускает файлы `.DS_Store`.*
