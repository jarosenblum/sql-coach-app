from __future__ import annotations

from typing import Any


def _normalized_columns(cols: list[str]) -> list[str]:
    return [c.strip().lower() for c in cols]


def validate_result_for_question(question_id: str, sql_result: dict[str, Any]) -> dict[str, Any]:
    executed = bool(sql_result.get("executed"))
    columns = _normalized_columns(sql_result.get("columns", []))
    row_count = int(sql_result.get("row_count", 0))
    error = sql_result.get("error")

    if not executed:
        return {
            "result_matches_task": False,
            "result_note": f"Query did not execute successfully: {error}",
        }

    if question_id == "Q1":
        # Expect all customer columns; row count should be > 0
        required = {"customerid", "customername", "contactname", "address", "city", "postalcode", "country"}
        has_required = required.issubset(set(columns))
        return {
            "result_matches_task": has_required and row_count > 0,
            "result_note": "Query should return all rows and all columns from Customers.",
        }

    if question_id == "Q2":
        expected = {"customername", "city"}
        exact = set(columns) == expected
        return {
            "result_matches_task": exact and row_count > 0,
            "result_note": "Query should return exactly CustomerName and City.",
        }

    if question_id == "Q3":
        return {
            "result_matches_task": row_count > 0,
            "result_note": "Query should return only customers from Germany.",
        }

    if question_id == "Q4":
        return {
            "result_matches_task": row_count > 0,
            "result_note": "Query should return customers from Germany OR France.",
        }

    if question_id == "Q5":
        return {
            "result_matches_task": row_count > 0,
            "result_note": "Query should return customers sorted by CustomerName.",
        }

    if question_id == "Q6":
        return {
            "result_matches_task": "country" in columns and row_count > 0,
            "result_note": "Query should return unique countries only.",
        }

    if question_id == "Q7":
        return {
            "result_matches_task": len(columns) == 1 and row_count == 1,
            "result_note": "Query should return one aggregate count.",
        }

    if question_id == "Q8":
        return {
            "result_matches_task": "country" in columns and row_count > 0,
            "result_note": "Query should return one grouped count per country.",
        }

    if question_id == "Q9":
        return {
            "result_matches_task": "country" in columns and row_count > 0,
            "result_note": "Query should return only grouped countries with count > 5.",
        }

    if question_id == "Q10":
        expected = {"customername", "orderid"}
        return {
            "result_matches_task": expected.issubset(set(columns)) and row_count > 0,
            "result_note": "Query should join Customers and Orders and return CustomerName and OrderID.",
        }

    if question_id == "Q11":
        return {
            "result_matches_task": row_count > 0,
            "result_note": "Query should return each customer with a count of orders.",
        }

    return {
        "result_matches_task": executed,
        "result_note": "No specialized validator available for this question.",
    }