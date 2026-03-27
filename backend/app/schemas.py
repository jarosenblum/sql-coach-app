from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


QuestionStatus = Literal["not_started", "in_progress", "complete"]
FeedbackMode = Literal[
    "affirm_correct",
    "targeted_correction",
    "concept_reinforcement",
    "retry_prompt",
    "checkpoint_prompt",
]
HintLevel = Literal[0, 1, 2, 3]


class AttemptRecord(BaseModel):
    attempt_number: int
    sql_query: str
    sandbox_result: str
    explanation: str = ""
    evaluation_score: int = 0
    evaluation_note: str = ""
    explanation_score: int = 0
    explanation_note: str = ""
    error_type: Optional[str] = None
    concept_to_reinforce: Optional[str] = None
    feedback_mode: Optional[FeedbackMode] = None


class QuestionProgress(BaseModel):
    question_id: str
    status: QuestionStatus = "not_started"
    attempts: List[AttemptRecord] = Field(default_factory=list)
    concept_score: Optional[int] = None
    concept_note: Optional[str] = None
    hint_level_used: HintLevel = 0
    last_error_type: Optional[str] = None
    last_feedback_mode: Optional[FeedbackMode] = None


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
    feedback_mode: Optional[FeedbackMode] = None
    recommended_hint_level: Optional[HintLevel] = None
    should_advance: bool = False


class ResumeRequest(BaseModel):
    session_id: str
    saved_report_text: str


class PrintReportResponse(BaseModel):
    session_id: str
    report_text: str


class HintRequest(BaseModel):
    session_id: str
    student_message: Optional[str] = ""


class HintResponse(BaseModel):
    session_id: str
    current_question_id: str
    hint_level: HintLevel
    assistant_message: str

class SupportChatRequest(BaseModel):
    session_id: str
    question_id: str
    student_message: str
    last_feedback: Optional[str] = None
    current_sql: Optional[str] = None


class SupportChatResponse(BaseModel):
    assistant_message: str