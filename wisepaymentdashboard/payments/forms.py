import re
from decimal import Decimal

from django import forms

from payments.services import RECEIVE_CURRENCY, SOURCE_CURRENCY


class BootstrapForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            is_select = isinstance(field.widget, forms.Select)
            field.widget.attrs.setdefault("class", "form-select" if is_select else "form-control")


class AmountForm(BootstrapForm):
    amount = forms.DecimalField(
        label=f"You send ({SOURCE_CURRENCY})", min_value=Decimal("0.01"), max_digits=12, decimal_places=2
    )
    reference = forms.CharField(
        max_length=18, initial="Test payment", help_text="Shown to the recipient. Up to 18 characters."
    )


class RecipientForm(BootstrapForm):
    recipient_id = forms.TypedChoiceField(label="Existing recipient", coerce=int, required=False, empty_value=None)
    account_holder_name = forms.CharField(label="Full name", max_length=200, required=False)
    iban = forms.CharField(label="IBAN", max_length=42, required=False)

    def __init__(self, *args, recipients=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipient_id"].choices = [("", "— Add a new recipient below —")] + [
            (recipient.id, f"{recipient.name} · {recipient.account}") for recipient in recipients
        ]

    def clean_iban(self):
        iban = self.cleaned_data["iban"].replace(" ", "").upper()
        if iban and not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", iban):
            raise forms.ValidationError("This does not look like an IBAN, e.g. DE89370400440532013000.")
        return iban

    def clean(self):
        data = super().clean()
        is_new = data.get("account_holder_name") and data.get("iban")
        if not data.get("recipient_id") and not is_new:
            raise forms.ValidationError("Pick an existing recipient, or enter a full name and an IBAN.")
        return data


class TopUpForm(forms.Form):
    balance_id = forms.IntegerField(widget=forms.HiddenInput)
    currency = forms.CharField(max_length=3, widget=forms.HiddenInput)
    amount = forms.DecimalField(min_value=Decimal("1"), max_digits=12, decimal_places=2, initial=1000)


class ReceiveForm(BootstrapForm):
    amount = forms.DecimalField(
        label=f"Amount ({RECEIVE_CURRENCY})",
        min_value=Decimal("2.00"),
        max_digits=10,
        decimal_places=2,
        help_text="Stripe's minimum for MYR is 2.00.",
    )
    description = forms.CharField(max_length=200, initial="Test order", help_text="Shown on the Stripe payment page.")
    customer_email = forms.EmailField(required=False, help_text="Optional. Stripe fills it in on the payment page.")
