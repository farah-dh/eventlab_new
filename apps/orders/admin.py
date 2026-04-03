from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Order, Transaction, WithdrawMethod, Withdrawal


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    list_display = ["id", "event", "user", "quantity", "total_price", "payment_status", "status", "created_at"]
    list_filter = ["payment_status", "status"]
    search_fields = ["user__email", "event__title"]
    readonly_fields = ["created_at", "updated_at", "total_price"]
    ordering = ["-created_at"]

    actions = ["mark_as_paid"]

    def mark_as_paid(self, request, queryset):
        queryset.update(payment_status=Order.PaymentStatus.PAID)
    mark_as_paid.short_description = "Mark selected orders as paid"


@admin.register(Transaction)
class TransactionAdmin(ImportExportModelAdmin):
    list_display = ["trx", "user", "organizer", "trx_type", "amount", "charge", "post_balance", "remark", "created_at"]
    list_filter = ["trx_type", "remark"]
    search_fields = ["trx", "user__email", "details"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]


@admin.register(WithdrawMethod)
class WithdrawMethodAdmin(admin.ModelAdmin):
    list_display = ["name", "currency", "min_limit", "max_limit", "fixed_charge", "percent_charge", "status"]
    list_filter = ["status"]
    list_editable = ["status"]


@admin.register(Withdrawal)
class WithdrawalAdmin(ImportExportModelAdmin):
    list_display = ["id", "user", "method", "amount", "charge", "final_amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "trx"]
    readonly_fields = ["created_at", "updated_at", "trx"]
    ordering = ["-created_at"]

    actions = ["approve_withdrawals", "reject_withdrawals"]

    def approve_withdrawals(self, request, queryset):
        for w in queryset.filter(status=Withdrawal.Status.PENDING):
            w.status = Withdrawal.Status.SUCCESS
            w.save()
            if w.user:
                w.user.balance -= w.amount
                w.user.save(update_fields=["balance"])
        self.message_user(request, "Selected withdrawals approved.")
    approve_withdrawals.short_description = "Approve selected withdrawals"

    def reject_withdrawals(self, request, queryset):
        queryset.filter(status=Withdrawal.Status.PENDING).update(status=Withdrawal.Status.CANCELLED)
        self.message_user(request, "Selected withdrawals rejected.")
    reject_withdrawals.short_description = "Reject selected withdrawals"
