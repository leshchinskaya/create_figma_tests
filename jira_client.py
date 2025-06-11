import requests
import base64

import config
from logger_setup import setup_logger # Import the setup function
import pathlib

logger = setup_logger(__name__) # Use the setup function

class JiraClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        auth_token = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.session.headers.update({"Authorization": f"Basic {auth_token}"})

    def _request(self, method: str, endpoint: str, json_data: dict | None = None, files: dict | None = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        headers = {} # Per-request headers
        if json_data:
            headers["Content-Type"] = "application/json"
        if files:
            headers["X-Atlassian-Token"] = "no-check"
        
        final_headers = self.session.headers.copy()
        final_headers.update(headers)

        try:
            response = self.session.request(method, url, json=json_data, files=files, headers=final_headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Jira API request {method} {url} failed: {e}")
            if e.response is not None:
                logger.error(f"Jira response: {e.response.status_code} - {e.response.text}")
            raise

    def create_issue(self, project_key: str, summary: str, description: str, 
                     issue_type: str, xray_steps_field: str, steps_data: list, labels: list[str],
                     custom_field_test_repository_path_id: str | None = None, 
                     test_repository_path_value: str | None = None,
                     custom_field_test_case_type_id: str | None = None, 
                     test_case_type_value: str | None = None) -> dict:
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
            "labels": labels,
            "assignee": {"name": None},
            xray_steps_field: {"steps": steps_data}
        }

        if custom_field_test_repository_path_id and test_repository_path_value is not None:
            fields[custom_field_test_repository_path_id] = test_repository_path_value
        
        if custom_field_test_case_type_id and test_case_type_value is not None:
            fields[custom_field_test_case_type_id] = {"value": test_case_type_value}

        if (board_field_id := getattr(config, "CUSTOMFIELD_TEST_BOARD", None)) is not None:
            fields[board_field_id] = {"value": "QA"}
            
        response = self._request("POST", "/rest/api/2/issue", json_data={"fields": fields})
        return response.json()

    def attach_file(self, issue_key: str, file_path: pathlib.Path) -> None:
        with file_path.open("rb") as fh:
            files_data = {"file": (file_path.name, fh, "image/png")}
            self._request("POST", f"/rest/api/2/issue/{issue_key}/attachments", files=files_data) 