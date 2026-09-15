import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from kb.models import Order

CUSTOMER_NAMES = [
    "Ava Thompson", "Liam Chen", "Sofia Ramirez", "Noah Patel", "Emma Johnson",
    "Oliver Kim", "Mia Rodriguez", "Lucas Nguyen", "Isabella Smith", "Ethan Brown",
    "Amelia Davis", "Mason Garcia", "Charlotte Wilson", "Logan Martinez", "Harper Lee",
    "James Anderson", "Evelyn Taylor", "Benjamin White", "Abigail Clark", "Henry Lewis",
]

PRODUCT_NAMES = [
    "Wireless Earbuds", "Standing Desk", "Espresso Machine", "Running Shoes",
    "Backpack", "Bluetooth Speaker", "Yoga Mat", "Air Fryer", "Desk Lamp",
    "Water Bottle", "Office Chair", "Laptop Stand", "Noise-Cancelling Headphones",
    "Electric Kettle", "Fitness Tracker",
]

# Weighted so "delivered" is the most common outcome, refunded/cancelled rarer.
STATUS_WEIGHTS = [
    (Order.STATUS_PENDING, 15),
    (Order.STATUS_SHIPPED, 20),
    (Order.STATUS_DELIVERED, 50),
    (Order.STATUS_REFUNDED, 8),
    (Order.STATUS_CANCELLED, 7),
]


class Command(BaseCommand):
    help = "Seed demo Order rows for the SQL agent."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=200)
        parser.add_argument("--flush", action="store_true", help="Delete existing orders first.")

    def handle(self, *args, **options):
        if options["flush"]:
            deleted, _ = Order.objects.all().delete()
            self.stdout.write(f"Deleted {deleted} existing order(s).")
        elif Order.objects.exists():
            self.stdout.write("Orders already seeded, skipping (use --flush to reseed).")
            return

        rng = random.Random(42)  # fixed seed: reproducible demo data
        statuses = [s for s, _ in STATUS_WEIGHTS]
        weights = [w for _, w in STATUS_WEIGHTS]
        today = date.today()

        orders = []
        for _ in range(options["count"]):
            orders.append(
                Order(
                    customer_name=rng.choice(CUSTOMER_NAMES),
                    product_name=rng.choice(PRODUCT_NAMES),
                    status=rng.choices(statuses, weights=weights, k=1)[0],
                    order_date=today - timedelta(days=rng.randint(0, 365)),
                    amount=round(rng.uniform(9.99, 999.99), 2),
                )
            )
        Order.objects.bulk_create(orders)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(orders)} order(s)."))
