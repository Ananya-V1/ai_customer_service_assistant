from django.conf import settings

from ..services.retrieval import answer_question


def retrieval_agent_node(state):
    """Wraps the existing RAG pipeline. Widens the search on the retry attempt."""
    attempt = state.get("attempt", 0)
    kwargs = {}
    if attempt:
        kwargs = {
            "top_k": int(round(settings.RAG_TOP_K * settings.AGENT_RETRY_WIDEN_TOP_K_MULTIPLIER)),
            "max_distance": settings.RAG_MAX_DISTANCE * settings.AGENT_RETRY_WIDEN_DISTANCE_MULTIPLIER,
        }

    answer, sources = answer_question(state["question"], state.get("conversation"), **kwargs)
    return {
        "answer": answer,
        "sources": sources,
        "attempt": attempt + 1,
        "agent_used": "retrieval",
    }
