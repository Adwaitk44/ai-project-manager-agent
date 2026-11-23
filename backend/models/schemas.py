
from pydantic import BaseModel, Field
from typing import Optional, List


class ActionItem(BaseModel):
    description: str
    owner: Optional[str] = None
    due_date: Optional[str] = None
    evidence: str
    source_speaker: Optional[str] = None


class Decision(BaseModel):
    description: str
    evidence: str


class Risk(BaseModel):
    description: str
    risk_type: str
    evidence: str


class ScopeChange(BaseModel):
    description: str
    status: str = "proposed"
    evidence: str


class MeetingAnalysis(BaseModel):
    summary: str
    decisions: List[Decision] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    scope_changes: List[ScopeChange] = Field(default_factory=list)


class DraftEditRequest(BaseModel):
    description: str = Field(min_length=1)
    owner: Optional[str] = None
    due_date: Optional[str] = None


class DraftDecisionRequest(BaseModel):
    comments: Optional[str] = None
