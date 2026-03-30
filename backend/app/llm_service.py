from __future__ import annotations

import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from app.prompts import concept_intro_prompt, evaluation_prompt

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _clean_json_content(content: str) -> str:
    content = content.strip()

    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].strip()

    return content.strip()


def get_concept_intro(question_id: str) -> str:
    prompt = concept_intro_prompt(question_id)
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise SQL tutor. "
                    "Teach only the concept required for the current question. "
                    "Do not introduce future SQL concepts early. "
                    "Teach reasoning, not answers."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def evaluate_submission(
    question_id: str,
    sql_query: str,
    sandbox_result: str,
    explanation: str,
    computed_result: dict,
    validation_result: dict,
) -> dict:
    prompt = evaluation_prompt(
        question_id,
        sql_query,
        sandbox_result,
        explanation,
        computed_result,
        validation_result,
    )

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "Return valid JSON only. "
                    "Evaluate ONLY the current question. "
                    "Do NOT reference future questions, future concepts, later optimizations, "
                    "or better practices that belong to later steps in the assignment. "
                    "Do NOT suggest selecting specific columns unless that is required by the current question. "
                    "Do NOT provide full SQL answers. "
                    "If the student's answer is correct for the current question, keep feedback scoped to that question only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    content = resp.choices[0].message.content or "{}"
    content = _clean_json_content(content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON: {content}") from e

    return data

def generate_support_chat_response(
    question_id: str,
    concept: str,
    task: str,
    student_message: str,
    last_feedback: str | None = None,
    current_sql: str | None = None,
) -> str:
    prompt = f"""You are a SQL support coach for a structured assignment.

Current question: {question_id}
Current concept: {concept}
Task: {task}

Last feedback from the evaluator:
{last_feedback or "None"}

Student's current SQL attempt:
{current_sql or "None provided"}

Student question:
{student_message}

Rules:
- Help the student understand the concept and debug their thinking.
- Keep the response supportive, clear, and concise.
- Do NOT provide the exact corrected SQL query.
- Do NOT rewrite the student's query into a corrected version, even partially.
- Do NOT provide exact replacement column names, table names, or clause values unless the current question explicitly allows that level of help.
- Prefer conceptual hints, debugging strategies, and self-check prompts over direct corrections.
- If the student used an incorrect identifier, tell them to compare their identifier against the schema, but do not reveal the exact correct identifier.
- Never reveal the full answer through “examples,” “possible fixes,” or “double-check whether it is X” phrasing.
- If the student asks for the exact answer, refuse briefly and instead provide a concept hint, a debugging step, or a self-check question.
- Keep help one step short of the solution.
"""

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful SQL support coach. "
                    "Do not provide full final answers for the current assignment question."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return resp.choices[0].message.content or ""