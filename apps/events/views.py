from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.core.permissions import IsAdmin, IsAdminOrReadOnly, IsOwnerOrAdmin
from apps.core.responses import success_response, created_response, error_response
from .models import Category, Location, Event, GalleryImage, Speaker, TimeSlot, Slot, UserEvent
from .serializers import (
    CategorySerializer, LocationSerializer,
    EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer,
    GalleryImageSerializer, SpeakerSerializer, TimeSlotSerializer, SlotSerializer,
)
from .filters import EventFilter


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(status=True).order_by("sort_order")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["sort_order", "name"]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.filter(status=True).order_by("sort_order")
    serializer_class = LocationSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_featured", "status"]
    search_fields = ["name"]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related(
        "organizer", "category", "location"
    ).prefetch_related("speakers", "gallery_images", "time_slots").order_by("-created_at")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EventFilter
    search_fields = ["title", "short_description", "location_address"]
    ordering_fields = ["created_at", "start_date", "price", "seats_booked"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return EventListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return EventCreateUpdateSerializer
        return EventDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(status=True)
        return qs

    def perform_create(self, serializer):
        # Try to get the organizer profile for this user
        try:
            from apps.accounts.models import Organizer
            organizer = Organizer.objects.get(email=self.request.user.email)
        except Exception:
            raise Exception("You must be an organizer to create events.")
        serializer.save(organizer=organizer)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def save_event(self, request, pk=None):
        event = self.get_object()
        _, created = UserEvent.objects.get_or_create(user=request.user, event=event)
        return success_response(message="Event saved." if created else "Already saved.")

    @action(detail=True, methods=["delete"], permission_classes=[IsAuthenticated])
    def unsave_event(self, request, pk=None):
        event = self.get_object()
        UserEvent.objects.filter(user=request.user, event=event).delete()
        return success_response(message="Event removed from saved list.")

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def saved(self, request):
        events = Event.objects.filter(saved_by=request.user, status=True)
        serializer = EventListSerializer(events, many=True)
        return success_response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def feature(self, request, pk=None):
        event = self.get_object()
        event.is_featured = not event.is_featured
        event.save(update_fields=["is_featured"])
        state = "featured" if event.is_featured else "unfeatured"
        return success_response(message=f"Event is now {state}.")

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsOwnerOrAdmin])
    def gallery(self, request, pk=None):
        event = self.get_object()
        if request.method == "POST":
            image_url = request.data.get("image")
            if not image_url:
                return error_response("image field is required.")
            img = GalleryImage.objects.create(event=event, image=image_url)
            return created_response(GalleryImageSerializer(img).data)
        image_id = request.data.get("image_id")
        GalleryImage.objects.filter(id=image_id, event=event).delete()
        return success_response(message="Image removed.")

    @action(detail=True, methods=["get", "post"], url_path="speakers", permission_classes=[IsOwnerOrAdmin])
    def speakers(self, request, pk=None):
        event = self.get_object()
        if request.method == "GET":
            return success_response(SpeakerSerializer(event.speakers.all(), many=True).data)
        serializer = SpeakerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(event=event)
        return created_response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="schedule", permission_classes=[IsOwnerOrAdmin])
    def schedule(self, request, pk=None):
        event = self.get_object()
        if request.method == "GET":
            return success_response(TimeSlotSerializer(event.time_slots.prefetch_related("slots"), many=True).data)
        serializer = TimeSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(event=event)
        return created_response(serializer.data)