#!/usr/bin/env python3
from create_final_tests.jira_sender import send_tests_from_json
from pathlib import Path

FINAL_TESTS_FILE_PATH = Path("create_final_tests/artifacts/scenario_tests.json")

if __name__ == "__main__":
    send_tests_from_json(str(FINAL_TESTS_FILE_PATH))
