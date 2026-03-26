from __future__ import annotations

from app.question_bank import QUESTION_BANK


def concept_intro_prompt(question_id: str) -> str:
    q = QUESTION_BANK[question_id]
    concept = q["concept"]
    task = q["task"]
    thinking = "\n".join(f"- {x}" for x in q["expected_thinking"])

    if question_id in {"Q8", "Q10", "Q11"}:
        return f"""Question {question_id}

Concept: {concept}

Task:
{task}

Use structured scaffolding.

Query Blueprint:
{thinking}

Give:
1. a short concept explanation
2. a clause-by-clause guide
3. a SQL scaffold with blanks

Do not give the full SQL answer.
"""
    return f"""Question {question_id}

Concept: {concept}

Task:
{task}

Expected thinking:
{thinking}

Give:
1. a short concept explanation
2. a simple syntax pattern
3. a simple example unrelated to the exact answer if possible

Do not give the full SQL answer.
"""


def evaluation_prompt(question_id: str, sql_query: str, sandbox_result: str, explanation: str) -> str:
    task = QUESTION_BANK[question_id]["task"]
    return f"""You are evaluating one SQL assignment question.

Question ID: {question_id}
Task: {task}

Student SQL:
{sql_query}

Sandbox result:
{sandbox_result}

Student explanation:
{explanation}

Return JSON with:
- correctness_score: 0, 1, or 2
- correctness_note: concise
- explanation_score: 0, 1, or 2
- explanation_note: concise
- should_advance: true/false
- feedback_to_student: brief, no full solution
"""