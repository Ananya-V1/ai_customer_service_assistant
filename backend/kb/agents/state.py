from typing import TypedDict


class GraphState(TypedDict, total=False):
    """Shared state threaded through every node in the query-router graph.

    total=False: every key is optional, since different nodes only set the
    keys relevant to the branch they ran on (e.g. sql_query is only set on
    the SQL path).
    """

    question: str
    conversation: object  # a kb.models.Conversation instance, or None

    intent: str  # "retrieval" | "sql" | "calculation" | "out_of_scope"
    execution_path: str  # "retrieval" | "sql" | "out_of_scope"
    attempt: int  # 0 on first pass, 1 on the single allowed retry

    answer: str
    sources: list

    sql_query: str
    sql_rows: list
    sql_blocked: bool

    is_sufficient: bool
    reflect_reason: str

    guardrail_violation: str
    agent_used: str  # "retrieval" | "sql" | "none"
