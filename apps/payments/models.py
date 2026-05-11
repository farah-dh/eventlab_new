"""
Payments app: Gateway, GatewayCurrency, Deposit.
"""
import secrets
import stripe

from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from apps.core.models import BaseModel
from apps.core.permissions import IsAdmin
from apps.core.responses import success_response, created_response, error_response
from apps.accounts.models import User, Organizer


# ─── Models ──────────────────────────────────────────────────────────────────

class Gateway(BaseModel):
    form_id = models.IntegerField(default=0)
    code = models.IntegerField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=40, blank=True, null=True)
    alias = models.CharField(max_length=40, default="NULL")
    image = models.CharField(max_length=255, blank=True, null=True)
    status = models.SmallIntegerField(default=1, choices=[(1, "Enable"), (2, "Disable")])
    gateway_parameters = models.JSONField(blank=True, null=True)
    supported_currencies = models.JSONField(blank=True, null=True)
    crypto = models.BooleanField(default=False)
    extra = models.JSONField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "gateways"
        verbose_name = "Payment Gateway"

    def __str__(self):
        return self.name or ""


class GatewayCurrency(BaseModel):
    name = models.CharField(max_length=40, blank=True, null=True)
    currency = models.CharField(max_length=40, blank=True, null=True)
    symbol = models.CharField(max_length=40, blank=True, null=True)
    method_code = models.IntegerField(blank=True, null=True)
    gateway_alias = models.CharField(max_length=40, blank=True, null=True)
    min_amount = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    max_amount = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    percent_charge = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fixed_charge = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    rate = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    gateway_parameter = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = "gateway_currencies"
        verbose_name = "Gateway Currency"

    def __str__(self):
        return f"{self.name} ({self.currency})"


class Deposit(BaseModel):
    class Status(models.IntegerChoices):
        PENDING = 2, "Pending"
        SUCCESS = 1, "Success"
        CANCELLED = 3, "Cancelled"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="deposits")
    order_id = models.IntegerField(default=0)
    method_code = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    method_currency = models.CharField(max_length=40, blank=True, null=True)
    charge = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    rate = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    final_amount = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    detail = models.JSONField(blank=True, null=True)
    btc_amount = models.CharField(max_length=255, blank=True, null=True)
    btc_wallet = models.CharField(max_length=255, blank=True, null=True)
    trx = models.CharField(max_length=40, blank=True, null=True)
    payment_try = models.IntegerField(default=0)
    status = models.SmallIntegerField(choices=Status.choices, default=Status.PENDING)
    from_api = models.BooleanField(default=False)
    admin_feedback = models.CharField(max_length=255, blank=True, null=True)
    success_url = models.CharField(max_length=255, blank=True, null=True)
    failed_url = models.CharField(max_length=255, blank=True, null=True)
    last_cron = models.IntegerField(default=0)

    # ── Stripe ────────────────────────────────────────────────────────────────
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_checkout_url = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = "deposits"
        verbose_name = "Deposit"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Deposit #{self.pk} — {self.amount}"


# ─── Serializers ─────────────────────────────────────────────────────────────

class GatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gateway
        fields = ["id", "code", "name", "alias", "image", "status", "crypto", "description"]


class GatewayCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = GatewayCurrency
        fields = "__all__"


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = [
            "id", "method_code", "amount", "method_currency", "charge",
            "final_amount", "trx", "status", "admin_feedback",
            "stripe_checkout_url", "created_at",
        ]
        read_only_fields = ["id", "charge", "final_amount", "trx", "status",
                            "stripe_checkout_url", "created_at"]


class DepositCreateSerializer(serializers.Serializer):
    method_code = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=28, decimal_places=8)
    currency = serializers.CharField(max_length=40)

    def validate(self, data):
        try:
            currency = GatewayCurrency.objects.get(
                method_code=data["method_code"],
                currency=data["currency"],
            )
            if data["amount"] < currency.min_amount:
                raise serializers.ValidationError(f"Minimum deposit is {currency.min_amount}.")
            if currency.max_amount and data["amount"] > currency.max_amount:
                raise serializers.ValidationError(f"Maximum deposit is {currency.max_amount}.")
            data["currency_obj"] = currency
        except GatewayCurrency.DoesNotExist:
            raise serializers.ValidationError("Invalid payment method or currency.")
        return data

    def create(self, validated_data):
        currency = validated_data["currency_obj"]
        amount = validated_data["amount"]
        charge = currency.fixed_charge + (amount * currency.percent_charge / 100)
        final_amount = amount - charge

        # 1. Créer le dépôt en base de données
        deposit = Deposit.objects.create(
            user=self.context["request"].user,
            method_code=validated_data["method_code"],
            amount=amount,
            method_currency=validated_data["currency"],
            charge=charge,
            rate=currency.rate,
            final_amount=final_amount,
            trx=secrets.token_hex(10).upper(),
            status=Deposit.Status.PENDING,
        )

        # 2. Si le gateway est Stripe, créer une session Checkout
        if currency.gateway_alias and "stripe" in currency.gateway_alias.lower():
            stripe.api_key = settings.STRIPE_SECRET_KEY
            frontend_url = settings.FRONTEND_URL

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": validated_data["currency"].lower(),
                        "product_data": {
                            "name": f"Dépôt EventFlow #{deposit.trx}",
                        },
                        "unit_amount": int(float(amount) * 100),
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=f"{frontend_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{frontend_url}/payment/cancel",
                metadata={
                    "deposit_id": str(deposit.id),
                    "deposit_trx": deposit.trx,
                },
            )

            # 3. Sauvegarder l'URL Stripe dans le dépôt
            deposit.stripe_session_id = session.id
            deposit.stripe_checkout_url = session.url
            deposit.save(update_fields=["stripe_session_id", "stripe_checkout_url"])

        return deposit


