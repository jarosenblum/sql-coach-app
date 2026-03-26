from __future__ import annotations

from datetime import date

from app.question_bank import QUESTION_ORDER
from app.schemas import SessionState


def build_report(state: SessionState) -> str:
    lines: list[str] = []
    lines.append("SESSION REPORT")
    lines.append("----------------------------------------")
    lines.append(f"StudentID: {state.student_id or 'Not Provided'}")
    lines.append(f"SessionID: {state.session_id}")
    lines.append(f"Date: {date.today().isoformat()}")
    status = "Complete" if state.current_question_id == "COMPLETE" and state.reflection_completed else "In Progress"
    lines.append(f"Status: {status}")
    lines.append(f"Current Question: {state.current_question_id}")
    lines.append("")
    lines.append("EVALUATION SUMMARY")
    lines.append(f"Questions Completed: {len(state.completed_questions)}")
    lines.append("")

    for qid in QUESTION_ORDER:
        qp = state.question_progress[qid]
        if not qp.attempts:
            continue
        final_attempt = qp.attempts[-1]
        lines.append(f"{qid}: {final_attempt.evaluation_score}/2 — {final_attempt.evaluation_note}")

    lines.append("")
    lines.append("REVISION HIGHLIGHTS")
    any_revision = False
    for qid in QUESTION_ORDER:
        qp = state.question_progress[qid]
        if len(qp.attempts) > 1:
            any_revision = True
            lines.append(f"- {qid}: improved across {len(qp.attempts)} attempts")
    if not any_revision:
        lines.append("- No major revisions recorded")

    lines.append("")
    lines.append("REFLECTION SUMMARY")
    lines.append("Completed" if state.reflection_completed else "Not completed")

    lines.append("")
    lines.append("NEXT STEP")
    if status == "Complete":
        lines.append("Submit this report.")
    else:
        lines.append(f"Continue with {state.current_question_id}")

    lines.append("")
    lines.append("PROGRESSION LOG")
    for qid in QUESTION_ORDER:
        qp = state.question_progress[qid]
        if not qp.attempts:
            continue
        lines.append("----------------------------------------")
        lines.append(f"{qid}")
        for attempt in qp.attempts:
            lines.append(f"Attempt {attempt.attempt_number}")
            lines.append(f"Query: {attempt.sql_query}")
            lines.append(f"Result: {attempt.sandbox_result}")
            lines.append(f"Understanding: {attempt.explanation}")
            lines.append(f"Evaluation: {attempt.evaluation_score}/2 — {attempt.evaluation_note}")

    return "```text\n" + "\n".join(lines) + "\n```"