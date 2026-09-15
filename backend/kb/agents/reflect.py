from pydantic import ValidationError

from .schemas import SufficiencyCheck
from .structured import call_structured
from ..services.ollama_client import OllamaError

REFLECT_SYSTEM_PROMPT = (
    "You are checking whether an answer actually addresses the user's question. "
    'Respond with ONLY JSON matching: {"is_sufficient": true or false, "reason": "..."}.'
)


def _build_reflect_messages(state):
    return [
        {"role": "system", "content": REFLECT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Question: {state['question']}\n\nAnswer: {state.get('answer', '')}",
        },
    ]


def reflect_node(state):
    # Short-circuit definitionally-insufficient cases without an LLM call.
    if state.get("sql_blocked"):
        return {
            "is_sufficient": False,
            "reflect_reason": state.get("guardrail_violation", "SQL query was rejected."),
        }
    if state.get("execution_path") == "retrieval" and not state.get("sources"):
        return {"is_sufficient": False, "reflect_reason": "No relevant documents found."}

    try:
        check = call_structured(_build_reflect_messages(state), SufficiencyCheck, max_retries=1)
        return {"is_sufficient": check.is_sufficient, "reflect_reason": check.reason}
    except (OllamaError, ValidationError):
        # Fail open: never loop because the judge itself is broken.
        return {
            "is_sufficient": True,
            "reflect_reason": "Reflection check unavailable; accepting best-effort answer.",
        }
