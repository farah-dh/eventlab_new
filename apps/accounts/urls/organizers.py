from rest_framework.routers import DefaultRouter
from apps.accounts.views import OrganizerViewSet

router = DefaultRouter()
router.register("", OrganizerViewSet, basename="organizer")
urlpatterns = router.urls
