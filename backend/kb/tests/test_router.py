from unittest.mock import patch

from django.test import SimpleTestCase

from kb.agents.router import router_node
from kb.agents.schemas import RouterDecision
from kb.services.ollama_client import OllamaError


class RouterNodeTests(SimpleTestCase):
    def _run(self, decision):
        with patch("kb.agents.router.call_structured", return_value=decision):
            return router_node({"question": "does not matter"})

    def test_retrieval_intent_maps_to_retrieval_path(self):
        result = self._run(RouterDecision(intent="retrieval"))
        self.assertEqual(result["execution_path"], "retrieval")

    def test_sql_intent_maps_to_sql_path(self):
        result = self._run(RouterDecision(intent="sql"))
        self.assertEqual(result["execution_path"], "sql")

    def test_calculation_intent_also_maps_to_sql_path(self):
        result = self._run(RouterDecision(intent="calculation"))
        self.assertEqual(result["execution_path"], "sql")

    def test_out_of_scope_sets_canned_answer(self):
        result = self._run(RouterDecision(intent="out_of_scope"))
        self.assertEqual(result["execution_path"], "out_of_scope")
        self.assertEqual(result["agent_used"], "none")
        self.assertEqual(result["sources"], [])

    def test_falls_back_to_retrieval_when_classification_fails(self):
        with patch("kb.agents.router.call_structured", side_effect=OllamaError("boom")):
            result = router_node({"question": "does not matter"})
        self.assertEqual(result["intent"], "retrieval")
        self.assertEqual(result["execution_path"], "retrieval")
