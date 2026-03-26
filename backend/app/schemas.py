from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


QuestionStatus = Literal["not_started", "in_progress", "complete"]


class AttemptRecord(BaseModel):
    attempt_number: int
    sql_query: str
    sandbox_result: str
    explanation: str = ""
    evaluation_score: int = 0
    evaluation_note: str = ""


class QuestionProgress(BaseModel):
    question_id: str
    status: QuestionStatus = "not_started"
    attempts: List[AttemptRecord] = Field(default_factory=list)
    concept_score: Optional[int] = None
    concept_note: Optional[str] = None


class SessionState(BaseModel):
    session_id: str
    student_id: Optional[str] = None
    current_question_id: str = "Q1"
    completed_questions: List[str] = Field(default_factory=list)
    checkpoint_completed: bool = False
    reflection_completed: bool = False
    question_progress: Dict[str, QuestionProgress] = Field(default_factory=dict)


class StartSessionResponse(BaseModel):
    session_id: str
    message: str
    menu: List[str]


class StudentTurnRequest(BaseModel):
    session_id: str
    message: str


class StudentTurnResponse(BaseModel):
    assistant_message: str
    session_id: str
    current_question_id: str
    require_checkpoint: bool = False
    show_report: bool = False
    report_text: Optional[str] = None


class ResumeRequest(BaseModel):
    session_id: str
    saved_report_text: str


class PrintReportResponse(BaseModel):
    session_id: str
    report_text: str