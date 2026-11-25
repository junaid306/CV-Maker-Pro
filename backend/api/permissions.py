from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    message = "Account is inactive or blocked."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_valid_session_user)


class IsNotGuest(BasePermission):
    message = "This action requires a registered account."

    def has_permission(self, request, view):
        return request.user.is_authenticated and not request.user.is_guest
