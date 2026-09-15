from django.test import SimpleTestCase

from kb.agents import guardrails


class QuestionLengthTests(SimpleTestCase):
    def test_within_limit_passes(self):
        result = guardrails.check_question_length("short question", max_length=100)
        self.assertTrue(result.ok)

    def test_over_limit_fails(self):
        result = guardrails.check_question_length("a" * 101, max_length=100)
        self.assertFalse(result.ok)


class TopicScopeCheapTests(SimpleTestCase):
    def test_relevant_question_passes(self):
        result = guardrails.check_topic_scope_cheap("What's the status of my order?")
        self.assertTrue(result.ok)

    def test_poem_request_fails(self):
        result = guardrails.check_topic_scope_cheap("Write me a poem about the ocean.")
        self.assertFalse(result.ok)

    def test_translation_request_fails(self):
        result = guardrails.check_topic_scope_cheap("Translate this sentence to French.")
        self.assertFalse(result.ok)


class SqlReadOnlyTests(SimpleTestCase):
    def test_select_passes(self):
        result = guardrails.check_sql_is_readonly_select("SELECT * FROM orders WHERE id = 1")
        self.assertTrue(result.ok)

    def test_delete_is_blocked(self):
        result = guardrails.check_sql_is_readonly_select("DELETE FROM orders")
        self.assertFalse(result.ok)

    def test_drop_is_blocked(self):
        result = guardrails.check_sql_is_readonly_select("DROP TABLE orders")
        self.assertFalse(result.ok)

    def test_multiple_statements_blocked(self):
        result = guardrails.check_sql_is_readonly_select("SELECT * FROM orders; DROP TABLE orders;")
        self.assertFalse(result.ok)

    def test_sql_comment_blocked(self):
        result = guardrails.check_sql_is_readonly_select("SELECT * FROM orders -- sneaky comment")
        self.assertFalse(result.ok)

    def test_empty_query_blocked(self):
        result = guardrails.check_sql_is_readonly_select("   ")
        self.assertFalse(result.ok)


class SqlTableAllowlistTests(SimpleTestCase):
    def test_allowed_table_passes(self):
        result = guardrails.check_sql_table_allowlist("SELECT * FROM orders", ["orders"])
        self.assertTrue(result.ok)

    def test_disallowed_table_blocked(self):
        result = guardrails.check_sql_table_allowlist("SELECT * FROM auth_user", ["orders"])
        self.assertFalse(result.ok)

    def test_join_on_disallowed_table_blocked(self):
        result = guardrails.check_sql_table_allowlist(
            "SELECT * FROM orders JOIN auth_user ON orders.id = auth_user.id", ["orders"]
        )
        self.assertFalse(result.ok)

    def test_no_table_reference_passes(self):
        result = guardrails.check_sql_table_allowlist("SELECT 1", ["orders"])
        self.assertTrue(result.ok)


class RowLimitTests(SimpleTestCase):
    def test_appends_limit_when_missing(self):
        sql = guardrails.enforce_row_limit("SELECT * FROM orders", max_rows=50)
        self.assertIn("LIMIT 50", sql)

    def test_replaces_existing_limit(self):
        sql = guardrails.enforce_row_limit("SELECT * FROM orders LIMIT 10000", max_rows=50)
        self.assertIn("LIMIT 50", sql)
        self.assertNotIn("10000", sql)


class AnswerTruncationTests(SimpleTestCase):
    def test_short_answer_unchanged(self):
        self.assertEqual(guardrails.truncate_answer("hello", max_length=100), "hello")

    def test_long_answer_truncated(self):
        result = guardrails.truncate_answer("a" * 200, max_length=100)
        self.assertLessEqual(len(result), 100 + len("... (truncated)"))
        self.assertTrue(result.endswith("... (truncated)"))
