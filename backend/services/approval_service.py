from backend.database import SessionLocal
from backend.models.db_models import Draft, ApprovalHistory


def get_pending_drafts():
    db = SessionLocal()
    try:
        drafts = (
            db.query(Draft)
            .filter(Draft.status.in_(["pending", "edited"]))
            .order_by(Draft.id.desc())
            .all()
        )

        return [
            {
                "id": d.id,
                "meeting_id": d.meeting_id,
                "draft_type": d.draft_type,
                "description": d.description,
                "owner": d.owner,
                "due_date": d.due_date,
                "evidence": d.evidence,
                "source_line_number": d.source_line_number,
                "evidence_verified": d.evidence_verified,
                "status": d.status,
                "jira_issue_key": d.jira_issue_key,
                "jira_issue_url": d.jira_issue_url,
                "jira_creation_status": d.jira_creation_status,
                "jira_error": d.jira_error
            }
            for d in drafts
        ]
    finally:
        db.close()


def get_jira_created_drafts():
    db = SessionLocal()
    try:
        drafts = (
            db.query(Draft)
            .filter(Draft.jira_issue_key.isnot(None))
            .order_by(Draft.id.desc())
            .all()
        )

        return [
            {
                "id": d.id,
                "meeting_id": d.meeting_id,
                "description": d.description,
                "owner": d.owner,
                "due_date": d.due_date,
                "status": d.status,
                "jira_issue_key": d.jira_issue_key,
                "jira_issue_url": d.jira_issue_url,
                "jira_created_at": (
                    d.jira_created_at.isoformat()
                    if d.jira_created_at else None
                )
            }
            for d in drafts
        ]
    finally:
        db.close()


def edit_draft(draft_id, data):
    db = SessionLocal()
    try:
        draft = db.query(Draft).filter(
            Draft.id == draft_id
        ).first()

        if not draft:
            return None

        if draft.status not in ["pending", "edited"]:
            raise ValueError("Draft cannot be edited")

        old_status = draft.status

        draft.description = data.description
        draft.owner = data.owner
        draft.due_date = data.due_date
        draft.status = "edited"

        db.add(
            ApprovalHistory(
                draft_id=draft.id,
                action="edited",
                previous_status=old_status,
                new_status="edited"
            )
        )

        db.commit()

        return {
            "id": draft.id,
            "description": draft.description,
            "owner": draft.owner,
            "due_date": draft.due_date,
            "status": draft.status
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def decide_draft(draft_id, decision, comments=None):
    db = SessionLocal()
    try:
        draft = db.query(Draft).filter(
            Draft.id == draft_id
        ).first()

        if not draft:
            return None

        if draft.status not in ["pending", "edited"]:
            raise ValueError("Draft already processed")

        if decision not in ["approved", "rejected"]:
            raise ValueError("Invalid draft decision")

        if decision == "approved" and not draft.evidence_verified:
            raise ValueError(
                "Cannot approve draft without verified evidence"
            )

        old_status = draft.status
        draft.status = decision

        db.add(
            ApprovalHistory(
                draft_id=draft.id,
                action=decision,
                previous_status=old_status,
                new_status=decision,
                comments=comments
            )
        )

        db.commit()

        return {
            "id": draft.id,
            "draft_type": draft.draft_type,
            "status": draft.status,
            "message": f"Draft {decision} successfully"
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()