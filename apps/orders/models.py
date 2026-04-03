"""
Orders app: Order, Transaction, Withdrawal, WithdrawMethod.
"""
from django.db import models
from apps.core.models import BaseModel
from apps.accounts.models import User, Organizer
from apps.events.models import Event


class Order(BaseModel):
    class PaymentStatus(models.IntegerChoices):
        PENDING = 0, "Pending"
        PAID = 1, "Paid"
        FAILED = 2, "Failed"
        REFUNDED = 3, "Refunded"

    class OrderStatus(models.IntegerChoices):
        ACTIVE = 1, "Active"
        CANCELLED = 2, "Cancelled"

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="orders")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    price = models.FloatField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    total_price = models.FloatField(blank=True, null=True)
    details = models.JSONField(blank=True, null=True)
    payment_status = models.SmallIntegerField(choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    status = models.SmallIntegerField(choices=OrderStatus.choices, default=OrderStatus.ACTIVE)

    class Meta:
        db_table = "orders"
        verbose_name = "Order"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "payment_status"])]

    def __str__(self):
        return f"Order #{self.pk} — {self.event.title}"

    def save(self, *args, **kwargs):
        if self.price and self.quantity:
            self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)


class Transaction(BaseModel):
    class TrxType(models.TextChoices):
        CREDIT = "+", "Credit"
        DEBIT = "-", "Debit"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    organizer = models.ForeignKey(Organizer, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    amount = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    charge = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    post_balance = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    trx_type = models.CharField(max_length=40, choices=TrxType.choices)
    trx = models.CharField(max_length=40, blank=True, null=True)
    details = models.CharField(max_length=255, blank=True, null=True)
    remark = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        db_table = "transactions"
        verbose_name = "Transaction"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["trx"])]

    def __str__(self):
        return f"TRX {self.trx} — {self.amount}"


class WithdrawMethod(BaseModel):
    form_id = models.IntegerField(default=0)
    name = models.CharField(max_length=40, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    min_limit = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    max_limit = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    fixed_charge = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    rate = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    percent_charge = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=40, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "withdraw_methods"
        verbose_name = "Withdraw Method"

    def __str__(self):
        return self.name or ""


class Withdrawal(BaseModel):
    class Status(models.IntegerChoices):
        PENDING = 2, "Pending"
        SUCCESS = 1, "Approved"
        CANCELLED = 3, "Rejected"

    method = models.ForeignKey(WithdrawMethod, on_delete=models.PROTECT, related_name="withdrawals")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="withdrawals")
    organizer = models.ForeignKey(Organizer, on_delete=models.SET_NULL, null=True, blank=True, related_name="withdrawals")
    amount = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    currency = models.CharField(max_length=40, blank=True, null=True)
    rate = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    charge = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    trx = models.CharField(max_length=40, blank=True, null=True)
    final_amount = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    after_charge = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    withdraw_information = models.JSONField(blank=True, null=True)
    status = models.SmallIntegerField(choices=Status.choices, default=Status.PENDING)
    admin_feedback = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "withdrawals"
        verbose_name = "Withdrawal"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Withdrawal #{self.pk} — {self.amount}"
