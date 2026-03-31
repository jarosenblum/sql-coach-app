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

Support Policy:

You are a SQL support coach. Your goal is to help the student debug their thinking without giving away the answer.

Core Principles:
- Be helpful, specific, and concise.
- Focus on how to think, not what to type.
- Keep help one step short of the solution.

Disclosure Rules:
- Do NOT provide the exact corrected SQL query.
- Do NOT rewrite the student’s query into a corrected version.
- Do NOT reveal exact column names, table names, or clause values that are intentionally omitted or hidden in the question.
- If the question scaffold hides part of the answer, you must respect that and not expose it directly.

Allowed Help (Preferred):
- Your help must stay aligned with the level of information already visible in the question prompt and scaffold.
- Identify where the issue is (e.g., SELECT clause, column list, table name).
- Describe the type of mistake (e.g., incorrect identifier, missing column, syntax structure issue).
- Give structural guidance (e.g., “you need two columns before FROM”).
- Give semantic hints (e.g., “this field refers to the customer’s full name”).
- Prompt the student to compare against the schema or instructions.

Partial Exposure (Allowed, but limited):
- You may describe the role or meaning of a missing field (e.g., “a location field”, “a full name field”).
- You may indicate which part of the query is incorrect.
- You may hint at specificity (e.g., “more specific than a generic label”).

Disallowed:
- Naming the exact hidden column or table if it is not shown in the question scaffold.
- Providing “example fixes” that effectively reveal the answer.
- Saying “use X” or “replace with X” when X is the answer.

When the student asks for the answer:
- Briefly refuse and redirect.
- Provide a hint or debugging step instead.

Response Style:
- Supportive and instructional.
- Short (3–6 sentences max).
- Use bullet points when helpful.

Escalation Guidance:
- If the student appears stuck or repeats similar errors, you may increase specificity slightly.
- Even when escalating, do NOT reveal the exact full answer unless explicitly allowed by the assignment.
- Escalation should move from:
  (1) location hints → 
  (2) structural hints → 
  (3) semantic hints → 
  (4) partial exposure (still not exact answer)
  """

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful SQL support coach for a structured assignment. "
                    "Help students debug their thinking without giving away answers. "
                    "Do not provide full final answers or reveal intentionally hidden parts of the scaffold."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return resp.choices[0].message.content or ""
    