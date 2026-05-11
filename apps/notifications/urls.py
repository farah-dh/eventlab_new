from rest_framework.routers import DefaultRouter
from .views import NotificationTemplateViewSet, NotificationLogViewSet, AdminNotificationViewSet

router = DefaultRouter()
router.register("templates", NotificationTemplateViewSet, basename="notification-template")
router.register("logs",      NotificationLogViewSet,      basename="notification-log")
router.register("admin",     AdminNotificationViewSet,    basename="admin-notification")

urlpatterns = router.urls
