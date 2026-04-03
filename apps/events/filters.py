import django_filters
from .models import Event


class EventFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    start_date_from = django_filters.DateFilter(field_name="start_date", lookup_expr="gte")
    start_date_to = django_filters.DateFilter(field_name="start_date", lookup_expr="lte")

    class Meta:
        model = Event
        fields = {
            "category": ["exact"],
            "location": ["exact"],
            "organizer": ["exact"],
            "type": ["exact"],
            "is_featured": ["exact"],
            "status": ["exact"],
        }
