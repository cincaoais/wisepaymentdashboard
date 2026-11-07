from django.contrib import admin

from payments.models import ApiCall, Payment, StatusChange, Transfer


class StatusChangeInline(admin.TabularInline):
    model = StatusChange
    extra = 0
    readonly_fields = ["status", "source", "created_at"]


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = [
        "reference_code",
        "created_at",
        "source_amount",
        "source_currency",
        "target_amount",
        "target_currency",
        "recipient_name",
        "status",
        "external_id",
    ]
    list_filter = ["provider", "status"]
    readonly_fields = ["customer_transaction_id"]
    inlines = [StatusChangeInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["reference_code", "created_at", "amount", "currency", "description", "status", "payment_status"]
    list_filter = ["provider", "status", "payment_status"]
    readonly_fields = ["idempotency_key"]


@admin.register(ApiCall)
class ApiCallAdmin(admin.ModelAdmin):
    list_display = ["created_at", "provider", "method", "path", "status_code", "duration_ms", "error", "transfer", "payment"]
    list_filter = ["provider", "method", "status_code"]
