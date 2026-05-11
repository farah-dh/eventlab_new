import random
import string
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.contrib.auth.hashers import check_password as django_check_password

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
OTP_EXPIRY_MINUTES = 10


def _generate_otp(length=6):
    return "".join(random.choices(string.digits, k=length))


def _send_otp_email(user, otp):
    """Send OTP to a regular User."""
    send_mail(
        subject="🔐 Votre code de vérification EventFlow",
        message=(
            f"Bonjour {user.username or user.email},\n\n"
            f"Votre code de vérification à deux facteurs est :\n\n"
            f"    {otp}\n\n"
            f"Ce code expire dans {OTP_EXPIRY_MINUTES} minutes.\n"
            f"Si vous n'avez pas demandé ce code, ignorez cet email.\n\n"
            f"L'équipe EventFlow"
        ),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )


def _send_otp_email_organizer(organizer, otp):
    """Send OTP to an Organizer (uses organizer.email directly)."""
    send_mail(
        subject="🔐 Votre code de vérification EventFlow",
        message=(
            f"Bonjour {organizer.organization_name},\n\n"
            f"Votre code de vérification à deux facteurs est :\n\n"
            f"    {otp}\n\n"
            f"Ce code expire dans {OTP_EXPIRY_MINUTES} minutes.\n"
            f"Si vous n'avez pas demandé ce code, ignorez cet email.\n\n"
            f"L'équipe EventFlow"
        ),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[organizer.email],
        fail_silently=False,
    )


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return error_response("Invalid email or password.")

        user = User.objects.get(email=request.data.get("email"))

        if user.ts:
            otp = _generate_otp()
            user.tsc = otp
            user.ver_code_send_at = timezone.now()
            user.save(update_fields=["tsc", "ver_code_send_at"])
            try:
                _send_otp_email(user, otp)
            except Exception:
                return error_response("Failed to send OTP. Please try again.")
            return Response({
                "2fa_required": True,
                "user_id": user.id,
                "message": f"OTP sent to {user.email}",
            }, status=status.HTTP_200_OK)

        self._log_login(request, user)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    def _log_login(self, request, user):
        try:
            x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR", "")
            UserLogin.objects.create(
                user=user,
                ip=ip,
                browser=request.META.get("HTTP_USER_AGENT", "")[:40],
                os=request.META.get("HTTP_SEC_CH_UA_PLATFORM", "")[:40],
            )
        except Exception:
            pass


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
            token = RefreshToken(request.data.get("refresh"))
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
            user.ver_code_send_at = timezone.now()
            user.save(update_fields=["ver_code", "ver_code_send_at"])
        except User.DoesNotExist:
            pass
        return success_response(message="If that email exists, a reset link has been sent.")


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        import hashlib
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


# ─── 2FA (User) ───────────────────────────────────────────────────────────────

class TwoFAVerifyLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        otp = request.data.get("otp", "").strip()
        if not user_id or not otp:
            return error_response("user_id and otp are required.")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return error_response("Invalid request.")
        if not user.ver_code_send_at or timezone.now() > user.ver_code_send_at + timedelta(minutes=OTP_EXPIRY_MINUTES):
            return error_response("OTP has expired. Please login again.")
        if user.tsc != otp:
            return error_response("Invalid OTP code.")
        user.tsc = None
        user.ver_code_send_at = None
        user.tv = True
        user.save(update_fields=["tsc", "ver_code_send_at", "tv"])
        tokens = RefreshToken.for_user(user)
        return success_response({
            "access": str(tokens.access_token),
            "refresh": str(tokens),
            "user": UserSerializer(user).data,
        }, "Login successful.")


class TwoFAResendOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return error_response("user_id is required.")
        try:
            user = User.objects.get(id=user_id, ts=True)
        except User.DoesNotExist:
            return error_response("Invalid request.")
        if user.ver_code_send_at and timezone.now() < user.ver_code_send_at + timedelta(seconds=60):
            wait = 60 - (timezone.now() - user.ver_code_send_at).seconds
            return error_response(f"Please wait {wait} seconds before requesting a new code.")
        otp = _generate_otp()
        user.tsc = otp
        user.ver_code_send_at = timezone.now()
        user.save(update_fields=["tsc", "ver_code_send_at"])
        try:
            _send_otp_email(user, otp)
        except Exception:
            return error_response("Failed to send OTP. Please try again.")
        return success_response(message=f"OTP resent to {user.email}.")


class TwoFAEnableView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.ts:
            return error_response("2FA is already enabled.")
        otp = _generate_otp()
        user.tsc = otp
        user.ver_code_send_at = timezone.now()
        user.save(update_fields=["tsc", "ver_code_send_at"])
        try:
            _send_otp_email(user, otp)
        except Exception:
            return error_response("Failed to send OTP. Please try again.")
        return success_response(message=f"OTP sent to {user.email}. Verify to activate 2FA.")


class TwoFAEnableConfirmView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        otp = request.data.get("otp", "").strip()
        if not otp:
            return error_response("OTP is required.")
        if not user.ver_code_send_at or timezone.now() > user.ver_code_send_at + timedelta(minutes=OTP_EXPIRY_MINUTES):
            return error_response("OTP has expired. Please request a new one.")
        if user.tsc != otp:
            return error_response("Invalid OTP code.")
        user.ts = True
        user.tv = True
        user.tsc = None
        user.ver_code_send_at = None
        user.save(update_fields=["ts", "tv", "tsc", "ver_code_send_at"])
        return success_response(message="2FA has been enabled successfully.")


