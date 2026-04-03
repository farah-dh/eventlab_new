from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, LocationViewSet, EventViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("locations", LocationViewSet, basename="location")
router.register("", EventViewSet, basename="event")

urlpatterns = router.urls