"""Guest upgrade and account lifecycle business logic."""
from django.db import transaction
from django.utils import timezone


@transaction.atomic
def upgrade_guest(user, email, password, name=""):
    """Convert a guest account into a registered account atomically.

    Because the guest uses the same user row, CVs, reward progress, credits,
    assets and settings are preserved automatically. Verified reward sessions
    are kept; their transactions stay unique so rewards cannot be re-claimed.
    """
    from .models import User

    email = email.strip().lower()
    if User.objects.filter(email=email).exclude(pk=user.pk).exists():
        raise ValueError("An account with this email already exists.")
    if not user.is_guest:
        raise ValueError("Account is already registered.")

    user.email = email
    user.name = name or user.name
    user.set_password(password)
    user.is_guest = False
    user.upgraded_at = timezone.now()
    user.guest_code = ""
    user.save()
    return user
