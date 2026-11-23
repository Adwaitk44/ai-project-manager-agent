from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException
)
from sqlalchemy import text
from datetime import date

from backend.database import init_db, SessionLocal

from backend.services.meeting_service import process_meeting
from backend.services.storage_service import save_meeting

from backend.services.approval_service import (
    get_pending_drafts,
    get_jira_created_drafts,
    edit_draft,
    decide_draft
)

from backend.services.jira_service import (
    create_jira_issue_for_draft
)

from backend.models.schemas import (
    DraftEditRequest,
    DraftDecisionRequest
)


app = FastAPI(
    title="AI Project Manager Agent",
    description="AI-powered project management assistant",
    version="1.1.0"
)


def migrate_jira_columns():
    db = SessionLocal()

    try:
        existing_columns = {
            row[1]
            for row in db.execute(
                text("PRAGMA table_info(drafts)")
            ).fetchall()
        }

        migrations = {
            "jira_issue_key": "VARCHAR(50)",
            "jira_issue_url": "VARCHAR(500)",
            "jira_created_at": "DATETIME",
            "jira_creation_status": "VARCHAR(30) DEFAULT 'not_started'",
            "jira_error": "TEXT"
        }

        for column, column_type in migrations.items():
            if column not in existing_columns:
                db.execute(
                    text(
                        f"ALTER TABLE drafts ADD COLUMN "
                        f"{column} {column_type}"
                    )
                )

        db.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_drafts_jira_issue_key "
                "ON drafts(jira_issue_key)"
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


init_db()
migrate_jira_columns()


@app.get("/")
def home():
    return {
        "message": "AI Project Manager Agent",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze-meeting")
async def analyze_meeting_api(
    meeting_date: date = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename or not file.filename.lower().endswith(
        (".txt", ".vtt")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only TXT and VTT files are supported"
        )

    content = await file.read()

    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File size must be below 2 MB"
        )

    try:
        transcript = content.decode("utf-8-sig")

        if not transcript.strip():
            raise HTTPException(
                status_code=400,
                detail="Transcript cannot be empty"
            )

        result = process_meeting(
            transcript=transcript,
            meeting_date=meeting_date.isoformat()
        )

        meeting_id = save_meeting(
            meeting_date=meeting_date.isoformat(),
            filename=file.filename,
            transcript=transcript,
            analysis=result
        )

        return {
            "status": "success",
            "message": "Meeting analyzed and saved",
            "meeting_id": meeting_id,
            "meeting_date": meeting_date.isoformat(),
            "filename": file.filename,
            "analysis": result
        }

    except HTTPException:
        raise

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Transcript must be UTF-8 encoded"
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Meeting analysis failed: {str(error)}"
        )


@app.get("/drafts/pending")
def pending_drafts():
    return {
        "status": "success",
        "drafts": get_pending_drafts()
    }


@app.get("/drafts/jira-created")
def jira_created_drafts():
    return {
        "status": "success",
        "drafts": get_jira_created_drafts()
    }


@app.put("/drafts/{draft_id}")
def update_draft(
    draft_id: int,
    data: DraftEditRequest
):
    try:
        result = edit_draft(draft_id, data)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Draft not found"
            )

        return {
            "status": "success",
            "draft": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@app.post("/drafts/{draft_id}/approve")
def approve_draft(
    draft_id: int,
    data: DraftDecisionRequest
):
    try:
        result = decide_draft(
            draft_id,
            "approved",
            data.comments
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Draft not found"
            )

        jira_result = {
            "status": "not_applicable",
            "message": "Only approved action items are sent to Jira"
        }

        if result["draft_type"] == "action_item":
            jira_result = create_jira_issue_for_draft(draft_id)

        return {
            "status": "success",
            "approval": result,
            "jira": jira_result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@app.post("/drafts/{draft_id}/sync-jira")
def sync_draft_to_jira(draft_id: int):
    result = create_jira_issue_for_draft(draft_id)

    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return {
        "status": "success",
        "jira": result
    }


@app.post("/drafts/{draft_id}/reject")
def reject_draft(
    draft_id: int,
    data: DraftDecisionRequest
):
    try:
        result = decide_draft(
            draft_id,
            "rejected",
            data.comments
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Draft not found"
            )

        return {
            "status": "success",
            "result": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )