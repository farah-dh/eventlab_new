from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from import_export.admin import ImportExportModelAdmin
from .models import User, Organizer, Admin, UserLogin, DeviceToken, UserOrganizer


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ImportExportModelAdmin):
    list_display = ["email", "full_name", "username", "is_active", "ev", "kv", "balance", "created_at"]
    list_filter = ["is_active", "is_staff", "ev", "sv", "kv"]
    search_fields = ["email", "username", "firstname", "lastname", "mobile"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "last_login"]
    list_per_page = 25

    fieldsets = (
        ("Credentials", {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("firstname", "lastname", "username", "mobile", "dial_code")}),
        ("Location", {"fields": ("country_name", "country_code", "city", "state", "zip", "address")}),
        ("Financial", {"fields": ("balance",)}),
        ("Status & Permissions", {"fields": (
            "is_active", "is_staff", "is_superuser", "ban_reason",
            "groups", "user_permissions",
        )}),
        ("Verification", {"fields": ("ev", "sv", "kv", "kyc_data", "kyc_rejection_reason")}),
        ("2FA", {"fields": ("ts", "tv", "tsc")}),
        ("Timestamps", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2"),
        }),
    )

    actions = ["ban_users", "activate_users"]

    def ban_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} user(s) banned.")
    ban_users.short_description = "Ban selected users"

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} user(s) activated.")
    activate_users.short_description = "Activate selected users"


@admin.register(Organizer)
class OrganizerAdmin(ImportExportModelAdmin):
    list_display = ["organization_name", "email", "username", "status", "is_featured", "kv", "balance", "created_at"]
    list_filter = ["status", "is_featured", "kv", "ev"]
    search_fields = ["organization_name", "email", "username", "mobile"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 25

    fieldsets = (
        ("Organization", {"fields": ("organization_name", "slug", "title", "short_description", "long_description")}),
        ("Contact", {"fields": ("firstname", "lastname", "email", "username", "mobile", "dial_code")}),
        ("Location", {"fields": ("country_name", "country_code", "city", "state", "zip", "address")}),
        ("Media", {"fields": ("profile_image", "cover_image")}),
        ("Financial", {"fields": ("balance",)}),
        ("Status", {"fields": ("status", "is_featured", "ban_reason", "profile_complete")}),
        ("Verification", {"fields": ("ev", "sv", "kv", "kyc_data", "kyc_rejection_reason")}),
        ("2FA", {"fields": ("ts", "tv")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    actions = ["approve_kyc", "reject_kyc", "feature_organizers"]

    def approve_kyc(self, request, queryset):
        queryset.update(kv=1)
        self.message_user(request, "KYC approved for selected organizers.")
    approve_kyc.short_description = "Approve KYC"

    def reject_kyc(self, request, queryset):
        queryset.update(kv=0)
        self.message_user(request, "KYC rejected for selected organizers.")
    reject_kyc.short_description = "Reject KYC"

    def feature_organizers(self, request, queryset):
        queryset.update(is_featured=True)
    feature_organizers.short_description = "Mark as featured"


@admin.register(UserLogin)
class UserLoginAdmin(admin.ModelAdmin):
    list_display = ["user", "ip", "city", "country", "browser", "os", "created_at"]
    list_filter = ["country"]
    search_fields = ["user__email", "ip", "city", "country"]
    readonly_fields = ["created_at"]
    list_per_page = 50


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "organizer", "is_app", "created_at"]
    list_filter = ["is_app"]
    search_fields = ["user__email", "organizer__email"]
