from __future__ import annotations

from typing import Any, Dict

from app.schemas import FeedbackMode, QuestionProgress


def choose_feedback_mode(eval_json: Dict[str, Any], qp: QuestionProgress) -> FeedbackMode:
    correctness = int(eval_json.get("correctness_score", 0))
    explanation = int(eval_json.get("explanation_score", 0))
    error_type = eval_json.get("error_type")

    if correctness == 2 and explanation == 2:
        return "affirm_correct"

    if error_type and correctness <= 1:
        return "concept_reinforcement"

    if correctness == 1 or explanation == 1:
        return "targeted_correction"

    return "retry_prompt"


def _clean(text: Any) -> str:
    return str(text or "").strip()


def build_adaptive_feedback(eval_json: Dict[str, Any], qp: QuestionProgress) -> str:
    mode = choose_feedback_mode(eval_json, qp)

    student_feedback = _clean(eval_json.get("feedback_to_student"))
    concept = _clean(eval_json.get("concept_to_reinforce"))
    correctness_note = _clean(eval_json.get("correctness_note"))
    explanation_note = _clean(eval_json.get("explanation_note"))

    if mode == "affirm_correct":
        if student_feedback:
            return student_feedback

        parts = []

        if correctness_note:
            parts.append(f"Correct. {correctness_note}")
        else:
            parts.append("Correct. Your SQL query matches the current question.")

        if explanation_note:
            parts.append(f"Your explanation is also on the right track. {explanation_note}")
        else:
            parts.append("Your explanation also matches the main SQL idea in this question.")

        if concept:
            parts.append(f"Key idea: {concept} is the concept driving this result.")

        return " ".join(parts)

    if mode == "concept_reinforcement":
        if student_feedback:
            return student_feedback

        parts = []

        if correctness_note:
            parts.append(correctness_note)
        else:
            parts.append("You are close, but one important part of the query still needs revision.")

        if concept:
            parts.append(f"Focus on the current SQL concept: {concept}.")
        else:
            parts.append("Focus on the main SQL concept for this question.")

        if explanation_note:
            parts.append(explanation_note)

        parts.append("Revise your query and try again.")
        return " ".join(parts)

    if mode == "targeted_correction":
        if student_feedback:
            return student_feedback

        parts = []

        if correctness_note:
            parts.append(correctness_note)
        else:
            parts.append("Your answer is partly correct, but one part still needs adjustment.")

        if explanation_note:
            parts.append(explanation_note)

        if concept:
            parts.append(f"Stay focused on the concept: {concept}.")

        parts.append("Make a small revision and try again.")
        return " ".join(parts)

    if student_feedback:
        return student_feedback

    parts = []

    if correctness_note:
        parts.append(correctness_note)
    else:
        parts.append("This answer is not correct yet for the current question.")

    if explanation_note:
        parts.append(explanation_note)

    if concept:
        parts.append(f"Return to the core concept: {concept}.")

    parts.append("Revise your query and explanation, then try again.")
    return " ".join(parts)