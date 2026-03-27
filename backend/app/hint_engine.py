from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

from app.attempt_logic import next_hint_level
from app.question_bank import QUESTION_BANK
from app.schemas import HintLevel, QuestionProgress

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_hint_prompt(question_id: str, qp: QuestionProgress, student_message: str = "") -> tuple[HintLevel, str]:
    question = QUESTION_BANK[question_id]
    concept = question["concept"]
    task = question["task"]
    hint_level = next_hint_level(qp)

    prior_attempts = []
    for a in qp.attempts:
        prior_attempts.append(
            f"Attempt {a.attempt_number}\nSQL: {a.sql_query}\nResult: {a.sandbox_result}\nExplanation: {a.explanation}\n"
        )
    prior_attempts_text = "\n".join(prior_attempts) if prior_attempts else "No attempts yet."

    prompt = f"""You are a SQL tutor giving a controlled hint.

Question ID: {question_id}
Concept: {concept}
Task: {task}
Hint Level: {hint_level}

Student message:
{student_message or "No extra message provided."}

Prior attempts:
{prior_attempts_text}

Rules:
- Do NOT provide the full SQL answer.
- Level 1 = conceptual hint only
- Level 2 = query blueprint only
- Level 3 = scaffold with blanks only
- Keep the hint concise
"""

    return hint_level, prompt


def get_hint(question_id: str, qp: QuestionProgress, student_message: str = "") -> tuple[HintLevel, str]:
    hint_level, prompt = build_hint_prompt(question_id, qp, student_message)

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "You are a concise SQL tutor. Never provide the full SQL answer as a hint."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return hint_level, resp.choices[0].message.content or ""