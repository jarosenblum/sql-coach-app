from __future__ import annotations

from app.question_bank import QUESTION_BANK


def concept_intro_prompt(question_id: str) -> str:
    q = QUESTION_BANK[question_id]
    concept = q["concept"]
    task = q["task"]
    thinking = "\n".join(f"- {x}" for x in q["expected_thinking"])
    teaching_focus = q.get("teaching_focus", "")
    common_mistake = q.get("common_mistake", "")

    def strip_markdown_sql(text: str) -> str:
        return (
            (text or "")
            .replace("```sql", "")
            .replace("```", "")
            .replace("`", "")
            .strip()
        )

    syntax_pattern = strip_markdown_sql(q.get("syntax_pattern", ""))
    what_changes = q.get("what_changes_from_previous", "")

    return f"""You are introducing ONLY the concept for the current SQL question.

Question ID: {question_id}
Concept: {concept}
Task: {task}

Teaching focus:
{teaching_focus}

Expected thinking:
{thinking}

What changes from the previous question:
{what_changes}

Common mistake to avoid:
{common_mistake}

Reference syntax pattern:
{syntax_pattern}

Rules:
- Teach ONLY the concept required for this question.
- Do NOT mention future SQL concepts unless they are explicitly part of this question.
- Do NOT give the full SQL answer.
- Keep the explanation instructional, clear, and moderately detailed.
- Use the reference syntax pattern only as teaching support, not as the final solution.
- Preserve the abstraction level of the reference syntax pattern.
- If the reference syntax pattern contains placeholders, blanks, bracketed labels, abstract slot markers, or partial structure, keep them abstract.
- Do NOT replace placeholders with the actual table name, column name, condition, value, join key, or full solved clause unless that detail is already explicitly present in the reference syntax pattern by design.
- The Assignment Instructions must clearly tell the student exactly what query to write.
- The Assignment Instructions must begin with: "Write a SQL query that..."

Return exactly in this format:
1. Explanation of the concept
2. Assignment Instructions
3. Simple syntax pattern
4. One key thing to notice
5. A useful tip for this question

Formatting rules:
- Use exactly those five section titles.
- Do NOT add sections such as Query Blueprint, Clause Guide, SQL Scaffold with Blanks, or Simple Example.
- Do NOT use markdown headings like ###.
- Do NOT use code fences.
- If you show SQL-like text, present it as plain text only.
"""

def evaluation_prompt(
    question_id: str,
    sql_query: str,
    sandbox_result: str,
    explanation: str,
    computed_result: dict,
    validation_result: dict,
) -> str:
    q = QUESTION_BANK[question_id]
    task = q["task"]
    concept = q["concept"]
    teaching_focus = q.get("teaching_focus", "")
    common_mistake = q.get("common_mistake", "")
    allowed_feedback_scope = ", ".join(q.get("allowed_feedback_scope", []))
    what_changes = q.get("what_changes_from_previous", "")

    computed_columns = computed_result.get("columns", [])
    computed_row_count = computed_result.get("row_count", 0)
    computed_sample_rows = computed_result.get("sample_rows", [])
    computed_error = computed_result.get("error")
    result_matches_task = validation_result.get("result_matches_task", False)
    result_note = validation_result.get("result_note", "")

    return f"""You are evaluating ONE SQL assignment question.

Question ID: {question_id}
Current concept: {concept}
Task: {task}

Teaching focus:
{teaching_focus}

What changes from the previous question:
{what_changes}

Common mistake to watch for:
{common_mistake}

Allowed feedback scope for this question only:
{allowed_feedback_scope}

Student SQL:
{sql_query}

Student-reported W3Schools result:
{sandbox_result}

Computed query execution result:
- executed successfully: {computed_error is None}
- columns returned: {computed_columns}
- row count: {computed_row_count}
- sample rows: {computed_sample_rows}
- execution error: {computed_error}

Deterministic validation:
- result_matches_task: {result_matches_task}
- result_note: {result_note}

Student explanation:
{explanation}

Explanation scoring rubric:
- 2 = The explanation is correct and sufficiently explains what the query does for THIS question, even if it is concise or not highly detailed.
- 1 = The explanation is partially correct, noticeably vague in a way that misses an important idea, or incomplete enough to weaken understanding of how the query works.
- 0 = The explanation is incorrect, off-topic, or shows misunderstanding of the SQL concept for THIS question.

Important explanation scoring rules:
- Do NOT lower the explanation score simply because the explanation could be more detailed, more polished, or more precise.
- Concise but correct explanations should usually receive 2.
- Evaluate only whether the student demonstrates correct understanding for THIS question, not whether the explanation is exhaustive or expert-level.
- Do NOT treat minor lack of elaboration as a reason to assign 1 instead of 2.
- If the student correctly explains the purpose of the SQL clauses used in the current question, assign explanation_score = 2.

Explanation note rules:
- When explanation_score = 2, the explanation_note may mention a small possible improvement, but it must clearly state that the explanation is correct and sufficient.
- When explanation_score = 1, the explanation_note must identify a real missing idea, conceptual weakness, or meaningful vagueness; do NOT say only that it could be more detailed.
- When explanation_score = 0, the explanation_note must clearly identify the misunderstanding or error.

Evaluation rules:
- Evaluate ONLY this question.
- Use the computed query result and deterministic validation as the main source of truth for SQL correctness.
- Treat the student-reported W3Schools result as observational evidence, not as the primary source of truth.
- If the computed query result does not match the task, do not mark the SQL as correct.
- If the explanation is correct and matches the query behavior for THIS question, assign explanation_score = 2.
- Do NOT reference future questions.
- Do NOT provide a full SQL solution.
- If the SQL is correct but the explanation is weak, say so without changing the SQL guidance.
- If you mention any SQL from the student, reproduce it as plain text only — never wrap it in backticks, code fences, or markdown.
- correctness_score must align with result_matches_task: true → 2, false → 0 or 1 depending on severity.
- correctness_score must align with result_matches_task: true → 2, false → 0 or 1 depending on severity.

Return valid JSON with exactly these keys:
- correctness_score: 0, 1, or 2
- correctness_note: concise note about correctness for THIS question only
- explanation_score: 0, 1, or 2
- explanation_note: concise note about explanation quality for THIS question only
- error_type: short machine-friendly label
- concept_to_reinforce: the single concept to reinforce for THIS question only
- should_advance: true or false
- feedback_to_student: brief but pedagogically useful tutoring feedback for THIS question only, no full answer, no future-question guidance

STRICT FORMAT REQUIREMENTS:
- Output must be valid JSON only.
- Do NOT use markdown.
- Do NOT use backticks (`).
- Do NOT use code fences (```).
- If you mention SQL, it must appear as plain text only.
- Your output will be parsed by a machine. Any markdown formatting will cause failure.

Formatting example:
BAD: `SELECT * FROM Customers;`
GOOD: SELECT * FROM Customers;
"""