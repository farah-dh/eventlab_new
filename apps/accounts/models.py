"""
Accounts app models: User, Organizer, Admin, UserLogin, DeviceToken.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from apps.core.models import BaseModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """Platform end user."""
    firstname = models.CharField(max_length=40, blank=True, null=True)
    lastname = models.CharField(max_length=40, blank=True, null=True)
    username = models.CharField(max_length=40, unique=True, null=True, blank=True)
    email = models.EmailField(max_length=40, unique=True)
    dial_code = models.CharField(max_length=40, blank=True, null=True)
    country_name = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    zip = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    country_code = models.CharField(max_length=40, blank=True, null=True)
    mobile = models.CharField(max_length=40, blank=True, null=True)
    balance = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    profile_image = models.ImageField(upload_to="users/avatars/", blank=True, null=True)

    # Status flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    ban_reason = models.CharField(max_length=255, blank=True, null=True)
    profile_complete = models.BooleanField(default=False)

    # Verification
    ev = models.BooleanField(default=False, help_text="Email verified")
    sv = models.BooleanField(default=False, help_text="Mobile verified")
    kv = models.SmallIntegerField(
        default=0, choices=[(0, "Unverified"), (1, "Verified"), (2, "Pending")],
        help_text="KYC status"
    )
    kyc_data = models.TextField(blank=True, null=True)
    kyc_rejection_reason = models.CharField(max_length=255, blank=True, null=True)
    ver_code = models.CharField(max_length=40, blank=True, null=True)
    ver_code_send_at = models.DateTimeField(blank=True, null=True)

    # 2FA
    ts = models.BooleanField(default=False, help_text="2FA enabled")
    tv = models.BooleanField(default=True, help_text="2FA verified")
    tsc = models.CharField(max_length=255, blank=True, null=True, help_text="2FA secret")

    # Auth
    provider = models.CharField(max_length=255, blank=True, null=True)
    provider_id = models.CharField(max_length=255, blank=True, null=True)
    remember_token = models.CharField(max_length=255, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"

    def get_full_name(self):
        return f"{self.firstname or ''} {self.lastname or ''}".strip() or self.email

    @property
    def full_name(self):
        return self.get_full_name()

    @property
    def is_kyc_verified(self):
        return self.kv == 1


class Organizer(BaseModel):
    """Event organizer profile (separate from User)."""
    organization_name = models.TextField()
    slug = models.TextField(blank=True, null=True)
    firstname = models.CharField(max_length=40, blank=True, null=True)
    lastname = models.CharField(max_length=40, blank=True, null=True)
    username = models.CharField(max_length=40, unique=True)
    email = models.EmailField(max_length=40, unique=True)
    dial_code = models.CharField(max_length=40, blank=True, null=True)
    country_name = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    zip = models.CharField(max_length=255, blank=True, null=True)
    country_code = models.CharField(max_length=40, blank=True, null=True)
    mobile = models.CharField(max_length=40, blank=True, null=True)
    balance = models.DecimalField(max_digits=28, decimal_places=8, default=0)
    password = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)

    # Status
    status = models.BooleanField(default=True, help_text="Active=True, Banned=False")
    ban_reason = models.CharField(max_length=255, blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    profile_complete = models.BooleanField(default=False)

    # KYC / verification
    kv = models.SmallIntegerField(default=0, choices=[(0, "Unverified"), (1, "Verified"), (2, "Pending")])
    ev = models.BooleanField(default=False)
    sv = models.BooleanField(default=False)
    kyc_data = models.TextField(blank=True, null=True)
    kyc_rejection_reason = models.CharField(max_length=255, blank=True, null=True)
    ver_code = models.CharField(max_length=40, blank=True, null=True)
    ver_code_send_at = models.DateTimeField(blank=True, null=True)

    # 2FA
    ts = models.BooleanField(default=False)
    tv = models.BooleanField(default=True)
    tsc = models.CharField(max_length=255, blank=True, null=True)

    # Profile
    title = models.TextField(blank=True)
    profile_image = models.TextField(blank=True)
    cover_image = models.TextField(blank=True)
    short_description = models.TextField(blank=True)
    long_description = models.TextField(blank=True)
    provider = models.CharField(max_length=255, blank=True, null=True)
    remember_token = models.CharField(max_length=255, blank=True, null=True)

    # Followers (users following this organizer)
    followers = models.ManyToManyField(
        User, through="UserOrganizer", related_name="following_organizers", blank=True
    )

    class Meta:
        db_table = "organizers"
        verbose_name = "Organizer"
        verbose_name_plural = "Organizers"
        ordering = ["-created_at"]

    def __str__(self):
        return self.organization_name

    @property
    def full_name(self):
        return f"{self.firstname or ''} {self.lastname or ''}".strip()


class Admin(BaseModel):
    """Backend admin user (separate table as per schema)."""
    name = models.CharField(max_length=40, blank=True, null=True)
    email = models.EmailField(max_length=40, unique=True)
    username = models.CharField(max_length=40, unique=True)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255)
    remember_token = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "admins"
        verbose_name = "Admin"

    def __str__(self):
        return self.email


class UserLogin(BaseModel):
    """Tracks user login history and geolocation."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="logins")
    organizer = models.ForeignKey(Organizer, on_delete=models.SET_NULL, null=True, blank=True, related_name="logins")
    ip = models.CharField(max_length=40, blank=True, null=True)
    city = models.CharField(max_length=40, blank=True, null=True)
    country = models.CharField(max_length=40, blank=True, null=True)
    country_code = models.CharField(max_length=40, blank=True, null=True)
    longitude = models.CharField(max_length=40, blank=True, null=True)
    latitude = models.CharField(max_length=40, blank=True, null=True)
    browser = models.CharField(max_length=40, blank=True, null=True)
    os = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        db_table = "user_logins"
        verbose_name = "User Login"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user or self.organizer} — {self.ip}"


class DeviceToken(BaseModel):
    """FCM push notification tokens."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="device_tokens")
    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE, null=True, blank=True, related_name="device_tokens")
    is_app = models.BooleanField(default=False)
    token = models.TextField()

    class Meta:
        db_table = "device_tokens"

    def __str__(self):
        return f"Token for {self.user or self.organizer}"


class UserOrganizer(BaseModel):
    """User ↔ Organizer follow relationship."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE)

    class Meta:
        db_table = "user_organizer"
        unique_together = [("user", "organizer")]

