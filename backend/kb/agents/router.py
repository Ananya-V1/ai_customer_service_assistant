from pydantic import ValidationError

from .schemas import RouterDecision
from .structured import call_structured
from ..services.ollama_client import OllamaError

ROUTER_SYSTEM_PROMPT = (
    "You are a routing classifier for a customer support assistant. Given the "
    "user's question, classify it into exactly one intent:\n"
    '- "retrieval": the question needs looking something up in uploaded documents '
    "(policies, FAQs, product/support documentation).\n"
    '- "sql": the question needs a lookup in structured order data (order status, '
    "a customer's orders, which orders match some criteria).\n"
    '- "calculation": the question needs a calculation or aggregate over the order '
    "data (e.g. totals, averages, counts).\n"
    '- "out_of_scope": the question has nothing to do with customer support, orders, '
    "or the knowledge base (e.g. jokes, poems, general trivia, unrelated requests).\n"
    'Respond with ONLY JSON matching: {"intent": "...", "reason": "..."}.'
)

OUT_OF_SCOPE_ANSWER = "I can only help with questions about your orders or our support documentation."


def router_node(state):
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": state["question"]},
    ]
    try:
        decision = call_structured(messages, RouterDecision, max_retries=1)
        intent = decision.intent
    except (OllamaError, ValidationError):
        intent = "retrieval"  # sensible fallback rather than failing the whole request

    execution_path = "sql" if intent in ("sql", "calculation") else intent

    result = {"intent": intent, "execution_path": execution_path}
    if execution_path == "out_of_scope":
        result.update(answer=OUT_OF_SCOPE_ANSWER, sources=[], agent_used="none")
    return result
