from typing import Literal

from pydantic import BaseModel


class RouterDecision(BaseModel):
    """Structured output for the router's intent classification."""

    intent: Literal["retrieval", "sql", "calculation", "out_of_scope"]
    reason: str = ""


class SqlPlan(BaseModel):
    """Structured output for the SQL agent's generated query."""

    sql: str
    explanation: str = ""


class SufficiencyCheck(BaseModel):
    """Structured output for the reflect step."""

    is_sufficient: bool
    reason: str = ""
