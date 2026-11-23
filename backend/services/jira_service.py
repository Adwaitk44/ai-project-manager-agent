
import os
import re
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

from backend.database import SessionLocal
from backend.models.db_models import Draft

load_dotenv()


def create_jira_issue_for_draft(draft_id):

    db = SessionLocal()

    try:
        draft = db.query(Draft).filter(
            Draft.id == draft_id
        ).first()

        if not draft:
            return {
                "status": "error",
                "message": "Draft not found"
            }

        if draft.status != "approved":
            return {
                "status": "error",
                "message": "Only approved drafts can create Jira issues"
            }

        if draft.draft_type != "action_item":
            return {
                "status": "skipped",
                "message": "Only action items are sent to Jira"
            }

        # Prevent duplicate issue creation.
        if draft.jira_issue_key:
            return {
                "status": "already_created",
                "issue_key": draft.jira_issue_key,
                "issue_url": draft.jira_issue_url
            }

        if draft.jira_creation_status == "creating":
            return {
                "status": "in_progress",
                "message": "Jira issue creation is already in progress"
            }

        # Claim this draft before making the external API request.
        draft.jira_creation_status = "creating"
        draft.jira_error = None
        db.commit()

        base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
        email = os.getenv("JIRA_EMAIL")
        api_token = os.getenv("JIRA_API_TOKEN")
        project_key = os.getenv("JIRA_PROJECT_KEY")

        if not all([base_url, email, api_token, project_key]):
            raise ValueError(
                "Missing Jira configuration in .env"
            )

        # Unique label helps identify the originating draft.
        unique_label = f"ai-pm-draft-{draft.id}"

        description_parts = [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"Action item: {draft.description}"
                    }
                ]
            }
        ]

        if draft.owner:
            description_parts.append({
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": f"Owner: {draft.owner}"
                }]
            })

        if draft.due_date:
            description_parts.append({
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": f"Due date: {draft.due_date}"
                }]
            })

        if draft.evidence:
            description_parts.append({
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": f"Meeting evidence: {draft.evidence}"
                }]
            })

        description_parts.append({
            "type": "paragraph",
            "content": [{
                "type": "text",
                "text": f"Source meeting ID: {draft.meeting_id}; Draft ID: {draft.id}"
            }]
        })

        fields = {
            "project": {
                "key": project_key
            },
            "summary": draft.description[:255],
            "description": {
                "type": "doc",
                "version": 1,
                "content": description_parts
            },
            "issuetype": {
                "name": "Task"
            },
            "labels": [
                "ai-project-manager",
                unique_label
            ]
        }

        # Jira expects YYYY-MM-DD for the due date.
        if draft.due_date:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", draft.due_date):
                fields["duedate"] = draft.due_date

        response = requests.post(
            f"{base_url}/rest/api/3/issue",
            json={"fields": fields},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            auth=HTTPBasicAuth(email, api_token),
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        issue_key = result["key"]
        issue_url = f"{base_url}/browse/{issue_key}"

        # Persist the Jira issue details.
        draft.jira_issue_key = issue_key
        draft.jira_issue_url = issue_url
        draft.jira_created_at = datetime.utcnow()
        draft.jira_creation_status = "created"
        draft.jira_error = None

        db.commit()

        return {
            "status": "created",
            "issue_key": issue_key,
            "issue_url": issue_url
        }

    except Exception as error:

        db.rollback()

        # Record failure so a PM can retry later.
        draft = db.query(Draft).filter(
            Draft.id == draft_id
        ).first()

        if draft and not draft.jira_issue_key:
            draft.jira_creation_status = "failed"
            draft.jira_error = str(error)[:2000]
            db.commit()

        return {
            "status": "failed",
            "message": str(error)
        }

    finally:
        db.close()
