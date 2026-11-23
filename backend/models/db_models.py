
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    meeting_date = Column(String(20))
    filename = Column(String(255))
    transcript = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    transcript_lines = relationship(
        "TranscriptLine",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )

    drafts = relationship(
        "Draft",
        back_populates="meeting",
        cascade="all, delete-orphan"
    )


class TranscriptLine(Base):
    __tablename__ = "transcript_lines"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    line_number = Column(Integer)
    speaker = Column(String(100), nullable=True)
    text = Column(Text)

    meeting = relationship(
        "Meeting",
        back_populates="transcript_lines"
    )


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))

    draft_type = Column(String(50))
    description = Column(Text)
    owner = Column(String(100), nullable=True)
    due_date = Column(String(30), nullable=True)
    evidence = Column(Text)

    source_line_number = Column(Integer, nullable=True)
    evidence_verified = Column(Boolean, default=False)

    status = Column(String(30), default="pending")

    # Jira integration fields
    jira_issue_key = Column(
        String(50),
        nullable=True,
        unique=True
    )

    jira_issue_url = Column(
        String(500),
        nullable=True
    )

    jira_created_at = Column(
        DateTime,
        nullable=True
    )

    jira_creation_status = Column(
        String(30),
        default="not_started"
    )

    jira_error = Column(
        Text,
        nullable=True
    )

    meeting = relationship(
        "Meeting",
        back_populates="drafts"
    )


class ApprovalHistory(Base):
    __tablename__ = "approval_history"

    id = Column(Integer, primary_key=True, index=True)

    draft_id = Column(
        Integer,
        ForeignKey("drafts.id"),
        nullable=False
    )

    action = Column(String(30), nullable=False)
    previous_status = Column(String(30))
    new_status = Column(String(30))

    changed_by = Column(
        String(100),
        default="project_manager"
    )

    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
