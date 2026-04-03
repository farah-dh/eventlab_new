"""
CMS app: GeneralSettings, Language, Page, Frontend, Extension, Subscriber, UpdateLog, CronJob.
"""
from django.db import models
from rest_framework import serializers, viewsets, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.routers import DefaultRouter
from django.urls import path
from django.contrib import admin

# Import ImportExportModelAdmin directly since it's installed
from import_export.admin import ImportExportModelAdmin

from apps.core.models import BaseModel
from apps.core.permissions import IsAdmin
from apps.core.responses import success_response, created_response


# ─── Models ──────────────────────────────────────────────────────────────────

class GeneralSettings(BaseModel):
    site_name = models.CharField(max_length=40, blank=True, null=True)
    cancel_time = models.IntegerField(blank=True, null=True)
    payment_timeout = models.IntegerField(blank=True, null=True)
    event_verification = models.BooleanField(default=False)
    cur_text = models.CharField(max_length=40, blank=True, null=True)
    cur_sym = models.CharField(max_length=40, blank=True, null=True)
    email_from = models.EmailField(max_length=40, blank=True, null=True)
    email_from_name = models.CharField(max_length=255, blank=True, null=True)
    email_template = models.TextField(blank=True, null=True)
    sms_template = models.CharField(max_length=255, blank=True, null=True)
    sms_body = models.CharField(max_length=255, blank=True, null=True)
    sms_from = models.CharField(max_length=255, blank=True, null=True)
    push_title = models.CharField(max_length=255, blank=True, null=True)
    push_template = models.CharField(max_length=255, blank=True, null=True)
    base_color = models.CharField(max_length=40, blank=True, null=True)
    secondary_color = models.CharField(max_length=40, blank=True, null=True)
    mail_config = models.JSONField(blank=True, null=True)
    sms_config = models.JSONField(blank=True, null=True)
    firebase_config = models.JSONField(blank=True, null=True)
    global_shortcodes = models.TextField(blank=True, null=True)
    kv = models.BooleanField(default=False, help_text="KYC verification required")
    ev = models.BooleanField(default=False, help_text="Email verification required")
    en = models.BooleanField(default=False, help_text="Email notifications enabled")
    sv = models.BooleanField(default=False, help_text="SMS verification required")
    sn = models.BooleanField(default=False, help_text="SMS notifications enabled")
    pn = models.BooleanField(default=True, help_text="Push notifications enabled")
    force_ssl = models.BooleanField(default=False)
    maintenance_mode = models.BooleanField(default=False)
    secure_password = models.BooleanField(default=False)
    agree = models.BooleanField(default=False)
    multi_language = models.BooleanField(default=True)
    registration = models.BooleanField(default=False)
    organizer_registration = models.SmallIntegerField(default=1)
    active_template = models.CharField(max_length=40, blank=True, null=True)
    socialite_credentials = models.JSONField(blank=True, null=True)
    system_info = models.TextField(blank=True, null=True)
    last_cron = models.DateTimeField(blank=True, null=True)
    available_version = models.CharField(max_length=40, blank=True, null=True)
    system_customized = models.BooleanField(default=False)
    paginate_number = models.IntegerField(default=0)
    currency_format = models.SmallIntegerField(
        default=0, 
        choices=[(0, "Default"), (1, "Both"), (2, "Text Only"), (3, "Symbol Only")]
    )
    max_gallery_images = models.IntegerField(default=10)

    class Meta:
        db_table = "general_settings"
        verbose_name = "General Settings"
        verbose_name_plural = "General Settings"

    def __str__(self):
        return self.site_name or "Settings"


