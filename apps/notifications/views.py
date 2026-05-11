from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from apps.core.permissions import IsAdmin
from apps.core.responses import success_response
from apps.accounts.models import Organizer
from .models import NotificationTemplate, NotificationLog, AdminNotification


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificationLogSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = NotificationLog
        fields = [
            "id", "subject", "message", "notification_type",
            "image", "user_read", "is_read", "sent_from", "created_at",
        ]

    def get_is_read(self, obj):
        return obj.user_read == 1


class AdminNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminNotification
        fields = ["id", "title", "is_read", "click_url", "created_at"]


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdmin]


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # ✅ Si c'est un Organizer → ses propres notifications
        if isinstance(user, Organizer):
            return NotificationLog.objects.filter(organizer=user)
        # User normal
        return NotificationLog.objects.filter(user=user)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        user = request.user
        if isinstance(user, Organizer):
            NotificationLog.objects.filter(organizer=user, user_read=0).update(user_read=1)
        else:
            NotificationLog.objects.filter(user=user, user_read=0).update(user_read=1)
        return success_response(message="All notifications marked as read.")

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.user_read = 1
        notif.save(update_fields=["user_read"])
        return success_response(message="Marked as read.")


class AdminNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdminNotification.objects.filter(is_read=False)
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAdmin]

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return success_response(message="Marked as read.")

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        AdminNotification.objects.filter(is_read=False).update(is_read=True)
        return success_response(message="All admin notifications marked as read.")