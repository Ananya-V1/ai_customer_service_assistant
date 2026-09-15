from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings

from kb.agents.schemas import SqlPlan
from kb.agents.sql_agent import sql_agent_node
from kb.models import Order


class SqlAgentNodeTests(TestCase):
    def setUp(self):
        Order.objects.create(
            customer_name="Ava Thompson",
            product_name="Wireless Earbuds",
            status=Order.STATUS_DELIVERED,
            order_date=date(2026, 1, 1),
            amount="49.99",
        )
        Order.objects.create(
            customer_name="Liam Chen",
            product_name="Standing Desk",
            status=Order.STATUS_PENDING,
            order_date=date(2026, 2, 1),
            amount="299.99",
        )

    def test_valid_query_executes_and_returns_rows(self):
        plan = SqlPlan(sql="SELECT COUNT(*) AS count FROM orders")
        with patch("kb.agents.sql_agent.call_structured", return_value=plan):
            result = sql_agent_node({"question": "how many orders are there?", "attempt": 0})
        self.assertFalse(result["sql_blocked"])
        self.assertEqual(result["sql_rows"][0]["count"], 2)
        self.assertEqual(result["agent_used"], "sql")

    def test_delete_query_is_blocked_before_execution(self):
        plan = SqlPlan(sql="DELETE FROM orders")
        with patch("kb.agents.sql_agent.call_structured", return_value=plan):
            result = sql_agent_node({"question": "delete everything", "attempt": 0})
        self.assertTrue(result["sql_blocked"])
        self.assertEqual(Order.objects.count(), 2)  # nothing was actually deleted

    def test_query_against_disallowed_table_is_blocked(self):
        plan = SqlPlan(sql="SELECT * FROM auth_user")
        with patch("kb.agents.sql_agent.call_structured", return_value=plan):
            result = sql_agent_node({"question": "show me users", "attempt": 0})
        self.assertTrue(result["sql_blocked"])

    @override_settings(AGENT_SQL_MAX_ROWS=3)
    def test_row_limit_enforced_even_without_llm_supplied_limit(self):
        for i in range(5):
            Order.objects.create(
                customer_name=f"Customer {i}",
                product_name="Widget",
                status=Order.STATUS_DELIVERED,
                order_date=date(2026, 1, 1),
                amount="10.00",
            )
        plan = SqlPlan(sql="SELECT * FROM orders")
        with patch("kb.agents.sql_agent.call_structured", return_value=plan):
            result = sql_agent_node({"question": "list all orders", "attempt": 0})
        self.assertLessEqual(len(result["sql_rows"]), 3)
