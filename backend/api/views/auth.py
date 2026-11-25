from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import PasswordResetCode, User
from apps.accounts.services import upgrade_guest
from apps.system_settings.models import get_setting

from api.permissions import IsActiveUser
from api.serializers.auth import (
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UpgradeGuestSerializer,
    UserSerializer,
)


def token_pair_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class TokenRefreshView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh)
        except Exception:  # noqa: BLE001
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"access": str(token.access_token), "refresh": str(token)})


class RegisterView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"user": UserSerializer(user).data, **token_pair_for(user)}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"user": UserSerializer(serializer.validated_data["user"]).data, **token_pair_for(serializer.validated_data["user"])})


class GuestLoginView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        maintenance = get_setting("maintenance")
        if maintenance.get("enabled") and not request.user.is_staff:
            return Response({"detail": maintenance.get("message", "Maintenance mode is on.")}, status=503)
        user = User.objects.create_guest()
        return Response({"user": UserSerializer(user).data, **token_pair_for(user)}, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response({"detail": "ok"})


class MeView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        name = request.data.get("name")
        if name is not None:
            request.user.name = str(name)[:120]
            request.user.save(update_fields=["name"])
        return Response(UserSerializer(request.user).data)


class UpgradeGuestView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = UpgradeGuestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = upgrade_guest(request.user, serializer.validated_data["email"],
                                 serializer.validated_data["password"], serializer.validated_data["name"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"user": UserSerializer(user).data, **token_pair_for(user)})


class ForgotPasswordView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        user = User.objects.filter(email=email, is_guest=False).first()
        if user:
            code = PasswordResetCode.objects.create(
                user=user, code=timezone.now().strftime("%f%H%M%S"), expires_at=timezone.now() + timezone.timedelta(minutes=30)
            )
            user.reset_codes.all().exclude(pk=code.pk).update(used_at=timezone.now())
        # Always return ok to avoid user enumeration; delivery is via the admin-configured email backend.
        return Response({"detail": "If the email exists, a reset code has been sent."})
