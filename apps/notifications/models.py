"""
Notifications app: NotificationTemplate, NotificationLog, AdminNotification.
"""
from django.db import models
from rest_framework import serializers, viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.routers import DefaultRouter
from django.contrib import admin

from apps.core.models import BaseModel
from apps.core.permissions import IsAdmin
from apps.core.responses import success_response
from apps.accounts.models import User, Organizer


# ─── Models ──────────────────────────────────────────────────────────────────

class NotificationTemplate(BaseModel):
    act = models.CharField(max_length=40, blank=True, null=True)
    name = models.CharField(max_length=40, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    push_title = models.CharField(max_length=255, blank=True, null=True)
    email_body = models.TextField(blank=True, null=True)
    sms_body = models.TextField(blank=True, null=True)
    push_body = models.TextField(blank=True, null=True)
    shortcodes = models.TextField(blank=True, null=True)
    email_status = models.BooleanField(default=True)
    email_sent_from_name = models.CharField(max_length=40, blank=True, null=True)
    email_sent_from_address = models.CharField(max_length=40, blank=True, null=True)
    sms_status = models.BooleanField(default=True)
    sms_sent_from = models.CharField(max_length=40, blank=True, null=True)
    push_status = models.BooleanField(default=False)

    class Meta:
        db_table = "notification_templates"
        verbose_name = "Notification Template"

    def __str__(self):
        return f"{self.name} ({self.act})"


class NotificationLog(BaseModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="notification_logs")
    organizer = models.ForeignKey(Organizer, on_delete=models.SET_NULL, null=True, blank=True, related_name="notification_logs")
    sender = models.CharField(max_length=40, blank=True, null=True)
    sent_from = models.CharField(max_length=40, blank=True, null=True)
    sent_to = models.CharField(max_length=40, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    notification_type = models.CharField(max_length=40, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    user_read = models.SmallIntegerField(default=0)

    class Meta:
        db_table = "notification_logs"
        verbose_name = "Notification Log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification_type}: {self.subject}"


class AdminNotification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    click_url = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "admin_notifications"
        verbose_name = "Admin Notification"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or ""


# ─── Serializers ─────────────────────────────────────────────────────────────

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = ["id", "subject", "message", "notification_type", "image", "user_read", "sent_from", "created_at"]


class AdminNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminNotification
        fields = ["id", "title", "is_read", "click_url", "created_at"]


# ─── Views ───────────────────────────────────────────────────────────────────

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdmin]


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationLog.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        NotificationLog.objects.filter(user=request.user, user_read=0).update(user_read=1)
        return success_response(message="All notifications marked as read.")

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.user_read = 1
        notif.save(update_fields=["user_read"])
        return success_response(message="Marked as read.")


class AdminNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdminNotification.objects.filter(is_read=False)
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAdmin]

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return success_response(message="Marked as read.")

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        AdminNotification.objects.filter(is_read=False).update(is_read=True)
        return success_response(message="All admin notifications marked as read.")


# ─── URLs ────────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register("templates", NotificationTemplateViewSet, basename="notification-template")
router.register("logs", NotificationLogViewSet, basename="notification-log")
router.register("admin", AdminNotificationViewSet, basename="admin-notification")
urlpatterns = router.urls


# ─── Admin ───────────────────────────────────────────────────────────────────

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "act", "email_status", "sms_status", "push_status"]
    list_filter = ["email_status", "sms_status", "push_status"]
    search_fields = ["name", "act", "subject"]
    list_editable = ["email_status", "sms_status"]


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ["user", "subject", "notification_type", "sent_to", "user_read", "created_at"]
    list_filter = ["notification_type", "user_read"]
    search_fields = ["user__email", "subject", "sent_to"]
    readonly_fields = ["created_at"]


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "is_read", "created_at"]
    list_filter = ["is_read"]
    list_editable = ["is_read"]
