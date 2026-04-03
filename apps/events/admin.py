from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Category, Location, Event, GalleryImage, Speaker, TimeSlot, Slot


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "sort_order", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["name"]
    list_editable = ["sort_order", "status"]
    prepopulated_fields = {}


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_featured", "sort_order", "status"]
    list_filter = ["is_featured", "status"]
    search_fields = ["name"]
    list_editable = ["is_featured", "sort_order", "status"]


class GalleryImageInline(admin.TabularInline):
    model = GalleryImage
    extra = 0
    fields = ["image"]


class SpeakerInline(admin.TabularInline):
    model = Speaker
    extra = 0
    fields = ["name", "designation", "image"]


class TimeSlotInline(admin.TabularInline):
    model = TimeSlot
    extra = 0
    fields = ["date"]
    show_change_link = True


@admin.register(Event)
class EventAdmin(ImportExportModelAdmin):
    list_display = [
        "title", "organizer", "category", "location", "type",
        "start_date", "end_date", "price", "seats_booked", "is_featured", "status",
    ]
    list_filter = ["status", "type", "is_featured", "category", "location"]
    search_fields = ["title", "organizer__organization_name", "location_address"]
    readonly_fields = ["seats_booked", "slug", "created_at", "updated_at"]
    list_per_page = 25
    inlines = [GalleryImageInline, SpeakerInline, TimeSlotInline]

    fieldsets = (
        ("Basic Info", {"fields": ("title", "slug", "organizer", "category", "location")}),
        ("Details", {"fields": ("short_description", "description", "link")}),
        ("Schedule", {"fields": ("start_date", "end_date", "location_address")}),
        ("Tickets", {"fields": ("type", "price", "seats", "seats_booked")}),
        ("Media", {"fields": ("cover_image",)}),
        ("Status", {"fields": ("status", "is_featured", "step", "verification_details")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    actions = ["feature_events", "approve_events", "reject_events"]

    def feature_events(self, request, queryset):
        queryset.update(is_featured=True)
    feature_events.short_description = "Mark as featured"

    def approve_events(self, request, queryset):
        queryset.update(status=True)
    approve_events.short_description = "Approve selected events"

    def reject_events(self, request, queryset):
        queryset.update(status=False)
    reject_events.short_description = "Reject selected events"


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ["event", "date"]
    search_fields = ["event__title"]

