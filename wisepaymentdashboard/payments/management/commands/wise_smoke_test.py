import time
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from payments import services
from payments.providers.wise import WiseError
from payments.services import SOURCE_CURRENCY, PaymentError
from payments.statuses import SIMULATION_STEPS

# Wise's own documentation example IBAN.
TEST_IBAN = "DE89370400440532013000"


class Command(BaseCommand):
    help = "Send one test transfer through the whole Wise sandbox flow and print every step."

    def add_arguments(self, parser):
        parser.add_argument("--amount", type=Decimal, default=Decimal("10"), help="GBP to send (default 10).")

    def handle(self, *args, **options):
        if not settings.WISE_IS_SANDBOX:
            raise CommandError("This command only runs against the Wise sandbox.")
        user = get_user_model().objects.filter(is_superuser=True).first()
        if user is None:
            raise CommandError("Create a user first: python manage.py createsuperuser")
        try:
            self.run_flow(user, options["amount"])
        except (WiseError, PaymentError) as error:
            raise CommandError(f"{self.step} failed: {error}") from error
        self.stdout.write(self.style.SUCCESS("The whole flow works. Open the dashboard to see the transfer."))

    def run_flow(self, user, amount):
        self.begin("1. Business profile")
        profile = services.get_business_profile()
        self.done(f"#{profile['id']} ({profile['type']})")

        self.begin(f"2. {SOURCE_CURRENCY} balance")
        balance = self.get_source_balance()
        if balance is None:
            services.create_balance(SOURCE_CURRENCY)
            balance = self.get_source_balance()
        if balance["amount"]["value"] < amount:
            services.top_up_balance(balance["id"], SOURCE_CURRENCY, amount + 1000)
            balance = self.get_source_balance()
        self.done(f"#{balance['id']} holds {balance['amount']['value']} {SOURCE_CURRENCY}")

        self.begin("3. Quote")
        quote = services.create_quote(amount)
        self.done(f"{quote.source_amount} → {quote.target_amount} {quote.target_currency}, rate {quote.rate}")

        self.begin("4. Recipient")
        services.get_account_requirements(quote.id)
        recipient = services.create_recipient("Smoke Test Recipient", TEST_IBAN)
        quote = services.update_quote_recipient(quote.id, recipient.id)
        self.done(f"#{recipient.id} {recipient.account}; recipient gets {quote.target_amount}")

        self.begin("5. Transfer")
        transfer = services.create_transfer(user, uuid.uuid4(), quote.id, recipient, "Smoke test")
        services.submit_transfer(transfer)
        self.done(f"{transfer} is Wise transfer {transfer.external_id}, status {transfer.status}")

        self.begin("6. Fund from balance")
        try:
            services.fund_transfer(transfer)
        except WiseError as error:
            if not error.is_sca_required:
                raise
            raise CommandError(
                f"Wise needs extra approval (SCA) to fund by API. Pay {transfer} (Wise #{transfer.external_id}) "
                f"in the Wise sandbox website, then open /transfers/{transfer.pk}/ in the dashboard, "
                "press Refresh status and use the Simulate button."
            ) from error
        self.done(transfer.status)

        for step in SIMULATION_STEPS[:3]:
            self.begin(f"7. Simulate {step}")
            if transfer.simulated_at:
                time.sleep(6)
            services.simulate_next_status(transfer)
            self.done(transfer.status)

        self.begin("8. Final status from Wise")
        time.sleep(6)
        services.refresh_transfer(transfer)
        self.done(transfer.status)

    def get_source_balance(self):
        return next((item for item in services.list_balances() if item["currency"] == SOURCE_CURRENCY), None)

    def begin(self, step):
        self.step = step
        self.stdout.write(f"{step} ... ", ending="")
        self.stdout.flush()

    def done(self, result):
        self.stdout.write(self.style.SUCCESS(str(result)))