class TwoFADisableView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.ts:
            return error_response("2FA is not enabled.")
        otp = request.data.get("otp", "").strip()
        if not otp:
            new_otp = _generate_otp()
            user.tsc = new_otp
            user.ver_code_send_at = timezone.now()
            user.save(update_fields=["tsc", "ver_code_send_at"])
            try:
                _send_otp_email(user, new_otp)
            except Exception:
                return error_response("Failed to send OTP. Please try again.")
            return success_response(message=f"OTP sent to {user.email}. Submit the OTP to disable 2FA.")
        if not user.ver_code_send_at or timezone.now() > user.ver_code_send_at + timedelta(minutes=OTP_EXPIRY_MINUTES):
            return error_response("OTP has expired. Please request a new one.")
        if user.tsc != otp:
            return error_response("Invalid OTP code.")
        user.ts = False
        user.tv = True
        user.tsc = None
        user.ver_code_send_at = None
        user.save(update_fields=["ts", "tv", "tsc", "ver_code_send_at"])
        return success_response(message="2FA has been disabled.")


class TwoFAStatusView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response({
            "2fa_enabled": request.user.ts,
            "email": request.user.email,
        })


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
        _, created = UserOrganizer.objects.get_or_create(user=request.user, organizer=organizer)
        return success_response(message="Now following organizer." if created else "Already following.")

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


# ─── Organizer Login + 2FA ────────────────────────────────────────────────────

class OrganizerLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email    = request.data.get("email", "").strip()
        password = request.data.get("password", "")

        if not email or not password:
            return error_response("Email and password are required.")

        try:
            organizer = Organizer.objects.get(email=email, status=True)
        except Organizer.DoesNotExist:
            return error_response("Invalid credentials.")

        if not django_check_password(password, organizer.password):
            return error_response("Invalid credentials.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response("No user account found for this organizer.")

        # ── 2FA check (même logique que LoginView) ─────────────────────────
        if user.ts:
            otp = _generate_otp()
            user.tsc = otp
            user.ver_code_send_at = timezone.now()
            user.save(update_fields=["tsc", "ver_code_send_at"])
            try:
                _send_otp_email_organizer(organizer, otp)
            except Exception:
                return error_response("Failed to send OTP. Please try again.")
            return Response({
                "2fa_required":  True,
                "organizer_id":  organizer.id,
                "message":       f"OTP sent to {organizer.email}",
            }, status=status.HTTP_200_OK)
        # ───────────────────────────────────────────────────────────────────

        token = RefreshToken.for_user(user)
        token["organizer_id"]      = organizer.id
        token["email"]             = organizer.email
        token["organization_name"] = organizer.organization_name
        token["is_organizer"]      = True
        token["is_staff"]          = False

        return success_response({
            "access":    str(token.access_token),
            "refresh":   str(token),
            "organizer": OrganizerSerializer(organizer).data,
        }, "Login successful.")


class OrganizerTwoFAVerifyLoginView(generics.GenericAPIView):
    """Vérifie le code OTP de l'organisateur → retourne JWT."""
    permission_classes = [AllowAny]

    def post(self, request):
        organizer_id = request.data.get("organizer_id")
        otp          = request.data.get("otp", "").strip()

        if not organizer_id or not otp:
            return error_response("organizer_id and otp are required.")

        try:
            organizer = Organizer.objects.get(id=organizer_id)
            user      = User.objects.get(email=organizer.email)
        except (Organizer.DoesNotExist, User.DoesNotExist):
            return error_response("Invalid request.")

        if not user.ver_code_send_at or timezone.now() > user.ver_code_send_at + timedelta(minutes=OTP_EXPIRY_MINUTES):
            return error_response("OTP has expired. Please login again.")

        if user.tsc != otp:
            return error_response("Invalid OTP code.")

        user.tsc              = None
        user.ver_code_send_at = None
        user.tv               = True
        user.save(update_fields=["tsc", "ver_code_send_at", "tv"])

        token = RefreshToken.for_user(user)
        token["organizer_id"]      = organizer.id
        token["email"]             = organizer.email
        token["organization_name"] = organizer.organization_name
        token["is_organizer"]      = True
        token["is_staff"]          = False

        return success_response({
            "access":    str(token.access_token),
            "refresh":   str(token),
            "organizer": OrganizerSerializer(organizer).data,
        }, "Login successful.")


class OrganizerTwoFAResendOTPView(generics.GenericAPIView):
    """Renvoie l'OTP à l'organisateur (anti-spam 60s)."""
    permission_classes = [AllowAny]

    def post(self, request):
        organizer_id = request.data.get("organizer_id")

        if not organizer_id:
            return error_response("organizer_id is required.")

        try:
            organizer = Organizer.objects.get(id=organizer_id)
            user      = User.objects.get(email=organizer.email)
        except (Organizer.DoesNotExist, User.DoesNotExist):
            return error_response("Invalid request.")

        if user.ver_code_send_at and timezone.now() < user.ver_code_send_at + timedelta(seconds=60):
            wait = 60 - (timezone.now() - user.ver_code_send_at).seconds
            return error_response(f"Please wait {wait} seconds before requesting a new code.")

        otp               = _generate_otp()
        user.tsc          = otp
        user.ver_code_send_at = timezone.now()
        user.save(update_fields=["tsc", "ver_code_send_at"])

        try:
            _send_otp_email_organizer(organizer, otp)
        except Exception:
            return error_response("Failed to send OTP. Please try again.")

        return success_response(message=f"OTP resent to {organizer.email}.")