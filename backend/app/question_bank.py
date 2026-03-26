from __future__ import annotations

QUESTION_BANK = {
    "Q1": {
        "concept": "SELECT",
        "task": "Retrieve all columns and rows from the Customers table.",
        "expected_thinking": [
            "Identify the table: Customers",
            "Use SELECT * to return all columns",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q2": {
        "concept": "Selecting columns",
        "task": "Retrieve CustomerName and City from the Customers table.",
        "expected_thinking": [
            "Replace * with specific columns",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q3": {
        "concept": "WHERE",
        "task": "Retrieve all customers from Germany.",
        "expected_thinking": [
            "Filter rows using Country = 'Germany'",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q4": {
        "concept": "AND / OR",
        "task": "Retrieve all customers from Germany OR France.",
        "expected_thinking": [
            "Combine conditions with OR",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q5": {
        "concept": "ORDER BY",
        "task": "Retrieve all customers and sort them by CustomerName.",
        "expected_thinking": [
            "Sort results using ORDER BY",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q6": {
        "concept": "DISTINCT",
        "task": "Retrieve a list of unique countries from the Customers table.",
        "expected_thinking": [
            "Use DISTINCT to remove duplicates",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q7": {
        "concept": "COUNT",
        "task": "Count the total number of orders in the Orders table.",
        "expected_thinking": [
            "Use COUNT() to aggregate",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q8": {
        "concept": "GROUP BY",
        "task": "Count how many customers are in each country.",
        "expected_thinking": [
            "Use COUNT() and GROUP BY Country",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q9": {
        "concept": "HAVING",
        "task": "Show only countries with more than 5 customers.",
        "expected_thinking": [
            "Use HAVING with COUNT()",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q10": {
        "concept": "JOIN",
        "task": "Retrieve CustomerName and OrderID for all customers and their orders.",
        "expected_thinking": [
            "Join Customers and Orders on CustomerID",
        ],
        "new_concept": True,
        "is_multi_concept": False,
    },
    "Q11": {
        "concept": "JOIN + GROUP BY + COUNT",
        "task": "Determine how many orders each customer has made.",
        "expected_thinking": [
            "Join Customers and Orders",
            "Count orders",
            "Group by customer",
        ],
        "new_concept": True,
        "is_multi_concept": True,
    },
}

QUESTION_ORDER = list(QUESTION_BANK.keys())