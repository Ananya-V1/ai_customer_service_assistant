from unittest.mock import patch

from django.test import TestCase


class ChatViewTests(TestCase):
    def test_retrieval_routed_response_shape(self):
        with patch(
            "kb.views.run_agent_graph",
            return_value=(
                "Refunds are issued within 14 days.",
                [{"knowledge_base": "Billing", "document": "Refund Policy.pdf", "chunk_id": 1}],
                "retrieval",
            ),
        ):
            response = self.client.post(
                "/api/chat/", {"message": "refund policy?"}, content_type="application/json"
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("conversation_id", data)
        self.assertEqual(data["answer"], "Refunds are issued within 14 days.")
        self.assertEqual(data["agent_used"], "retrieval")
        self.assertTrue(data["sources"])

    def test_sql_routed_response_shape(self):
        with patch(
            "kb.views.run_agent_graph",
            return_value=("There are 3 pending orders.", [], "sql"),
        ):
            response = self.client.post(
                "/api/chat/", {"message": "how many pending orders?"}, content_type="application/json"
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent_used"], "sql")
        self.assertEqual(data["sources"], [])
