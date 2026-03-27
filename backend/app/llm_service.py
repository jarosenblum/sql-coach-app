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