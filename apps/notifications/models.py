from django.db import models
from django.contrib import admin
from apps.core.models import BaseModel
from apps.accounts.models import User, Organizer


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
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="notification_logs"
    )
    # ✅ Champ organisateur pour les notifications de l'organisateur
    organizer = models.ForeignKey(
        Organizer, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="notification_logs"
    )
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

    @property
    def is_read(self):
        return self.user_read == 1


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


# ─── Admin ────────────────────────────────────────────────────────────────────

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display  = ["name", "act", "email_status", "sms_status", "push_status"]
    list_filter   = ["email_status", "sms_status", "push_status"]
    search_fields = ["name", "act", "subject"]
    list_editable = ["email_status", "sms_status"]


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display    = ["user", "organizer", "subject", "notification_type", "sent_to", "user_read", "created_at"]
    list_filter     = ["notification_type", "user_read"]
    search_fields   = ["user__email", "organizer__email", "subject", "sent_to"]
    readonly_fields = ["created_at"]


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display  = ["title", "user", "organizer", "is_read", "created_at"]
    list_filter   = ["is_read"]
    list_editable = ["is_read"]