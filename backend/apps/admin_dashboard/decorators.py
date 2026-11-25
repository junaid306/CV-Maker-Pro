from functools import wraps

from django.contrib.admin.views.decorators import staff_member_required


def admin_required(view):
    return staff_member_required(view, login_url="panel_login")


def audit(action):
    """Decorator factory: log admin activity for the wrapped view."""

    def decorator(view):
        @wraps(view)
        @admin_required(view)
        def wrapped(request, *args, **kwargs):
            from apps.system_settings.models import AdminActivityLog

            response = view(request, *args, **kwargs)
            try:
                AdminActivityLog.objects.create(
                    admin=request.user,
                    action=action.format(**kwargs) if "{" in action else action,
                    target=str(kwargs.get("pk", "")),
                    ip=request.META.get("REMOTE_ADDR"),
                )
            except Exception:
                pass
            return response

        return wrapped

    return decorator
