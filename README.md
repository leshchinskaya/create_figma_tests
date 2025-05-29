## Using
1. Create a config.py file based on config_template.py
2. Fill in the values for the variables in config.py
3. Run the setup script to install dependencies: `./setup.sh`. This will also make the main script executable.
4. Run the script: `./send_figma_tests_all_tests.py` or `python3 send_figma_tests_all_tests.py`
5. The script will create Test-issues in Jira for all screens and elements in the Figma file
6. The script will also create a link to the created issues in Jira, you can find it there: `figma_screens/jira_issues_run_<RUN_ID>.txt`
7. Created images will be at `figma_screens` folder.
8. Logs will be written to `figma_to_jira.log` and also printed to the console.

## Run script
Then, run the main script:
```bash
./send_figma_tests_all_tests.py
```
Alternatively, you can use:
```bash
python3 send_figma_tests_all_tests.py
```

## Frameworks
* Python 3.9+
* requests 2.31+
* urllib3 1.26.17+