class Language(BaseModel):
    name = models.CharField(max_length=40, blank=True, null=True)
    code = models.CharField(max_length=40, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    image = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        db_table = "languages"
        verbose_name = "Language"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Page(BaseModel):
    name = models.CharField(max_length=40, blank=True, null=True)
    slug = models.CharField(max_length=40, blank=True, null=True)
    tempname = models.CharField(max_length=40, blank=True, null=True)
    secs = models.TextField(blank=True, null=True)
    seo_content = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "pages"
        verbose_name = "Page"

    def __str__(self):
        return self.name or self.slug or ""


class Frontend(BaseModel):
    data_keys = models.CharField(max_length=40, blank=True, null=True)
    data_values = models.TextField(blank=True, null=True)
    seo_content = models.TextField(blank=True, null=True)
    tempname = models.CharField(max_length=40, blank=True, null=True)
    slug = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "frontends"
        verbose_name = "Frontend Content"

    def __str__(self):
        return f"{self.tempname} / {self.data_keys}"


class Extension(BaseModel):
    act = models.CharField(max_length=40, blank=True, null=True)
    name = models.CharField(max_length=40, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    script = models.TextField(blank=True, null=True)
    shortcode = models.JSONField(blank=True, null=True)
    support = models.TextField(blank=True, null=True)
    status = models.SmallIntegerField(
        default=1, 
        choices=[(1, "Enable"), (2, "Disable")]
    )

    class Meta:
        db_table = "extensions"
        verbose_name = "Extension"

    def __str__(self):
        return self.name or ""


class Subscriber(BaseModel):
    email = models.EmailField(max_length=40, unique=True)

    class Meta:
        db_table = "subscribers"
        verbose_name = "Subscriber"

    def __str__(self):
        return self.email


class UpdateLog(BaseModel):
    version = models.CharField(max_length=40, blank=True, null=True)
    update_log = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "update_logs"
        verbose_name = "Update Log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"v{self.version}"


class CronSchedule(BaseModel):
    name = models.CharField(max_length=40, blank=True, null=True)
    interval = models.IntegerField(default=0)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "cron_schedules"
        verbose_name = "Cron Schedule"

    def __str__(self):
        return self.name or ""


class CronJob(BaseModel):
    name = models.CharField(max_length=40, blank=True, null=True)
    alias = models.CharField(max_length=40, blank=True, null=True)
    action = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    cron_schedule = models.ForeignKey(
        CronSchedule, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="jobs"
    )
    next_run = models.DateTimeField(blank=True, null=True)
    last_run = models.DateTimeField(blank=True, null=True)
    is_running = models.BooleanField(default=True)
    is_default = models.SmallIntegerField(default=1)

    class Meta:
        db_table = "cron_jobs"
        verbose_name = "Cron Job"

    def __str__(self):
        return self.name or ""


# ─── Serializers ─────────────────────────────────────────────────────────────

class GeneralSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralSettings
        exclude = ["mail_config", "sms_config", "firebase_config", "socialite_credentials"]
        read_only_fields = ["id", "created_at", "updated_at"]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class FrontendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Frontend
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ["id", "email", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        obj, _ = Subscriber.objects.get_or_create(email=validated_data["email"])
        return obj


# ─── Views ───────────────────────────────────────────────────────────────────

class GeneralSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = GeneralSettingsSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdmin()]

    def get_object(self):
        obj, _ = GeneralSettings.objects.get_or_create(pk=1)
        return obj


class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdmin()]


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdmin()]


class FrontendViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Frontend.objects.all()
    serializer_class = FrontendSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["tempname", "slug", "data_keys"]


class SubscribeView(generics.CreateAPIView):
    serializer_class = SubscriberSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return created_response(message="Subscribed successfully.")


# ─── URLs ────────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register("languages", LanguageViewSet, basename="language")
router.register("pages", PageViewSet, basename="page")
router.register("frontend", FrontendViewSet, basename="frontend")

urlpatterns = router.urls + [
    path("settings/", GeneralSettingsView.as_view(), name="general-settings"),
    path("subscribe/", SubscribeView.as_view(), name="subscribe"),
]


# ─── Admin ───────────────────────────────────────────────────────────────────

@admin.register(GeneralSettings)
class GeneralSettingsAdmin(admin.ModelAdmin):
    list_display = ["site_name", "cur_text", "cur_sym", "maintenance_mode", "registration"]

    def has_add_permission(self, request):
        return not GeneralSettings.objects.exists()


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_default"]
    list_editable = ["is_default"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "tempname", "is_default"]
    search_fields = ["name", "slug"]


@admin.register(Frontend)
class FrontendAdmin(admin.ModelAdmin):
    list_display = ["tempname", "data_keys", "slug"]
    list_filter = ["tempname"]
    search_fields = ["data_keys", "tempname"]


@admin.register(Extension)
class ExtensionAdmin(admin.ModelAdmin):
    list_display = ["name", "act", "status"]
    list_editable = ["status"]


@admin.register(Subscriber)
class SubscriberAdmin(ImportExportModelAdmin):
    list_display = ["email", "created_at"]
    search_fields = ["email"]


@admin.register(UpdateLog)
class UpdateLogAdmin(admin.ModelAdmin):
    list_display = ["version", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(CronSchedule)
class CronScheduleAdmin(admin.ModelAdmin):
    list_display = ["name", "interval", "status"]
    list_editable = ["status"]


@admin.register(CronJob)
class CronJobAdmin(admin.ModelAdmin):
    list_display = ["name", "alias", "next_run", "last_run", "is_running"]
    list_filter = ["is_running"]