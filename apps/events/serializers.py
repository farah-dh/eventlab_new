from rest_framework import serializers
from .models import Category, Location, Event, GalleryImage, Speaker, TimeSlot, Slot, UserEvent


class CategorySerializer(serializers.ModelSerializer):
    events_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "image", "slug", "sort_order", "status", "events_count", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_events_count(self, obj):
        return obj.events.filter(status=True).count()


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "slug", "image", "is_featured", "sort_order", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ["id", "start_time", "end_time", "title", "description"]


class TimeSlotSerializer(serializers.ModelSerializer):
    slots = SlotSerializer(many=True, read_only=True)

    class Meta:
        model = TimeSlot
        fields = ["id", "date", "slots"]


class SpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speaker
        fields = ["id", "name", "designation", "social", "image"]


class GalleryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryImage
        fields = ["id", "image"]


class EventListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    organizer_name = serializers.CharField(source="organizer.organization_name", read_only=True)
    seats_available = serializers.ReadOnlyField()
    is_sold_out = serializers.ReadOnlyField()

    class Meta:
        model = Event
        fields = [
            "id", "title", "slug", "cover_image", "start_date", "end_date",
            "price", "type", "is_featured", "status", "seats", "seats_booked",
            "seats_available", "is_sold_out", "location_address",
            "category_name", "location_name", "organizer_name", "created_at",
        ]


class EventDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    speakers = SpeakerSerializer(many=True, read_only=True)
    gallery_images = GalleryImageSerializer(many=True, read_only=True)
    time_slots = TimeSlotSerializer(many=True, read_only=True)
    seats_available = serializers.ReadOnlyField()
    is_sold_out = serializers.ReadOnlyField()
    organizer_name = serializers.CharField(source="organizer.organization_name", read_only=True)
    organizer_id = serializers.IntegerField(source="organizer.id", read_only=True)

    class Meta:
        model = Event
        fields = [
            "id", "title", "slug", "link", "description", "short_description",
            "location_address", "cover_image", "start_date", "end_date",
            "price", "type", "is_featured", "status", "seats", "seats_booked",
            "seats_available", "is_sold_out", "step",
            "category", "location", "organizer_id", "organizer_name",
            "speakers", "gallery_images", "time_slots", "created_at", "updated_at",
        ]


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "category", "location", "link", "title", "location_address",
            "short_description", "description", "start_date", "end_date",
            "seats", "price", "cover_image", "type", "step",
        ]

    def validate(self, data):
        if data.get("start_date") and data.get("end_date"):
            if data["start_date"] > data["end_date"]:
                raise serializers.ValidationError("End date must be after start date.")
        return data
