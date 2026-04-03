from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Organizer, UserLogin, DeviceToken

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        token["is_staff"] = user.is_staff
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "username", "firstname", "lastname", "password", "password_confirm"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    is_kyc_verified = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "firstname", "lastname", "full_name",
            "dial_code", "country_name", "city", "state", "zip", "address",
            "country_code", "mobile", "balance", "profile_image",
            "is_active", "profile_complete", "ev", "sv", "kv", "is_kyc_verified",
            "ts", "tv", "provider", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "balance", "ev", "sv", "kv", "created_at", "updated_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "firstname", "lastname", "username", "dial_code", "country_name",
            "city", "state", "zip", "address", "country_code", "mobile", "profile_image",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return data

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class OrganizerSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    followers_count = serializers.SerializerMethodField()

    class Meta:
        model = Organizer
        fields = [
            "id", "organization_name", "slug", "firstname", "lastname", "full_name",
            "username", "email", "dial_code", "country_name", "city", "state",
            "country_code", "mobile", "balance", "status", "is_featured",
            "kv", "ev", "sv", "title", "profile_image", "cover_image",
            "short_description", "long_description", "followers_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "balance", "slug", "created_at", "updated_at"]

    def get_followers_count(self, obj):
        return obj.followers.count()


class OrganizerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Organizer
        fields = [
            "organization_name", "firstname", "lastname", "username", "email",
            "mobile", "dial_code", "country_code", "password", "password_confirm",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password
        import re
        validated_data.pop("password_confirm")
        raw_password = validated_data.pop("password")
        slug = re.sub(r"[^a-z0-9]+", "-", validated_data["organization_name"].lower()).strip("-")
        organizer = Organizer.objects.create(
            password=make_password(raw_password),
            slug=slug,
            **validated_data,
        )
        return organizer


class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLogin
        fields = ["id", "ip", "city", "country", "browser", "os", "created_at"]


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "token", "is_app", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        token = validated_data["token"]
        obj, _ = DeviceToken.objects.update_or_create(
            user=user, token=token,
            defaults={"is_app": validated_data.get("is_app", False)},
        )
        return obj


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    email = serializers.EmailField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return data
