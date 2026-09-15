from datetime import date
from unittest.mock import patch

from django.test import TestCase

from kb.agents.graph import run as run_agent_graph
from kb.agents.schemas import RouterDecision, SqlPlan, SufficiencyCheck
from kb.models import Document, DocumentChunk, KnowledgeBase, Order
from kb.services import ollama_client

FAKE_EMBEDDING = [1.0] + [0.0] * 767


class GraphEndToEndTests(TestCase):
    def setUp(self):
        kb = KnowledgeBase.objects.create(name="Billing")
        doc = Document.objects.create(knowledge_base=kb, title="Refund Policy.pdf")
        DocumentChunk.objects.create(
            document=doc,
            knowledge_base=kb,
            chunk_index=0,
            text="Refunds are issued within 14 days.",
            embedding=FAKE_EMBEDDING,
        )
        Order.objects.create(
            customer_name="Ava Thompson",
            product_name="Wireless Earbuds",
            status=Order.STATUS_PENDING,
            order_date=date(2026, 1, 1),
            amount="49.99",
        )

    def test_retrieval_question_routes_to_retrieval_agent(self):
        with patch(
            "kb.agents.router.call_structured", return_value=RouterDecision(intent="retrieval")
        ), patch(
            "kb.agents.reflect.call_structured", return_value=SufficiencyCheck(is_sufficient=True)
        ), patch.object(
            ollama_client, "embed", return_value=FAKE_EMBEDDING
        ), patch.object(
            ollama_client, "chat", return_value="Refunds are issued within 14 days."
        ):
            answer, sources, agent_used = run_agent_graph("What's your refund policy?")

        self.assertEqual(agent_used, "retrieval")
        self.assertTrue(sources)

    def test_sql_question_routes_to_sql_agent(self):
        with patch(
            "kb.agents.router.call_structured", return_value=RouterDecision(intent="sql")
        ), patch(
            "kb.agents.sql_agent.call_structured",
            return_value=SqlPlan(sql="SELECT COUNT(*) AS count FROM orders"),
        ), patch(
            "kb.agents.reflect.call_structured", return_value=SufficiencyCheck(is_sufficient=True)
        ):
            answer, sources, agent_used = run_agent_graph("how many orders are pending?")

        self.assertEqual(agent_used, "sql")

    def test_calculation_question_also_routes_to_sql_agent(self):
        with patch(
            "kb.agents.router.call_structured", return_value=RouterDecision(intent="calculation")
        ), patch(
            "kb.agents.sql_agent.call_structured",
            return_value=SqlPlan(sql="SELECT SUM(amount) AS total FROM orders"),
        ), patch(
            "kb.agents.reflect.call_structured", return_value=SufficiencyCheck(is_sufficient=True)
        ):
            answer, sources, agent_used = run_agent_graph("what's the total order amount?")

        self.assertEqual(agent_used, "sql")

    def test_oversized_question_short_circuits_without_any_llm_call(self):
        with patch("kb.agents.router.call_structured") as router_mock, patch.object(
            ollama_client, "embed"
        ) as embed_mock:
            answer, sources, agent_used = run_agent_graph("a" * 5000)
        router_mock.assert_not_called()
        embed_mock.assert_not_called()
        self.assertEqual(agent_used, "none")

    def test_out_of_scope_question_short_circuits_without_any_llm_call(self):
        with patch("kb.agents.router.call_structured") as router_mock, patch.object(
            ollama_client, "embed"
        ) as embed_mock:
            answer, sources, agent_used = run_agent_graph("Write me a poem about the ocean.")
        router_mock.assert_not_called()
        embed_mock.assert_not_called()
        self.assertEqual(agent_used, "none")
