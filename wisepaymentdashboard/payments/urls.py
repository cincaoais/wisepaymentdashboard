from django.urls import path

from payments import views

app_name = "payments"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("balances/create/", views.create_balance, name="create_balance"),
    path("balances/top-up/", views.top_up, name="top_up"),
    path("send/", views.send_amount, name="send_amount"),
    path("send/recipient/", views.send_recipient, name="send_recipient"),
    path("send/review/", views.send_review, name="send_review"),
    path("transfers/", views.transfer_list, name="transfer_list"),
    path("transfers/<int:pk>/", views.transfer_detail, name="transfer_detail"),
    path("transfers/<int:pk>/<slug:action>/", views.transfer_action, name="transfer_action"),
    path("recipients/", views.recipient_list, name="recipient_list"),
    path("receive/", views.receive_money, name="receive_money"),
    path("payments/", views.payment_list, name="payment_list"),
    path("payments/<int:pk>/", views.payment_detail, name="payment_detail"),
    path("payments/<int:pk>/start/", views.payment_start, name="payment_start"),
    path("payments/<int:pk>/return/", views.payment_return, name="payment_return"),
    path("payments/<int:pk>/refresh/", views.payment_refresh, name="payment_refresh"),
    path("api-log/", views.api_log, name="api_log"),
]
