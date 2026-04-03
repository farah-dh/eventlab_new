"""
Events app models: Category, Location, Event, GalleryImage, Speaker, TimeSlot, Slot.
"""
from django.db import models
from apps.core.models import BaseModel
from apps.accounts.models import Organizer, User


class Category(BaseModel):
    name = models.TextField()
    image = models.CharField(max_length=255, blank=True, null=True)
    slug = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return str(self.name)


class Location(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    slug = models.CharField(max_length=255, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "locations"
        verbose_name = "Location"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name or ""


class Event(BaseModel):
    class EventType(models.IntegerChoices):
        PAID = 1, "Paid"
        FREE = 2, "Free"

    organizer = models.ForeignKey(
        Organizer, on_delete=models.CASCADE, related_name="events"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="events"
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, related_name="events"
    )
    link = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True, blank=True, null=True)
    location_address = models.TextField()
    short_description = models.TextField()
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    seats = models.IntegerField(blank=True, null=True)
    seats_booked = models.IntegerField(default=0)
    price = models.FloatField(blank=True, null=True)
    cover_image = models.CharField(max_length=255, blank=True, null=True)
    type = models.SmallIntegerField(choices=EventType.choices, default=EventType.PAID)
    is_featured = models.BooleanField(default=False)
    step = models.IntegerField(default=0, help_text="Creation wizard step")
    status = models.BooleanField(default=True)
    verification_details = models.TextField(blank=True)

    # Wishlist / saved by users
    saved_by = models.ManyToManyField(User, through="UserEvent", related_name="saved_events", blank=True)

    class Meta:
        db_table = "events"
        verbose_name = "Event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["status", "is_featured"]),
        ]

    def __str__(self):
        return self.title

    @property
    def seats_available(self):
        if self.seats is None:
            return None
        return max(self.seats - self.seats_booked, 0)

    @property
    def is_sold_out(self):
        if self.seats is None:
            return False
        return self.seats_booked >= self.seats

    def save(self, *args, **kwargs):
        if not self.slug:
            import re
            self.slug = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")
        super().save(*args, **kwargs)


class GalleryImage(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.TextField()

    class Meta:
        db_table = "gallery_images"
        verbose_name = "Gallery Image"

    def __str__(self):
        return f"Image for {self.event}"


class Speaker(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="speakers")
    name = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    social = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "speakers"
        verbose_name = "Speaker"

    def __str__(self):
        return f"{self.name} @ {self.event}"


class TimeSlot(BaseModel):
    """A day/date for an event's schedule."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="time_slots")
    date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "time_slots"
        verbose_name = "Time Slot Day"

    def __str__(self):
        return f"{self.event} — {self.date}"


class Slot(BaseModel):
    """A specific session within a TimeSlot day."""
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name="slots")
    start_time = models.CharField(max_length=40, blank=True, null=True)
    end_time = models.CharField(max_length=40, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "slots"
        verbose_name = "Slot"

    def __str__(self):
        return f"{self.title} ({self.start_time} - {self.end_time})"


class UserEvent(BaseModel):
    """User saved/wishlist events."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    class Meta:
        db_table = "user_event"
        unique_together = [("user", "event")]
