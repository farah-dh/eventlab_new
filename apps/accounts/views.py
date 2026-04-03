"""
Accounts views: auth, users, organizers.
"""
from django.contrib.auth import get_user_model
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.core.permissions import IsAdmin, IsOwnerOrAdmin
from apps.core.responses import success_response, created_response, error_response
from .models import Organizer, UserLogin, DeviceToken, UserOrganizer
from .serializers import (
    CustomTokenObtainPairSerializer, RegisterSerializer, UserSerializer,
    UserUpdateSerializer, ChangePasswordSerializer, OrganizerSerializer,
    OrganizerRegisterSerializer, UserLoginSerializer, DeviceTokenSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
)

User = get_user_model()


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Log the login
            try:
                user = User.objects.get(email=request.data.get("email"))
                UserLogin.objects.create(
                    user=user,
                    ip=self._get_client_ip(request),
                    browser=request.META.get("HTTP_USER_AGENT", "")[:40],
                    os=request.META.get("HTTP_SEC_CH_UA_PLATFORM", "")[:40],
                )
            except Exception:
                pass
        return response

    def _get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR", "")


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = RefreshToken.for_user(user)
        return created_response({
            "user": UserSerializer(user).data,
            "access": str(tokens.access_token),
            "refresh": str(tokens),
        }, "Registration successful.")


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(message="Logged out successfully.")
        except Exception:
            return error_response("Invalid or expired token.")


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            import secrets, hashlib
            token = secrets.token_urlsafe(32)
            user.ver_code = hashlib.sha256(token.encode()).hexdigest()[:40]
            from django.utils import timezone
            user.ver_code_send_at = timezone.now()
            user.save(update_fields=["ver_code", "ver_code_send_at"])
            # In production, send via email task
            # from apps.notifications.tasks import send_password_reset_email
            # send_password_reset_email.delay(user.id, token)
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        return success_response(message="If that email exists, a reset link has been sent.")


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        import hashlib
        from django.utils import timezone
        from datetime import timedelta
        try:
            user = User.objects.get(email=serializer.validated_data["email"])
            token_hash = hashlib.sha256(serializer.validated_data["token"].encode()).hexdigest()[:40]
            if user.ver_code != token_hash:
                return error_response("Invalid token.")
            if user.ver_code_send_at and timezone.now() > user.ver_code_send_at + timedelta(hours=2):
                return error_response("Token has expired.")
            user.set_password(serializer.validated_data["new_password"])
            user.ver_code = None
            user.ver_code_send_at = None
            user.save()
            return success_response(message="Password reset successfully.")
        except User.DoesNotExist:
            return error_response("Invalid request.")


# ─── Users ────────────────────────────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(summary="List users (admin only)"),
    retrieve=extend_schema(summary="Get user detail"),
    update=extend_schema(summary="Update user"),
    partial_update=extend_schema(summary="Partial update user"),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "ev", "sv", "kv"]
    search_fields = ["email", "username", "firstname", "lastname", "mobile"]
    ordering_fields = ["created_at", "email", "balance"]

    def get_permissions(self):
        if self.action in ["list", "destroy"]:
            return [IsAdmin()]
        if self.action in ["retrieve", "update", "partial_update"]:
            return [IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.method == "GET":
            return success_response(UserSerializer(request.user).data)
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(UserSerializer(request.user).data, "Profile updated.")

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return success_response(message="Password changed successfully.")

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def login_history(self, request):
        logs = UserLogin.objects.filter(user=request.user).order_by("-created_at")[:20]
        return success_response(UserLoginSerializer(logs, many=True).data)

    @action(detail=False, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def device_token(self, request):
        if request.method == "POST":
            serializer = DeviceTokenSerializer(data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return created_response(serializer.data)
        token = request.data.get("token")
        DeviceToken.objects.filter(user=request.user, token=token).delete()
        return success_response(message="Device token removed.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def ban(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.ban_reason = request.data.get("reason", "")
        user.save(update_fields=["is_active", "ban_reason"])
        return success_response(message=f"User {user.email} has been banned.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def unban(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.ban_reason = None
        user.save(update_fields=["is_active", "ban_reason"])
        return success_response(message=f"User {user.email} has been unbanned.")


# ─── Organizers ───────────────────────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(summary="List organizers"),
    retrieve=extend_schema(summary="Get organizer detail"),
)
class OrganizerViewSet(viewsets.ModelViewSet):
    queryset = Organizer.objects.filter(status=True).order_by("-created_at")
    serializer_class = OrganizerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "is_featured", "kv"]
    search_fields = ["organization_name", "username", "email"]
    ordering_fields = ["created_at", "organization_name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        if self.action == "create":
            return [AllowAny()]
        if self.action in ["update", "partial_update"]:
            return [IsOwnerOrAdmin()]
        return [IsAdmin()]

    def get_serializer_class(self):
        if self.action == "create":
            return OrganizerRegisterSerializer
        return OrganizerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organizer = serializer.save()
        return created_response(OrganizerSerializer(organizer).data, "Organizer registered.")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def follow(self, request, pk=None):
        organizer = self.get_object()
        _, created = UserOrganizer.objects.get_or_create(
            user=request.user, organizer=organizer
        )
        msg = "Now following organizer." if created else "Already following."
        return success_response(message=msg)

    @action(detail=True, methods=["delete"], permission_classes=[IsAuthenticated])
    def unfollow(self, request, pk=None):
        organizer = self.get_object()
        UserOrganizer.objects.filter(user=request.user, organizer=organizer).delete()
        return success_response(message="Unfollowed organizer.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def ban(self, request, pk=None):
        organizer = self.get_object()
        organizer.status = False
        organizer.ban_reason = request.data.get("reason", "")
        organizer.save(update_fields=["status", "ban_reason"])
        return success_response(message="Organizer banned.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def approve_kyc(self, request, pk=None):
        organizer = self.get_object()
        organizer.kv = 1
        organizer.save(update_fields=["kv"])
        return success_response(message="KYC approved.")

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def reject_kyc(self, request, pk=None):
        organizer = self.get_object()
        organizer.kv = 0
        organizer.kyc_rejection_reason = request.data.get("reason", "")
        organizer.save(update_fields=["kv", "kyc_rejection_reason"])
        return success_response(message="KYC rejected.")
