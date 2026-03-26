from __future__ import annotations

import json
import os
from typing import Any, Dict

from openai import OpenAI

from app.prompts import concept_intro_prompt, evaluation_prompt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_concept_intro(question_id: str) -> str:
    prompt = concept_intro_prompt(question_id)
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.2-mini"),
        messages=[
            {"role": "system", "content": "You are a concise SQL tutor. Teach reasoning, not answers."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def evaluate_submission(question_id: str, sql_query: str, sandbox_result: str, explanation: str) -> Dict[str, Any]:
    prompt = evaluation_prompt(question_id, sql_query, sandbox_result, explanation)
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.2-mini"),
        messages=[
            {"role": "system", "content": "Return valid JSON only. Do not provide full SQL answers."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)