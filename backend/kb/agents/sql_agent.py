from django.conf import settings
from pydantic import ValidationError

from . import guardrails
from .schemas import SqlPlan
from .structured import call_structured
from ..services.ollama_client import OllamaError

SQL_SYSTEM_PROMPT = (
    "You have access to a single table `orders` with columns:\n"
    "  id (integer), customer_name (text), product_name (text),\n"
    "  status (one of: pending, shipped, delivered, refunded, cancelled),\n"
    "  order_date (date), amount (decimal).\n"
    "Given the user's question, respond with ONLY JSON matching: "
    '{"sql": "SELECT ...", "explanation": "..."}.\n'
    "Only ever query the `orders` table with a single read-only SELECT statement. "
    "Never use DELETE, DROP, UPDATE, INSERT, ALTER, or any other statement type."
)

SQL_UNAVAILABLE_ANSWER = "I couldn't generate a query to answer that right now. Please try rephrasing."
SQL_REFUSAL_ANSWER = "I can't run that query — it isn't a safe, read-only lookup against your order data."


def _render_rows_as_text(rows):
    if not rows:
        return "I didn't find any orders matching that."
    if len(rows) == 1 and len(rows[0]) == 1:
        # A single aggregate value, e.g. {"count": 12} or {"sum": Decimal("1234.50")}.
        (value,) = rows[0].values()
        return f"The answer is {value}."
    lines = [", ".join(f"{key}: {val}" for key, val in row.items()) for row in rows[:10]]
    suffix = f"\n(+{len(rows) - 10} more rows)" if len(rows) > 10 else ""
    return f"Found {len(rows)} order(s):\n" + "\n".join(lines) + suffix


def sql_agent_node(state):
    from django.db import connection  # lazy import, matches services/retrieval.py's pattern

    attempt = state.get("attempt", 0)
    messages = [{"role": "system", "content": SQL_SYSTEM_PROMPT}]
    if attempt:
        feedback = state.get("reflect_reason") or state.get("guardrail_violation") or ""
        messages.append(
            {
                "role": "user",
                "content": (
                    f"The previous attempt was rejected or insufficient: {feedback}. "
                    f"Previous SQL: {state.get('sql_query', '')}. "
                    f"Question: {state['question']}. Please try again."
                ),
            }
        )
    else:
        messages.append({"role": "user", "content": state["question"]})

    try:
        plan = call_structured(messages, SqlPlan, max_retries=1)
    except (OllamaError, ValidationError):
        return {
            "sql_blocked": True,
            "answer": SQL_UNAVAILABLE_ANSWER,
            "sources": [],
            "agent_used": "sql",
            "attempt": attempt + 1,
        }

    safety = guardrails.check_sql_is_readonly_select(plan.sql)
    if safety.ok:
        safety = guardrails.check_sql_table_allowlist(plan.sql, settings.AGENT_SQL_ALLOWED_TABLES)

    if not safety.ok:
        return {
            "sql_blocked": True,
            "sql_query": plan.sql,
            "answer": SQL_REFUSAL_ANSWER,
            "sources": [],
            "agent_used": "sql",
            "attempt": attempt + 1,
            "guardrail_violation": safety.reason,
        }

    final_sql = guardrails.enforce_row_limit(plan.sql, settings.AGENT_SQL_MAX_ROWS)
    with connection.cursor() as cursor:
        cursor.execute(final_sql)
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()][: settings.AGENT_SQL_MAX_ROWS]

    return {
        "sql_query": final_sql,
        "sql_rows": rows,
        "answer": _render_rows_as_text(rows),
        "sources": [],
        "agent_used": "sql",
        "attempt": attempt + 1,
        "sql_blocked": False,
    }
