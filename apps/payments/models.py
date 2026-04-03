"""
Payments app: Gateway, GatewayCurrency, Deposit.
"""
from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.urls import path, include
from rest_framework.routers import DefaultRouter
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
            "final_amount", "trx", "status", "admin_feedback", "created_at",
        ]
        read_only_fields = ["id", "charge", "final_amount", "trx", "status", "created_at"]


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
        import secrets
        currency = validated_data["currency_obj"]
        amount = validated_data["amount"]
        charge = currency.fixed_charge + (amount * currency.percent_charge / 100)
        final_amount = amount - charge
        return Deposit.objects.create(
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
        return created_response(DepositSerializer(deposit).data, "Deposit initiated.")

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
        return success_response(message="Deposit approved and balance updated.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def reject(self, request, pk=None):
        deposit = self.get_object()
        deposit.status = Deposit.Status.CANCELLED
        deposit.admin_feedback = request.data.get("feedback", "")
        deposit.save()
        return success_response(message="Deposit rejected.")


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
    search_fields = ["user__email", "trx"]
    readonly_fields = ["created_at", "trx"]
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
