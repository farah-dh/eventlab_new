from django.urls import path
from .models import urlpatterns as router_urls
from .models import StripeWebhookView

urlpatterns = router_urls + [
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
]