import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import validate_email
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        validate_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)

    def create_guest(self):
        suffix = uuid.uuid4().hex[:10]
        user = self.model(
            email=f"guest_{suffix}@guest.local",
            name="Guest",
            is_guest=True,
            is_active=True,
            guest_code=uuid.uuid4().hex,
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=120, blank=True)
    is_guest = models.BooleanField(default=False, db_index=True)
    # Server-side identity token for guests; never used as the only secret but
    # lets us find a guest record across devices after re-login.
    guest_code = models.CharField(max_length=64, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    upgraded_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        indexes = [
            models.Index(fields=["is_guest", "is_active"]),
        ]

    def __str__(self):
        return self.email

    @property
    def is_valid_session_user(self):
        return self.is_active and not self.is_blocked

    def get_full_name(self):
        return self.name


class PasswordResetCode(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="reset_codes")
    code = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()