# ─── Views ───────────────────────────────────────────────────────────────────

class GatewayViewSet(viewsets.ModelViewSet):
    queryset = Gateway.objects.filter(status=1)
    serializer_class = GatewaySerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdmin()]


class DepositViewSet(viewsets.ModelViewSet):
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Deposit.objects.select_related("user").all()
        return Deposit.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return DepositCreateSerializer
        return DepositSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deposit = serializer.save()

        response_data = DepositSerializer(deposit).data

        if deposit.stripe_checkout_url:
            response_data["checkout_url"] = deposit.stripe_checkout_url

        if deposit.user and deposit.user.email:
            send_mail(
                subject='Demande de dépôt reçue',
                message=(
                    f'Bonjour {deposit.user.username},\n\n'
                    f'Votre demande de dépôt de {deposit.amount} a été reçue '
                    f'et est en attente de validation.\n\nMerci.'
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[deposit.user.email],
                fail_silently=False,
            )

        return created_response(response_data, "Deposit initiated.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        deposit = self.get_object()
        if deposit.status != Deposit.Status.PENDING:
            return error_response("Only pending deposits can be approved.")
        deposit.status = Deposit.Status.SUCCESS
        deposit.admin_feedback = request.data.get("feedback", "")
        deposit.save()
        if deposit.user:
            deposit.user.balance += deposit.final_amount
            deposit.user.save(update_fields=["balance"])
            if deposit.user.email:
                send_mail(
                    subject='Dépôt approuvé ✅',
                    message=(
                        f'Bonjour {deposit.user.username},\n\n'
                        f'Votre dépôt de {deposit.final_amount} a été approuvé '
                        f'et ajouté à votre solde.\n\nMerci.'
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[deposit.user.email],
                    fail_silently=False,
                )
        return success_response(message="Deposit approved and balance updated.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def reject(self, request, pk=None):
        deposit = self.get_object()
        deposit.status = Deposit.Status.CANCELLED
        deposit.admin_feedback = request.data.get("feedback", "")
        deposit.save()
        if deposit.user and deposit.user.email:
            send_mail(
                subject='Dépôt refusé ❌',
                message=(
                    f'Bonjour {deposit.user.username},\n\n'
                    f'Votre dépôt a été refusé.\n'
                    f'Raison : {deposit.admin_feedback or "Non spécifiée"}\n\n'
                    f'Contactez le support pour plus d\'informations.'
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[deposit.user.email],
                fail_silently=False,
            )
        return success_response(message="Deposit rejected.")


# ─── Stripe Webhook ──────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """
    Reçoit les événements Stripe et met à jour le statut des dépôts.
    URL : POST /api/v1/payments/stripe/webhook/
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({"error": "Invalid signature"}, status=400)

        # Paiement confirmé par Stripe
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            deposit_id = session.get("metadata", {}).get("deposit_id")
            if deposit_id:
                try:
                    deposit = Deposit.objects.get(id=deposit_id)
                    if deposit.status == Deposit.Status.PENDING:
                        deposit.status = Deposit.Status.SUCCESS
                        deposit.save(update_fields=["status"])
                        if deposit.user:
                            deposit.user.balance += deposit.final_amount
                            deposit.user.save(update_fields=["balance"])
                except Deposit.DoesNotExist:
                    pass

        # Session expirée → annuler le dépôt
        elif event["type"] == "checkout.session.expired":
            session = event["data"]["object"]
            deposit_id = session.get("metadata", {}).get("deposit_id")
            if deposit_id:
                Deposit.objects.filter(
                    id=deposit_id,
                    status=Deposit.Status.PENDING
                ).update(status=Deposit.Status.CANCELLED)

        return Response({"status": "ok"})


# ─── URLs ────────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register("gateways", GatewayViewSet, basename="gateway")
router.register("deposits", DepositViewSet, basename="deposit")
urlpatterns = router.urls


# ─── Admin ───────────────────────────────────────────────────────────────────

@admin.register(Gateway)
class GatewayAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "alias", "crypto", "status"]
    list_filter = ["status", "crypto"]
    search_fields = ["name", "alias"]
    list_editable = ["status"]


@admin.register(GatewayCurrency)
class GatewayCurrencyAdmin(admin.ModelAdmin):
    list_display = ["name", "currency", "symbol", "method_code", "min_amount", "max_amount", "rate"]
    search_fields = ["name", "currency"]


@admin.register(Deposit)
class DepositAdmin(ImportExportModelAdmin):
    list_display = ["id", "user", "amount", "method_currency", "charge", "final_amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "trx", "stripe_session_id"]
    readonly_fields = ["created_at", "trx", "stripe_session_id", "stripe_checkout_url"]
    ordering = ["-created_at"]
    actions = ["approve_deposits"]

    def approve_deposits(self, request, queryset):
        for d in queryset.filter(status=Deposit.Status.PENDING):
            d.status = Deposit.Status.SUCCESS
            d.save()
            if d.user:
                d.user.balance += d.final_amount
                d.user.save(update_fields=["balance"])
    approve_deposits.short_description = "Approve selected deposits"