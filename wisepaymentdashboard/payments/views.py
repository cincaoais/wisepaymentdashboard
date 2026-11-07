"""Dashboard pages. Each view is a thin layer over `payments.services`."""

import json
import uuid
from dataclasses import asdict

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from payments import services
from payments.forms import AmountForm, ReceiveForm, RecipientForm, TopUpForm
from payments.models import ApiCall, Payment, Provider, Transfer
from payments.providers.stripe import StripeError
from payments.providers.wise import WiseError
from payments.services import PaymentError, Recipient
from payments.statuses import STATUS_GROUPS

# Session key holding the send-money wizard's progress between steps.
WIZARD_KEY = "send_money"


def overview(request):
    context = {"recent_transfers": Transfer.objects.all()[:5], "counts": Transfer.objects.count_by_group()}
    try:
        profile = services.get_business_profile()
        context["profile"] = profile
        context["profile_name"] = profile.get("businessName") or profile.get("fullName", "")
        context["profiles"] = services.list_profiles()
        context["balances"] = services.list_balances()
    except (WiseError, PaymentError) as error:
        context["connection_error"] = error
    context["has_source_balance"] = any(
        balance["currency"] == services.SOURCE_CURRENCY for balance in context.get("balances", [])
    )

    context["recent_payments"] = Payment.objects.all()[:5]
    try:
        context["stripe_balance"] = services.get_stripe_balance()
    except StripeError as error:
        context["stripe_error"] = error
    return render(request, "payments/overview.html", context)


@require_POST
def create_balance(request):
    try:
        services.create_balance(services.SOURCE_CURRENCY)
    except (WiseError, PaymentError) as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"{services.SOURCE_CURRENCY} balance opened.")
    return redirect("payments:overview")


@require_POST
def top_up(request):
    form = TopUpForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter a top-up amount of at least 1.")
        return redirect("payments:overview")
    data = form.cleaned_data
    try:
        services.top_up_balance(data["balance_id"], data["currency"], data["amount"])
    except (WiseError, PaymentError) as error:
        messages.error(request, str(error))
    else:
        messages.success(request, f"Added {data['amount']} {data['currency']} (sandbox money).")
    return redirect("payments:overview")


# Send money wizard: amount → recipient → review


def send_amount(request):
    form = AmountForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            quote = services.create_quote(form.cleaned_data["amount"])
        except (WiseError, PaymentError) as error:
            messages.error(request, str(error))
        else:
            request.session[WIZARD_KEY] = {
                "quote_id": quote.id,
                "reference": form.cleaned_data["reference"],
                "customer_transaction_id": str(uuid.uuid4()),
            }
            return redirect("payments:send_recipient")
    return render(request, "payments/send_amount.html", {"form": form, "step": 1})


def send_recipient(request):
    wizard = request.session.get(WIZARD_KEY)
    if not wizard:
        return redirect("payments:send_amount")

    try:
        recipients = services.list_recipients()
    except (WiseError, PaymentError) as error:
        messages.error(request, str(error))
        recipients = []
    form = RecipientForm(request.POST or None, recipients=recipients)

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            if data["recipient_id"]:
                recipient = next(item for item in recipients if item.id == data["recipient_id"])
            else:
                recipient = services.create_recipient(data["account_holder_name"], data["iban"])
            services.update_quote_recipient(wizard["quote_id"], recipient.id)
        except WiseError as error:
            add_wise_errors(form, error)
        except PaymentError as error:
            messages.error(request, str(error))
        else:
            request.session[WIZARD_KEY] = {**wizard, "recipient": asdict(recipient)}
            return redirect("payments:send_review")

    requirements = None
    if request.method == "GET":
        try:
            requirements = json.dumps(services.get_account_requirements(wizard["quote_id"]), indent=2, default=str)
        except WiseError as error:
            requirements = f"Could not load requirements: {error}"
    context = {"form": form, "requirements": requirements, "step": 2}
    return render(request, "payments/send_recipient.html", context)


def send_review(request):
    wizard = request.session.get(WIZARD_KEY)
    if not wizard or "recipient" not in wizard:
        return redirect("payments:send_amount")
    recipient = Recipient(**wizard["recipient"])

    if request.method == "POST":
        try:
            transfer = services.create_transfer(
                request.user, wizard["customer_transaction_id"], wizard["quote_id"], recipient, wizard["reference"]
            )
        except (WiseError, PaymentError) as error:
            messages.error(request, str(error))
        else:
            del request.session[WIZARD_KEY]
            try:
                if not transfer.is_submitted:
                    services.submit_transfer(transfer)
            except (WiseError, PaymentError) as error:
                messages.error(request, f"{error} The transfer is saved here: press Retry to send it again safely.")
            else:
                messages.success(request, "Transfer created. Fund it to send the money.")
            return redirect("payments:transfer_detail", pk=transfer.pk)

    try:
        quote = services.get_quote(wizard["quote_id"])
    except (WiseError, PaymentError) as error:
        messages.error(request, str(error))
        quote = None
    context = {"quote": quote, "recipient": recipient, "reference": wizard["reference"], "step": 3}
    return render(request, "payments/send_review.html", context)


