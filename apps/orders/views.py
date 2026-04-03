from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.core.permissions import IsAdmin, IsOwnerOrAdmin
from apps.core.responses import success_response, created_response, error_response
from .models import Order, Transaction, WithdrawMethod, Withdrawal


# ─── Serializers ─────────────────────────────────────────────────────────────

class OrderSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source="event.title", read_only=True)
    event_cover = serializers.CharField(source="event.cover_image", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "event", "event_title", "event_cover", "user",
            "price", "quantity", "total_price", "details",
            "payment_status", "status", "created_at",
        ]
        read_only_fields = ["id", "user", "total_price", "price", "payment_status", "created_at"]


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["event", "quantity", "details"]

    def validate(self, data):
        event = data["event"]
        qty = data.get("quantity", 1)
        if event.is_sold_out:
            raise serializers.ValidationError("This event is sold out.")
        if event.seats and (event.seats - event.seats_booked) < qty:
            raise serializers.ValidationError(f"Only {event.seats - event.seats_booked} seats available.")
        return data

    def create(self, validated_data):
        event = validated_data["event"]
        qty = validated_data.get("quantity", 1)
        order = Order.objects.create(
            user=self.context["request"].user,
            price=event.price or 0,
            **validated_data,
        )
        return order


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "amount", "charge", "post_balance", "trx_type", "trx", "details", "remark", "created_at"]
        read_only_fields = fields


class WithdrawMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawMethod
        fields = [
            "id", "name", "image", "min_limit", "max_limit",
            "fixed_charge", "percent_charge", "currency", "description", "status",
        ]


class WithdrawalSerializer(serializers.ModelSerializer):
    method_name = serializers.CharField(source="method.name", read_only=True)

    class Meta:
        model = Withdrawal
        fields = [
            "id", "method", "method_name", "amount", "currency", "charge",
            "final_amount", "after_charge", "withdraw_information",
            "status", "admin_feedback", "trx", "created_at",
        ]
        read_only_fields = ["id", "charge", "final_amount", "after_charge", "status", "admin_feedback", "trx", "created_at"]


class WithdrawalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ["method", "amount", "withdraw_information"]

    def validate(self, data):
        method = data["method"]
        amount = data["amount"]
        if amount < method.min_limit:
            raise serializers.ValidationError(f"Minimum withdrawal is {method.min_limit}.")
        if amount > method.max_limit:
            raise serializers.ValidationError(f"Maximum withdrawal is {method.max_limit}.")
        user = self.context["request"].user
        if user.balance < amount:
            raise serializers.ValidationError("Insufficient balance.")
        return data

    def create(self, validated_data):
        import secrets
        method = validated_data["method"]
        amount = validated_data["amount"]
        charge = method.fixed_charge + (amount * method.percent_charge / 100 if method.percent_charge else 0)
        final_amount = amount - charge
        return Withdrawal.objects.create(
            user=self.context["request"].user,
            charge=charge,
            final_amount=final_amount,
            after_charge=amount - charge,
            trx=secrets.token_hex(10).upper(),
            status=Withdrawal.Status.PENDING,
            **validated_data,
        )


# ─── ViewSets ────────────────────────────────────────────────────────────────

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["payment_status", "status", "event"]
    ordering_fields = ["created_at", "total_price"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.select_related("event", "user").all()
        return Order.objects.select_related("event").filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return created_response(OrderSerializer(order).data, "Order placed successfully.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def mark_paid(self, request, pk=None):
        order = self.get_object()
        order.payment_status = Order.PaymentStatus.PAID
        # Update seats booked
        order.event.seats_booked += order.quantity or 1
        order.event.save(update_fields=["seats_booked"])
        order.save(update_fields=["payment_status"])
        return success_response(message="Order marked as paid.")

    @action(detail=True, methods=["post"], permission_classes=[IsOwnerOrAdmin])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.payment_status == Order.PaymentStatus.PAID:
            return error_response("Cannot cancel a paid order.")
        order.status = Order.OrderStatus.CANCELLED
        order.save(update_fields=["status"])
        return success_response(message="Order cancelled.")


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["trx_type", "remark"]
    ordering_fields = ["created_at", "amount"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(user=user)


class WithdrawMethodViewSet(viewsets.ModelViewSet):
    queryset = WithdrawMethod.objects.filter(status=True)
    serializer_class = WithdrawMethodSerializer

    def get_permissions(self):
        from rest_framework.permissions import AllowAny
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdmin()]


class WithdrawalViewSet(viewsets.ModelViewSet):
    serializer_class = WithdrawalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "amount"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Withdrawal.objects.select_related("method", "user").all()
        return Withdrawal.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return WithdrawalCreateSerializer
        return WithdrawalSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        withdrawal = serializer.save()
        return created_response(WithdrawalSerializer(withdrawal).data, "Withdrawal request submitted.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def approve(self, request, pk=None):
        withdrawal = self.get_object()
        if withdrawal.status != Withdrawal.Status.PENDING:
            return error_response("Only pending withdrawals can be approved.")
        withdrawal.status = Withdrawal.Status.SUCCESS
        withdrawal.admin_feedback = request.data.get("feedback", "")
        # Deduct balance
        if withdrawal.user:
            withdrawal.user.balance -= withdrawal.amount
            withdrawal.user.save(update_fields=["balance"])
        withdrawal.save()
        return success_response(message="Withdrawal approved.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def reject(self, request, pk=None):
        withdrawal = self.get_object()
        if withdrawal.status != Withdrawal.Status.PENDING:
            return error_response("Only pending withdrawals can be rejected.")
        withdrawal.status = Withdrawal.Status.CANCELLED
        withdrawal.admin_feedback = request.data.get("feedback", "Required.")
        withdrawal.save()
        return success_response(message="Withdrawal rejected.")
