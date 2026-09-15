from unittest.mock import patch

from django.test import SimpleTestCase

from kb.agents.reflect import reflect_node
from kb.agents.schemas import SufficiencyCheck
from kb.services.ollama_client import OllamaError


class ReflectNodeTests(SimpleTestCase):
    def test_sufficient_answer(self):
        with patch(
            "kb.agents.reflect.call_structured",
            return_value=SufficiencyCheck(is_sufficient=True, reason="looks good"),
        ) as mocked:
            result = reflect_node(
                {"question": "q", "answer": "a", "execution_path": "retrieval", "sources": [{"x": 1}]}
            )
        mocked.assert_called_once()
        self.assertTrue(result["is_sufficient"])

    def test_insufficient_answer(self):
        with patch(
            "kb.agents.reflect.call_structured",
            return_value=SufficiencyCheck(is_sufficient=False, reason="off topic"),
        ):
            result = reflect_node({"question": "q", "answer": "a", "execution_path": "sql", "sources": []})
        self.assertFalse(result["is_sufficient"])

    def test_sql_blocked_short_circuits_without_llm_call(self):
        with patch("kb.agents.reflect.call_structured") as mocked:
            result = reflect_node(
                {
                    "question": "q",
                    "sql_blocked": True,
                    "guardrail_violation": "nope",
                    "execution_path": "sql",
                }
            )
        mocked.assert_not_called()
        self.assertFalse(result["is_sufficient"])
        self.assertEqual(result["reflect_reason"], "nope")

    def test_empty_retrieval_sources_short_circuits_without_llm_call(self):
        with patch("kb.agents.reflect.call_structured") as mocked:
            result = reflect_node(
                {"question": "q", "answer": "a", "execution_path": "retrieval", "sources": []}
            )
        mocked.assert_not_called()
        self.assertFalse(result["is_sufficient"])

    def test_fails_open_when_reflect_llm_call_fails(self):
        with patch("kb.agents.reflect.call_structured", side_effect=OllamaError("boom")):
            result = reflect_node({"question": "q", "answer": "a", "execution_path": "sql", "sources": []})
        self.assertTrue(result["is_sufficient"])
