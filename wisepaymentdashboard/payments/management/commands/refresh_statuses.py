from django.core.management.base import BaseCommand

from payments import services
from payments.models import Payment, StatusChange, Transfer
from payments.providers.stripe import StripeError
from payments.providers.wise import WiseError


class Command(BaseCommand):
    help = "Ask Wise and Stripe for the latest status of every transfer and payment that is not finished."

    def handle(self, *args, **options):
        transfers = [transfer for transfer in Transfer.objects.exclude(external_id=None) if not transfer.is_final]
        for transfer in transfers:
            try:
                services.refresh_transfer(transfer, StatusChange.Source.COMMAND)
            except WiseError as error:
                self.stderr.write(f"{transfer}: {error}")
            else:
                self.stdout.write(f"{transfer}: {transfer.status}")

        payments = [payment for payment in Payment.objects.exclude(external_id=None) if not payment.status_info.is_final]
        for payment in payments:
            try:
                services.refresh_payment(payment)
            except StripeError as error:
                self.stderr.write(f"{payment}: {error}")
            else:
                self.stdout.write(f"{payment}: {payment.status} / {payment.payment_status}")

        self.stdout.write(self.style.SUCCESS(f"Checked {len(transfers)} transfer(s) and {len(payments)} payment(s)."))
