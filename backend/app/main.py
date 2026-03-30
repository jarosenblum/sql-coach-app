from __future__ import annotations

from datetime import datetime
import time
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.adaptive_feedback import build_adaptive_feedback, choose_feedback_mode
from app.attempt_logic import recommended_hint_level_from_attempts
from app.hint_engine import get_hint
from app.llm_service import (
    evaluate_submission,
    generate_support_chat_response,
    get_concept_intro,
)
from app.question_bank import QUESTION_BANK
from app.report_engine import build_report
from app.result_validator import validate_result_for_question
from app.schemas import (
    HintRequest,
    HintResponse,
    PrintReportResponse,
    ResumeRequest,
    StartSessionResponse,
    StudentTurnRequest,
    StudentTurnResponse,
    SupportChatRequest,
    SupportChatResponse,
)
from app.sql_runner import execute_student_sql
from app.state_engine import (
    checkpoint_required,
    mark_question_complete,
    new_session,
    record_attempt,
)
from app.storage import load_session, save_session

app = FastAPI(title="SQL Coach App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


LOG_DIR = "logs"

def log_event(event: str, **fields) -> None:
    timestamp = datetime.utcnow().isoformat()
    payload = " | ".join(f"{k}={v}" for k, v in fields.items())
    line = f"{timestamp} | {event}" + (f" | {payload}" if payload else "")

    # Keep existing behavior (Render logs)
    print(line)

    # --- per-session logging ---
    session_id = fields.get("session_id", "unknown")

    os.makedirs(LOG_DIR, exist_ok=True)
    file_path = os.path.join(LOG_DIR, f"{session_id}.log")

    try:
        # overwrite file on session start
        if event == "SESSION_START":
            with open(file_path, "w") as f:
                f.write(line + "\n")
        else:
            with open(file_path, "a") as f:
                f.write(line + "\n")

    except Exception as e:
        print(f"LOG_WRITE_FAIL | session_id={session_id} | error={e}")


def _is_low_information_text(text: str) -> bool:
    cleaned = (text or "").strip().lower()

    low_info_values = {
        "?",
        "idk",
        "i dunno",
        "dunno",
        "dont know",
        "don't know",
        "worked",
        "it worked",
        "fine",
        "ok",
        "okay",
        "yes",
        "no",
        "n/a",
        "what",
        "idk lol",
    }

    if cleaned in low_info_values:
        return True

    if len(cleaned.split()) < 4:
        return True

    return False


def _explanation_matches_question_concept(question_id: str, explanation: str) -> bool:
    cleaned = (explanation or "").strip().lower()
    keywords = QUESTION_BANK.get(question_id, {}).get("explanation_keywords", [])

    if not keywords:
        return True

    match_count = 0
    for kw in keywords:
        if kw.lower() in cleaned:
            match_count += 1

    return match_count >= 1


def _extract_session_id_from_report(report_text: str) -> str:
    for line in report_text.splitlines():
        line = line.strip()
        if line.lower().startswith("session id:"):
            return line.split(":", 1)[1].strip()
    raise ValueError("Session ID not found in report")


def _extract_completed_questions_from_report(report_text: str) -> list[str]:
    for line in report_text.splitlines():
        line = line.strip()
        if line.lower().startswith("completed questions:"):
            raw = line.split(":", 1)[1].strip()
            if not raw or raw.lower() in {"none", "n/a"}:
                return []
            return [q.strip() for q in raw.split(",") if q.strip()]
    return []


def _next_question_id_from_completed(completed_questions: list[str]) -> str:
    ordered = list(QUESTION_BANK.keys())
    completed_set = set(completed_questions)

    for qid in ordered:
        if qid not in completed_set:
            return qid

    return ordered[-1]


@app.get("/")
def root():
    return {"message": "SQL Coach backend is running"}


@app.post("/start", response_model=StartSessionResponse)
def start_session() -> StartSessionResponse:
    state = new_session()
    save_session(state)
    log_event("SESSION_START", session_id=state.session_id)

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
        log_event("CONCEPT_INTRO_FAIL", session_id=session_id, reason="session_not_found")
        raise HTTPException(status_code=404, detail="Session not found")

    qid = state.current_question_id
    if not qid:
        log_event("CONCEPT_INTRO_FAIL", session_id=session_id, reason="no_active_question")
        raise HTTPException(status_code=400, detail="No active question. Please start a session.")

    try:
        intro = get_concept_intro(qid)
        log_event("CONCEPT_INTRO_OK", session_id=session_id, question_id=qid)
    except Exception as e:
        log_event(
            "CONCEPT_INTRO_ERROR",
            session_id=session_id,
            question_id=qid,
            error=type(e).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Concept intro failed: {type(e).__name__}: {str(e)}",
        )

    return StudentTurnResponse(
        assistant_message=intro,
        session_id=session_id,
        current_question_id=qid,
    )


@app.get("/resume/{session_id}", response_model=StudentTurnResponse)
def resume_session(session_id: str) -> StudentTurnResponse:
    state = load_session(session_id)
    if not state:
        log_event("SESSION_RESUME_BROWSER_FAIL", session_id=session_id, reason="session_not_found")
        raise HTTPException(status_code=404, detail="Session not found")

    qid = state.current_question_id
    if not qid:
        log_event("SESSION_RESUME_BROWSER_FAIL", session_id=state.session_id, reason="no_active_question")
        raise HTTPException(status_code=400, detail="No active question in saved session.")

    try:
        intro = get_concept_intro(qid)
        log_event("SESSION_RESUME_BROWSER_OK", session_id=state.session_id, question_id=qid)
    except Exception as e:
        log_event(
            "SESSION_RESUME_BROWSER_ERROR",
            session_id=state.session_id,
            question_id=qid,
            error=type(e).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Resume failed: {type(e).__name__}: {str(e)}",
        )

    return StudentTurnResponse(
        assistant_message=intro,
        session_id=state.session_id,
        current_question_id=qid,
        require_checkpoint=False,
        show_report=False,
        report_text=None,
        feedback_mode=None,
        recommended_hint_level=None,
        should_advance=False,
    )


@app.post("/resume-from-report", response_model=StudentTurnResponse)
def resume_from_report(req: ResumeRequest) -> StudentTurnResponse:
    report_text = (req.saved_report_text or "").strip()
    log_event("SESSION_RESUME_REPORT_ATTEMPT")

    if not report_text:
        log_event("SESSION_RESUME_REPORT_FAIL", reason="empty_report")
        raise HTTPException(status_code=400, detail="Saved session report is required.")

    try:
        session_id = _extract_session_id_from_report(report_text)
        completed_questions = _extract_completed_questions_from_report(report_text)
        current_question_id = _next_question_id_from_completed(completed_questions)

        state = load_session(session_id)
        if not state:
            state = new_session()
            state.session_id = session_id

        state.completed_questions = completed_questions
        state.current_question_id = current_question_id
        save_session(state)

        intro = get_concept_intro(current_question_id)

        log_event(
            "SESSION_RESUME_REPORT_OK",
            session_id=state.session_id,
            question_id=current_question_id,
            completed=len(completed_questions),
        )

        return StudentTurnResponse(
            assistant_message=intro,
            session_id=state.session_id,
            current_question_id=current_question_id,
            require_checkpoint=False,
            show_report=False,
            report_text=None,
            feedback_mode=None,
            recommended_hint_level=None,
            should_advance=False,
        )
    except Exception as e:
        log_event("SESSION_RESUME_REPORT_FAIL", error=type(e).__name__)
        raise HTTPException(
            status_code=400,
            detail=f"Could not resume from report: {type(e).__name__}: {str(e)}",
        )


@app.post("/submit", response_model=StudentTurnResponse)
def submit_turn(req: StudentTurnRequest) -> StudentTurnResponse:
    submit_started = time.time()

    state = load_session(req.session_id)
    if not state:
        log_event("SUBMIT_FAIL", session_id=req.session_id, reason="session_not_found")
        raise HTTPException(status_code=404, detail="Session not found")

    qid = state.current_question_id
    if not qid:
        log_event("SUBMIT_FAIL", session_id=state.session_id, reason="no_active_question")
        raise HTTPException(status_code=400, detail="No active question. Please start a session.")

    log_event("SUBMIT_RECEIVED", session_id=state.session_id, question_id=qid)

    try:
        qp = state.question_progress[qid]
    except KeyError:
        log_event(
            "SUBMIT_FAIL",
            session_id=state.session_id,
            question_id=qid,
            reason="question_progress_not_found",
        )
        raise HTTPException(status_code=404, detail="Question progress not found")

    response_question_id = qid
    should_advance = False

    try:
        def extract_section(text: str, start_key: str, end_key: str | None = None) -> str:
            start_marker = f"{start_key}:::"
            if start_marker not in text:
                return ""
            section = text.split(start_marker, 1)[1]
            if end_key:
                end_marker = f"{end_key}:::"
                if end_marker in section:
                    section = section.split(end_marker, 1)[0]
            return section.strip()

        sql_query = extract_section(req.message, "SQL", "RESULT")
        sandbox_result = extract_section(req.message, "RESULT", "EXPLANATION")
        explanation = extract_section(req.message, "EXPLANATION")

        if not sql_query or not sandbox_result:
            raise ValueError("Missing required submission sections")

        log_event(
            "SUBMIT_PARSED",
            session_id=state.session_id,
            question_id=qid,
            sql_len=len(sql_query),
            sql_lines=sql_query.count("\n") + 1,
            result_len=len(sandbox_result),
            explanation_len=len(explanation),
        )
    except Exception:
        log_event(
            "SUBMIT_FAIL",
            session_id=state.session_id,
            question_id=qid,
            reason="invalid_submission_format",
        )
        raise HTTPException(
            status_code=400,
            detail="Submission format is invalid. Please submit SQL, Sandbox Result, and Explanation.",
        )

    if not sql_query:
        log_event("SUBMIT_FAIL", session_id=state.session_id, question_id=qid, reason="missing_sql")
        raise HTTPException(status_code=400, detail="SQL query is required.")

    if not sandbox_result:
        log_event("SUBMIT_FAIL", session_id=state.session_id, question_id=qid, reason="missing_sandbox_result")
        raise HTTPException(
            status_code=400,
            detail=(
                "A Sandbox Result is required. Run your query in W3Schools and describe the output, "
                "including rows, columns, or the exact error message."
            ),
        )

    if not explanation:
        log_event("SUBMIT_FAIL", session_id=state.session_id, question_id=qid, reason="missing_explanation")
        raise HTTPException(
            status_code=400,
            detail="An Explanation is required. Describe what your query does.",
        )

    if _is_low_information_text(sandbox_result):
        log_event(
            "SUBMIT_FAIL",
            session_id=state.session_id,
            question_id=qid,
            reason="low_information_sandbox_result",
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "Please describe what you observed in W3Schools in more detail. "
                "Include row count, visible columns, sample rows, or the exact error message."
            ),
        )

    if _is_low_information_text(explanation):
        log_event(
            "SUBMIT_FAIL",
            session_id=state.session_id,
            question_id=qid,
            reason="low_information_explanation",
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "Please explain what your query does in your own words. "
                "For example: what table you are querying, what columns you are returning, "
                "and what the result represents."
            ),
        )

    if not _explanation_matches_question_concept(qid, explanation):
        concept = QUESTION_BANK.get(qid, {}).get("concept", "this SQL concept")
        keywords = QUESTION_BANK.get(qid, {}).get("explanation_keywords", [])
        keyword_hint = ", ".join(keywords[:3]) if keywords else concept

        log_event(
            "SUBMIT_FAIL",
            session_id=state.session_id,
            question_id=qid,
            reason="concept_mismatch_explanation",
        )
        raise HTTPException(
            status_code=400,
            detail=(
                f"Your explanation does not yet describe the main idea for {concept}. "
                f"Try mentioning ideas like: {keyword_hint}."
            ),
        )

    try:
        log_event("SQL_EXECUTE_START", session_id=state.session_id, question_id=qid)
        computed_result = execute_student_sql(sql_query)

        if not computed_result.get("executed", False):
            log_event(
                "SQL_EXECUTE_FAIL",
                session_id=state.session_id,
                question_id=qid,
                error=computed_result.get("error", "unknown"),
            )
            raise HTTPException(
                status_code=400,
                detail=f"Your SQL did not run successfully: {computed_result.get('error', 'Unknown SQL error.')}",
            )

        log_event(
            "SQL_EXECUTE_OK",
            session_id=state.session_id,
            question_id=qid,
            row_count=computed_result.get("row_count", "na"),
        )

        validation_result = validate_result_for_question(qid, computed_result)

        eval_json = evaluate_submission(
            qid,
            sql_query,
            sandbox_result,
            explanation,
            computed_result,
            validation_result,
        )

        correctness_score = int(eval_json.get("correctness_score", 0))
        correctness_note = str(
            eval_json.get("correctness_note", "No evaluation note provided")
        )

        explanation_score = int(eval_json.get("explanation_score", 0))
        explanation_note = str(
            eval_json.get("explanation_note", "No explanation note provided")
        )

        error_type = eval_json.get("error_type")
        concept_to_reinforce = eval_json.get("concept_to_reinforce")

        should_advance = correctness_score == 2 and explanation_score >= 1

        feedback_mode = choose_feedback_mode(eval_json, qp)
        feedback = build_adaptive_feedback(eval_json, qp)

        print("DEBUG correctness_score:", correctness_score)
        print("DEBUG explanation_score:", explanation_score)
        print("DEBUG should_advance:", should_advance)
        print("DEBUG feedback:", feedback)

        log_event(
            "EVAL_RESULT",
            session_id=state.session_id,
            question_id=qid,
            correctness_score=correctness_score,
            explanation_score=explanation_score,
            should_advance=should_advance,
            feedback_mode=feedback_mode,
        )

        record_attempt(
            state=state,
            question_id=qid,
            sql_query=sql_query,
            sandbox_result=sandbox_result,
            explanation=explanation,
            evaluation_score=correctness_score,
            evaluation_note=correctness_note,
            explanation_score=explanation_score,
            explanation_note=explanation_note,
            error_type=error_type,
            concept_to_reinforce=concept_to_reinforce,
            feedback_mode=feedback_mode,
        )

        updated_qp = state.question_progress.get(qid, qp)

        if should_advance:
            old_qid = qid
            mark_question_complete(state, qid)
            log_event(
                "QUESTION_ADVANCE",
                session_id=state.session_id,
                from_question=old_qid,
                to_question=state.current_question_id,
            )
        else:
            log_event("QUESTION_STAY", session_id=state.session_id, question_id=qid)

        if checkpoint_required(state):
            state.checkpoint_completed = True
            save_session(state)
            log_event(
                "CHECKPOINT_TRIGGERED",
                session_id=state.session_id,
                question_id=state.current_question_id,
                latency_sec=round(time.time() - submit_started, 2),
            )
            return StudentTurnResponse(
                assistant_message=(
                    "Checkpoint reached. This is a good place to save your progress. "
                    "Click 'Print Session Report' now and save that report somewhere you can find it. "
                    "If you want to keep going, click 'Continue Assignment'. "
                    "If you need to stop, save your report and come back later using 'Continue Previous Session'."
                ),
                session_id=state.session_id,
                current_question_id=state.current_question_id,
                require_checkpoint=True,
                feedback_mode="checkpoint_prompt",
                recommended_hint_level=recommended_hint_level_from_attempts(updated_qp),
                should_advance=False,
            )

        if state.current_question_id == "COMPLETE":
            save_session(state)
            log_event(
                "SESSION_COMPLETE",
                session_id=state.session_id,
                latency_sec=round(time.time() - submit_started, 2),
            )
            return StudentTurnResponse(
                assistant_message=(
                    "Assignment complete. Click 'Print Session Report' now to save your final work."
                ),
                session_id=state.session_id,
                current_question_id="COMPLETE",
                feedback_mode="affirm_correct",
                recommended_hint_level=recommended_hint_level_from_attempts(updated_qp),
                should_advance=False,
                show_report=False,
            )

        response = StudentTurnResponse(
            assistant_message=feedback,
            session_id=state.session_id,
            current_question_id=state.current_question_id if should_advance else response_question_id,
            feedback_mode=feedback_mode,
            recommended_hint_level=recommended_hint_level_from_attempts(updated_qp),
            should_advance=should_advance,
        )

        save_session(state)
        log_event(
            "SUBMIT_RESPONSE_SENT",
            session_id=state.session_id,
            question_id=qid,
            response_question_id=state.current_question_id if should_advance else response_question_id,
            latency_sec=round(time.time() - submit_started, 2),
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        log_event(
            "SUBMIT_INTERNAL_ERROR",
            session_id=req.session_id,
            question_id=qid if "qid" in locals() else "unknown",
            error=type(e).__name__,
        )
        print("🔥 Internal error in submit_turn:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while processing your submission. Please try again.",
        )


@app.post("/hint", response_model=HintResponse)
def hint(req: HintRequest) -> HintResponse:
    state = load_session(req.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    qid = state.current_question_id
    if not qid:
        raise HTTPException(
            status_code=400,
            detail="No active question. Please start a session.",
        )

    try:
        qp = state.question_progress[qid]
    except KeyError:
        raise HTTPException(status_code=404, detail="Question progress not found")

    try:
        level, hint_text = get_hint(qid, qp, req.student_message or "")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Hint failed: {type(e).__name__}: {str(e)}",
        )

    qp.hint_level_used = level
    save_session(state)

    return HintResponse(
        session_id=state.session_id,
        current_question_id=qid,
        hint_level=level,
        assistant_message=hint_text,
    )


@app.post("/support-chat", response_model=SupportChatResponse)
def support_chat(req: SupportChatRequest) -> SupportChatResponse:
    state = load_session(req.session_id)
    if not state:
        log_event("SUPPORT_CHAT_FAIL", session_id=req.session_id, reason="session_not_found")
        raise HTTPException(status_code=404, detail="Session not found")

    qid = req.question_id or state.current_question_id
    if not qid or qid not in QUESTION_BANK:
        log_event(
            "SUPPORT_CHAT_FAIL",
            session_id=state.session_id,
            reason="invalid_question_id",
        )
        raise HTTPException(status_code=400, detail="Invalid question ID")

    q = QUESTION_BANK[qid]
    concept = q["concept"]
    task = q["task"]

    log_event(
        "SUPPORT_CHAT_REQUEST",
        session_id=state.session_id,
        question_id=qid,
        msg_len=len(req.student_message or ""),
    )

    try:
        message = generate_support_chat_response(
            question_id=qid,
            concept=concept,
            task=task,
            student_message=req.student_message,
            last_feedback=req.last_feedback,
            current_sql=req.current_sql,
        )
        log_event("SUPPORT_CHAT_RESPONSE", session_id=state.session_id, question_id=qid)
        return SupportChatResponse(assistant_message=message)
    except Exception as e:
        log_event(
            "SUPPORT_CHAT_FAIL",
            session_id=state.session_id,
            question_id=qid,
            error=type(e).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Support chat failed: {type(e).__name__}: {str(e)}",
        )


@app.get("/report/{session_id}", response_model=PrintReportResponse)
def get_report(session_id: str) -> PrintReportResponse:
    state = load_session(session_id)
    if not state:
        log_event("REPORT_FAIL", session_id=session_id, reason="session_not_found")
        raise HTTPException(status_code=404, detail="Session not found")

    log_event("REPORT_GENERATED", session_id=session_id, question_id=state.current_question_id)

    return PrintReportResponse(
        session_id=session_id,
        report_text=build_report(state),
    )