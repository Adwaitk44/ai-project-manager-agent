
import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

auth = HTTPBasicAuth(EMAIL, API_TOKEN)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

payload = {
    "fields": {
        "project": {
            "key": PROJECT_KEY
        },
        "summary": "Test task created by AI Project Manager Agent",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "This is a test issue created "
                                "through the Jira REST API."
                            )
                        }
                    ]
                }
            ]
        },
        "issuetype": {
            "name": "Task"
        },
        "labels": [
            "ai-project-manager"
        ]
    }
}

try:
    response = requests.post(
        f"{BASE_URL}/rest/api/3/issue",
        json=payload,
        headers=headers,
        auth=auth,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    issue_key = result["key"]
    issue_url = f"{BASE_URL}/browse/{issue_key}"

    print("SUCCESS: Jira issue created!")
    print("Issue Key:", issue_key)
    print("Issue URL:", issue_url)

except requests.HTTPError as error:
    print("Jira creation failed:", error.response.status_code)
    print(error.response.text[:2000])

except requests.RequestException as error:
    print("Connection error:", error)
