"""
Support app: SupportTicket, SupportMessage, SupportAttachment.
"""
from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.routers import DefaultRouter
from django.contrib import admin

from apps.core.models import BaseModel
from apps.core.permissions import IsAdmin, IsOwnerOrAdmin
from apps.core.responses import success_response, created_response
from apps.accounts.models import User, Organizer


# ─── Models ──────────────────────────────────────────────────────────────────

class SupportTicket(BaseModel):
    class Status(models.IntegerChoices):
        OPEN = 0, "Open"
        ANSWERED = 1, "Answered"
        REPLIED = 2, "Replied"
        CLOSED = 3, "Closed"

    class Priority(models.IntegerChoices):
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets")
    organizer = models.ForeignKey(Organizer, on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets")
    name = models.CharField(max_length=40, blank=True, null=True)
    email = models.EmailField(max_length=40, blank=True, null=True)
    ticket = models.CharField(max_length=40, blank=True, null=True, unique=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    status = models.SmallIntegerField(choices=Status.choices, default=Status.OPEN)
    priority = models.SmallIntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    last_reply = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "support_tickets"
        verbose_name = "Support Ticket"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["ticket"])]

    def __str__(self):
        return f"[{self.ticket}] {self.subject}"

    def save(self, *args, **kwargs):
        if not self.ticket:
            import secrets
            self.ticket = secrets.token_hex(5).upper()
        super().save(*args, **kwargs)


class SupportMessage(BaseModel):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    admin_id = models.IntegerField(default=0)
    message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "support_messages"
        verbose_name = "Support Message"
        ordering = ["created_at"]

    def __str__(self):
        return f"Message on {self.ticket}"


class SupportAttachment(BaseModel):
    support_message = models.ForeignKey(SupportMessage, on_delete=models.CASCADE, related_name="attachments")
    attachment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "support_attachments"
        verbose_name = "Support Attachment"


# ─── Serializers ─────────────────────────────────────────────────────────────

class SupportAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportAttachment
        fields = ["id", "attachment"]


class SupportMessageSerializer(serializers.ModelSerializer):
    attachments = SupportAttachmentSerializer(many=True, read_only=True)
    is_admin_reply = serializers.SerializerMethodField()

    class Meta:
        model = SupportMessage
        fields = ["id", "message", "attachments", "is_admin_reply", "admin_id", "created_at"]
        read_only_fields = ["id", "admin_id", "created_at"]

    def get_is_admin_reply(self, obj):
        return obj.admin_id != 0


class SupportTicketListSerializer(serializers.ModelSerializer):
    messages_count = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id", "ticket", "subject", "status", "priority",
            "last_reply", "messages_count", "created_at",
        ]

    def get_messages_count(self, obj):
        return obj.messages.count()


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    messages = SupportMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            "id", "ticket", "subject", "status", "priority",
            "name", "email", "last_reply", "messages", "created_at",
        ]


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    first_message = serializers.CharField(write_only=True)

    class Meta:
        model = SupportTicket
        fields = ["subject", "priority", "first_message"]

    def create(self, validated_data):
        from django.utils import timezone
        first_message = validated_data.pop("first_message")
        user = self.context["request"].user
        ticket = SupportTicket.objects.create(
            user=user,
            name=user.full_name,
            email=user.email,
            last_reply=timezone.now(),
            **validated_data,
        )
        SupportMessage.objects.create(ticket=ticket, message=first_message)
        return ticket


class ReplySerializer(serializers.Serializer):
    message = serializers.CharField()
    attachments = serializers.ListField(
        child=serializers.CharField(), required=False
    )


# ─── Views ───────────────────────────────────────────────────────────────────

class SupportTicketViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SupportTicket.objects.prefetch_related("messages").all()
        return SupportTicket.objects.filter(user=user).prefetch_related("messages")

    def get_serializer_class(self):
        if self.action == "list":
            return SupportTicketListSerializer
        if self.action == "create":
            return SupportTicketCreateSerializer
        return SupportTicketDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        return created_response(SupportTicketDetailSerializer(ticket).data, "Ticket created.")

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        from django.utils import timezone
        ticket = self.get_object()
        serializer = ReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_admin = request.user.is_staff
        msg = SupportMessage.objects.create(
            ticket=ticket,
            message=serializer.validated_data["message"],
            admin_id=request.user.pk if is_admin else 0,
        )
        for attachment_url in serializer.validated_data.get("attachments", []):
            SupportAttachment.objects.create(support_message=msg, attachment=attachment_url)

        ticket.last_reply = timezone.now()
        ticket.status = SupportTicket.Status.ANSWERED if is_admin else SupportTicket.Status.REPLIED
        ticket.save(update_fields=["last_reply", "status"])
        return created_response(SupportMessageSerializer(msg).data, "Reply sent.")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def close(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = SupportTicket.Status.CLOSED
        ticket.save(update_fields=["status"])
        return success_response(message="Ticket closed.")


# ─── URLs ────────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register("tickets", SupportTicketViewSet, basename="support-ticket")
urlpatterns = router.urls


# ─── Admin ───────────────────────────────────────────────────────────────────

class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ["created_at"]
    fields = ["message", "admin_id", "created_at"]


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ["ticket", "subject", "user", "status", "priority", "last_reply", "created_at"]
    list_filter = ["status", "priority"]
    search_fields = ["ticket", "subject", "user__email", "email"]
    readonly_fields = ["ticket", "created_at", "updated_at"]
    inlines = [SupportMessageInline]
    ordering = ["-created_at"]

    actions = ["close_tickets"]

    def close_tickets(self, request, queryset):
        queryset.update(status=SupportTicket.Status.CLOSED)
    close_tickets.short_description = "Close selected tickets"

