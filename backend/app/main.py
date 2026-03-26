from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.llm_service import evaluate_submission, get_concept_intro
from app.question_bank import QUESTION_BANK
from app.report_engine import build_report
from app.schemas import PrintReportResponse, StartSessionResponse, StudentTurnRequest, StudentTurnResponse
from app.state_engine import checkpoint_required, mark_question_complete, new_session, record_attempt
from app.storage import load_session, save_session

app = FastAPI(title="SQL Coach App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/start", response_model=StartSessionResponse)
def start_session() -> StartSessionResponse:
    state = new_session()
    save_session(state)
    return StartSessionResponse(
        session_id=state.session_id,
        message="Session started. Open the W3Schools SQL Try-It sandbox in a new tab.",
        menu=[
            "Start assignment walkthrough",
            "Continue assignment",
            "Print Session Report",
            "Save and Exit",
        ],
    )


@app.post("/concept-intro/{session_id}", response_model=StudentTurnResponse)
def concept_intro(session_id: str) -> StudentTurnResponse:
    state = load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    qid = state.current_question_id
    intro = get_concept_intro(qid)
    return StudentTurnResponse(
        assistant_message=intro,
        session_id=session_id,
        current_question_id=qid,
    )


@app.post("/submit", response_model=StudentTurnResponse)
def submit_turn(req: StudentTurnRequest) -> StudentTurnResponse:
    state = load_session(req.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # For MVP, expect a compact payload format in req.message
    # SQL:::... RESULT:::... EXPLANATION:::...
    try:
        parts = dict(
            item.split(":::", 1) for item in req.message.split("\n") if ":::" in item
        )
        sql_query = parts["SQL"]
        sandbox_result = parts["RESULT"]
        explanation = parts.get("EXPLANATION", "")
    except Exception as exc:
        return StudentTurnResponse(
            assistant_message="Please send your turn as SQL:::... RESULT:::... EXPLANATION:::...",
            session_id=state.session_id,
            current_question_id=state.current_question_id,
        )

    qid = state.current_question_id
    eval_json = evaluate_submission(qid, sql_query, sandbox_result, explanation)
    score = int(eval_json.get("correctness_score", 0))
    note = str(eval_json.get("correctness_note", "No evaluation note provided"))
    should_advance = bool(eval_json.get("should_advance", False))
    feedback = str(eval_json.get("feedback_to_student", "Please revise and try again."))

    record_attempt(state, qid, sql_query, sandbox_result, explanation, score, note)

    if should_advance:
        mark_question_complete(state, qid)

    if checkpoint_required(state):
        save_session(state)
        return StudentTurnResponse(
            assistant_message="Checkpoint reached after Q5. Use Save and Exit now, then resume later.",
            session_id=state.session_id,
            current_question_id=state.current_question_id,
            require_checkpoint=True,
        )

    save_session(state)
    return StudentTurnResponse(
        assistant_message=feedback,
        session_id=state.session_id,
        current_question_id=state.current_question_id,
    )


@app.get("/report/{session_id}", response_model=PrintReportResponse)
def get_report(session_id: str) -> PrintReportResponse:
    state = load_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return PrintReportResponse(session_id=session_id, report_text=build_report(state))