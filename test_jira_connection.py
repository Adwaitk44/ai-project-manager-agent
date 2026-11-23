
import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

if not all([BASE_URL, EMAIL, API_TOKEN, PROJECT_KEY]):
    raise ValueError(
        "Missing Jira configuration. Check your .env file."
    )

auth = HTTPBasicAuth(EMAIL, API_TOKEN)

headers = {
    "Accept": "application/json"
}

try:
    # Test account authentication
    user_response = requests.get(
        f"{BASE_URL}/rest/api/3/myself",
        headers=headers,
        auth=auth,
        timeout=30
    )

    user_response.raise_for_status()
    user = user_response.json()

    print("SUCCESS: Jira authentication working")
    print("Connected account:", user.get("displayName"))

    # Test project access
    project_response = requests.get(
        f"{BASE_URL}/rest/api/3/project/{PROJECT_KEY}",
        headers=headers,
        auth=auth,
        timeout=30
    )

    project_response.raise_for_status()
    project = project_response.json()

    print("\nSUCCESS: Jira project access working")
    print("Project name:", project.get("name"))
    print("Project key:", project.get("key"))

except requests.HTTPError as error:
    print("Jira HTTP error:", error.response.status_code)
    print(error.response.text[:1000])

except requests.RequestException as error:
    print("Connection error:", error)
