from django.conf import settings
from langgraph.graph import END, StateGraph

from . import guardrails
from .reflect import reflect_node
from .retrieval_agent import retrieval_agent_node
from .router import OUT_OF_SCOPE_ANSWER, router_node
from .sql_agent import sql_agent_node
from .state import GraphState


def guardrail_input_node(state):
    """Checks 1 (question length) and 2 (cheap topic-scope denylist) — both run
    before any LLM call."""
    question = state["question"]

    length_check = guardrails.check_question_length(question, settings.AGENT_MAX_QUESTION_LENGTH)
    if not length_check.ok: # if question failed the length check
        return { # return reason for rejection
            "guardrail_violation": length_check.reason,
            "answer": length_check.reason,
            "sources": [],
            "agent_used": "none",
        }

    scope_check = guardrails.check_topic_scope_cheap(question)
    if not scope_check.ok: # if questions passes the length check but is not in the scope of the LLM's knowledge
        return { # return reason for rejection
            "guardrail_violation": scope_check.reason,
            "answer": OUT_OF_SCOPE_ANSWER,
            "sources": [],
            "agent_used": "none",
        }

    return {}


def finalize_node(state):
    """Check 7 (answer length cap) — the last stop before returning."""
    # get answer from state and make answer is not larger than max length
    # prevent really long responses
    answer = guardrails.truncate_answer(state.get("answer", ""), settings.AGENT_MAX_ANSWER_LENGTH)
    return {"answer": answer}


def route_from_guardrail(state):
    # finalize if there are no violations
    return "finalize" if state.get("guardrail_violation") else "router"


def route_from_router(state):
    # if out of scope, end
    # if sql, sql agent handles it
    return {"out_of_scope": "finalize", "sql": "sql_agent"}.get(
        state["execution_path"], "retrieval_agent"
    )


def route_after_reflect(state):
    # if the answer is sufficient or the if the answer has been given before
    if state.get("is_sufficient") or state.get("attempt", 0) >= 1:
        return "finalize"
    # if not, sends question back to the right agent (either sql or retrival)
    return "sql_agent" if state["execution_path"] == "sql" else "retrieval_agent"


def build_graph():
    g = StateGraph(GraphState)
    g.add_node("guardrail_input", guardrail_input_node)
    g.add_node("router", router_node)
    g.add_node("retrieval_agent", retrieval_agent_node)
    g.add_node("sql_agent", sql_agent_node)
    g.add_node("reflect", reflect_node)
    g.add_node("finalize", finalize_node)

    # staring point of the graph
    g.set_entry_point("guardrail_input")
    # where to go from guardrail (either finalize or route)
    g.add_conditional_edges(
        "guardrail_input", route_from_guardrail, {"finalize": "finalize", "router": "router"}
    )
    # from route, either finalize or send to either SQL agent or retrieval agent
    g.add_conditional_edges(
        "router",
        route_from_router,
        {"finalize": "finalize", "sql_agent": "sql_agent", "retrieval_agent": "retrieval_agent"},
    )

    g.add_edge("retrieval_agent", "reflect")
    g.add_edge("sql_agent", "reflect")
    # finalize if answer is sufficient or has been given, or return to agents
    g.add_conditional_edges(
        "reflect",
        route_after_reflect,
        {"finalize": "finalize", "retrieval_agent": "retrieval_agent", "sql_agent": "sql_agent"},
    )
    g.add_edge("finalize", END)
    return g.compile()  # no checkpointer — single synchronous invoke() per request


_GRAPH = None


def get_graph():
    global _GRAPH
    # if the graphs exists, return it; if not build a new graph
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def run(question, conversation=None):
    """Run the full router graph for one question.

    Returns (answer_text, sources, agent_used).
    """
    state = get_graph().invoke({"question": question, "conversation": conversation, "attempt": 0})
    return state.get("answer", ""), state.get("sources", []), state.get("agent_used", "none")
