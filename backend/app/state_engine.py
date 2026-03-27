from __future__ import annotations

import uuid

from app.question_bank import QUESTION_ORDER
from app.schemas import AttemptRecord, QuestionProgress, SessionState


def new_session() -> SessionState:
    session_id = f"SQL302F-Session-{str(uuid.uuid4().int)[:6]}"
    progress = {
        qid: QuestionProgress(question_id=qid)
        for qid in QUESTION_ORDER
    }
    return SessionState(
        session_id=session_id,
        current_question_id="Q1",
        question_progress=progress,
    )


def next_question_id(current_question_id: str) -> str | None:
    idx = QUESTION_ORDER.index(current_question_id)
    if idx + 1 >= len(QUESTION_ORDER):
        return None
    return QUESTION_ORDER[idx + 1]


def mark_question_complete(state: SessionState, question_id: str) -> None:
    qp = state.question_progress[question_id]
    qp.status = "complete"
    if question_id not in state.completed_questions:
        state.completed_questions.append(question_id)

    nxt = next_question_id(question_id)
    if nxt:
        state.current_question_id = nxt
    else:
        state.current_question_id = "COMPLETE"


def checkpoint_required(state: SessionState) -> bool:
    return "Q5" in state.completed_questions and not state.checkpoint_completed and state.current_question_id != "Q5"


def record_attempt(
    state: SessionState,
    question_id: str,
    sql_query: str,
    sandbox_result: str,
    explanation: str,
    evaluation_score: int,
    evaluation_note: str,
    explanation_score: int,
    explanation_note: str,
    error_type: str | None = None,
    concept_to_reinforce: str | None = None,
    feedback_mode: str | None = None,
) -> None:
    qp = state.question_progress[question_id]
    qp.status = "in_progress"
    qp.last_error_type = error_type
    qp.last_feedback_mode = feedback_mode  # type: ignore[assignment]

    qp.attempts.append(
        AttemptRecord(
            attempt_number=len(qp.attempts) + 1,
            sql_query=sql_query,
            sandbox_result=sandbox_result,
            explanation=explanation,
            evaluation_score=evaluation_score,
            evaluation_note=evaluation_note,
            explanation_score=explanation_score,
            explanation_note=explanation_note,
            error_type=error_type,
            concept_to_reinforce=concept_to_reinforce,
            feedback_mode=feedback_mode,  # type: ignore[arg-type]
        )
    )