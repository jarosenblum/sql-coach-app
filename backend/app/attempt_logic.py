from __future__ import annotations

from app.schemas import QuestionProgress


def get_attempt_count(qp: QuestionProgress) -> int:
    return len(qp.attempts)


def next_hint_level(qp: QuestionProgress) -> int:
    current = qp.hint_level_used
    if current < 3:
        return current + 1
    return 3


def can_show_full_solution(qp: QuestionProgress, explicit_request: bool = False) -> bool:
    return explicit_request and get_attempt_count(qp) >= 2


def recommended_hint_level_from_attempts(qp: QuestionProgress) -> int:
    attempts = get_attempt_count(qp)
    if attempts <= 1:
        return 1
    if attempts == 2:
        return 2
    return 3