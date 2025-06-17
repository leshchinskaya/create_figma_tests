import urllib.parse

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
                     priority: str = "Normal",
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
            "priority": {"name": priority},
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

    def download_issues_csv(self, jql: str, output_path: pathlib.Path) -> None:
        """
        Downloads issues from Jira as a CSV file based on a JQL query.

        Args:
            jql: The JQL query string for the issues to export.
            output_path: The local path (including filename) to save the CSV.
        """
        logger.info(f"Attempting to download issues as CSV for JQL: '{jql}'")

        try:
            # This is the specific, non-standard API endpoint for CSV export in Jira
            csv_export_path = "/sr/jira.issueviews:searchrequest-csv-current-fields/temp/SearchRequest.csv"

            encoded_jql = urllib.parse.quote(jql)

            # Construct the full download URL with a semicolon delimiter
            download_url = f"{self.base_url}{csv_export_path}?jqlQuery={encoded_jql}&delimiter=;"

            logger.info(f"Requesting CSV from URL: {download_url}")

            # Make the GET request using the authenticated session
            # No need to call _request as this is a simple GET with no special headers
            response = self.session.get(download_url, timeout=30)

            response.raise_for_status()

            # Ensure the parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the content to the file in binary mode
            with output_path.open("wb") as f:
                f.write(response.content)

            logger.success(f"✅ Successfully downloaded and saved issues to: {output_path}")

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP Error downloading CSV: {e.response.status_code} {e.response.reason}")
            logger.error(f"Response Body: {e.response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to download CSV from Jira. A network error occurred: {e}")
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during CSV download: {e}")