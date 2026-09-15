from django.core.management import call_command
from django.test import TestCase

from kb.models import Order


class SeedOrdersCommandTests(TestCase):
    def test_default_count_created(self):
        call_command("seed_orders")
        self.assertEqual(Order.objects.count(), 200)

    def test_custom_count(self):
        call_command("seed_orders", count=10)
        self.assertEqual(Order.objects.count(), 10)

    def test_running_twice_without_flush_does_not_duplicate(self):
        call_command("seed_orders", count=10)
        call_command("seed_orders", count=10)
        self.assertEqual(Order.objects.count(), 10)

    def test_flush_reseeds(self):
        call_command("seed_orders", count=10)
        call_command("seed_orders", count=20, flush=True)
        self.assertEqual(Order.objects.count(), 20)