def add_wise_errors(form, error):
    """Show each Wise validation error next to its field, or at the top of the form."""
    if not error.errors or error.status_code not in (400, 422):
        form.add_error(None, str(error))
        return
    for item in error.errors:
        path = item["path"].lower()
        field = None
        if "iban" in path:
            field = "iban"
        elif "name" in path:
            field = "account_holder_name"
        form.add_error(field, item["message"] or item["code"])


# Transfers


def transfer_list(request):
    group = request.GET.get("group", "")
    transfers = Transfer.objects.select_related("created_by")
    if group in STATUS_GROUPS:
        transfers = transfers.in_group(group)
    context = {"transfers": transfers, "groups": STATUS_GROUPS, "group": group}
    return render(request, "payments/transfer_list.html", context)


def transfer_detail(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk)
    context = {"transfer": transfer, "history": transfer.status_changes.all()}
    return render(request, "payments/transfer_detail.html", context)


TRANSFER_ACTIONS = {
    "submit": (services.submit_transfer, "Transfer sent to Wise."),
    "fund": (services.fund_transfer, "Transfer funded from your balance."),
    "refresh": (services.refresh_transfer, "Status refreshed from Wise."),
    "simulate": (services.simulate_next_status, "Simulation step sent to Wise."),
}


@require_POST
def transfer_action(request, pk, action):
    if action not in TRANSFER_ACTIONS:
        raise Http404
    transfer = get_object_or_404(Transfer, pk=pk)
    run, success_message = TRANSFER_ACTIONS[action]
    try:
        run(transfer)
    except (WiseError, PaymentError) as error:
        messages.error(request, str(error))
    else:
        messages.success(request, success_message)
    return redirect("payments:transfer_detail", pk=transfer.pk)


# Recipients and API log


def recipient_list(request):
    try:
        recipients = services.list_recipients()
    except (WiseError, PaymentError) as error:
        messages.error(request, str(error))
        recipients = []
    context = {"recipients": recipients, "currency": services.TARGET_CURRENCY}
    return render(request, "payments/recipient_list.html", context)


def api_log(request):
    provider = request.GET.get("provider", "")
    calls = ApiCall.objects.select_related("transfer", "payment")
    if provider in Provider.values:
        calls = calls.filter(provider=provider)
    context = {"calls": calls[:200], "providers": Provider.values, "provider": provider}
    return render(request, "payments/api_log.html", context)


# Stripe: receive money


def receive_money(request):
    form = ReceiveForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payment = services.create_payment(request.user, **form.cleaned_data)
        return start_checkout_and_redirect(request, payment)
    return render(request, "payments/receive_money.html", {"form": form})


@require_POST
def payment_start(request, pk):
    return start_checkout_and_redirect(request, get_object_or_404(Payment, pk=pk))


def start_checkout_and_redirect(request, payment):
    """Send the browser to Stripe's payment page, which sends it back to `payment_return`."""
    return_url = request.build_absolute_uri(reverse("payments:payment_return", args=[payment.pk]))
    try:
        services.start_checkout(payment, return_url)
    except (StripeError, PaymentError) as error:
        messages.error(request, f"{error} The payment is saved here: press Retry to try again safely.")
        return redirect("payments:payment_detail", pk=payment.pk)
    return redirect(payment.checkout_url)


def payment_return(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    try:
        services.refresh_payment(payment)
    except (StripeError, PaymentError) as error:
        messages.error(request, str(error))
    else:
        if payment.paid_at:
            messages.success(request, "Payment received.")
        else:
            messages.info(request, "Not paid yet. Open the Stripe payment page again, or press Refresh later.")
    return redirect("payments:payment_detail", pk=payment.pk)


@require_POST
def payment_refresh(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    try:
        services.refresh_payment(payment)
    except (StripeError, PaymentError) as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Status refreshed from Stripe.")
    return redirect("payments:payment_detail", pk=payment.pk)


def payment_list(request):
    payments = Payment.objects.select_related("created_by")
    return render(request, "payments/payment_list.html", {"payments": payments})


def payment_detail(request, pk):
    return render(request, "payments/payment_detail.html", {"payment": get_object_or_404(Payment, pk=pk)})
