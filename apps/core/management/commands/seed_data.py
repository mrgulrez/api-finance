"""
Management command: seed_data

Creates 3 test users (one per role) and 30 random financial records.

Usage:
    python manage.py seed_data
    python manage.py seed_data --records 50   # custom record count
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.finance.models import FinancialRecord

User = get_user_model()

# ─── Test user definitions ────────────────────────────────────────────────────
SEED_USERS = [
    {
        "email": "viewer@finance.dev",
        "full_name": "Victoria Viewer",
        "password": "Viewer@123",
        "role": "VIEWER",
    },
    {
        "email": "analyst@finance.dev",
        "full_name": "Alex Analyst",
        "password": "Analyst@123",
        "role": "ANALYST",
    },
    {
        "email": "admin@finance.dev",
        "full_name": "Adam Admin",
        "password": "Admin@123",
        "role": "ADMIN",
        "is_staff": True,
    },
]

INCOME_CATEGORIES = ["salary", "freelance", "investment", "bonus", "rental", "dividend"]
EXPENSE_CATEGORIES = ["rent", "groceries", "utilities", "transport", "entertainment", "healthcare"]

DESCRIPTIONS = [
    "Monthly payment",
    "Quarterly settlement",
    "Regular expense",
    "One-time payment",
    "Routine cost",
    "",  # some records have no description
]


class Command(BaseCommand):
    """Populate the database with test users and financial records."""

    help = "Seed the database with 3 test users and financial records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--records",
            type=int,
            default=30,
            help="Number of financial records to create (default: 30).",
        )

    def handle(self, *args, **options):
        record_count: int = options["records"]
        self.stdout.write(self.style.MIGRATE_HEADING("=== Finance Backend Seed ==="))

        # ── Create users ──────────────────────────────────────────────────────
        created_users = []
        for spec in SEED_USERS:
            email = spec["email"]
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": spec["full_name"],
                    "role": spec["role"],
                    "is_staff": spec.get("is_staff", False),
                    "is_active": True,
                },
            )
            if created:
                user.set_password(spec["password"])
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"  + Created {spec['role']} user: {email}")
                )
            else:
                self.stdout.write(f"  - User already exists: {email}")
            created_users.append(user)

        # ── Create financial records ──────────────────────────────────────────
        self.stdout.write(f"\nCreating {record_count} financial records…")
        records = []
        today = date.today()
        analyst_user = next(u for u in created_users if u.role == "ANALYST")
        admin_user = next(u for u in created_users if u.role == "ADMIN")
        owners = [analyst_user, admin_user]  # VIEWER has no records

        for _ in range(record_count):
            tx_type = random.choice(["INCOME", "EXPENSE"])
            owner = random.choice(owners)
            category = random.choice(
                INCOME_CATEGORIES if tx_type == "INCOME" else EXPENSE_CATEGORIES
            )
            amount = Decimal(str(round(random.uniform(50, 5000), 2)))
            days_back = random.randint(0, 365)
            record_date = today - timedelta(days=days_back)

            records.append(
                FinancialRecord(
                    user=owner,
                    amount=amount,
                    transaction_type=tx_type,
                    category=category,
                    date=record_date,
                    description=random.choice(DESCRIPTIONS),
                )
            )

        FinancialRecord.objects.bulk_create(records)
        self.stdout.write(self.style.SUCCESS(f"  + Created {record_count} financial records."))

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write("\n" + self.style.SUCCESS("=== Seed complete! Test credentials ==="))
        for spec in SEED_USERS:
            self.stdout.write(
                f"  [{spec['role']:8s}] {spec['email']}  /  {spec['password']}"
            )
