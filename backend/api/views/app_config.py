from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.advertisements.models import AdRewardRequirement, AdSetting
from apps.notifications.models import Announcement
from apps.system_settings.models import get_setting

from api.permissions import IsActiveUser


class AppConfigView(APIView):
    """Bootstrap configuration for the Flutter app. Server-enforced settings only."""

    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request):
        ads = AdSetting.load()
        ai_rewards = AdRewardRequirement.objects.filter(purpose=AdRewardRequirement.PURPOSE_AI).first()
        export_rewards = AdRewardRequirement.objects.filter(purpose=AdRewardRequirement.PURPOSE_EXPORT).first()
        announcements = Announcement.objects.filter(is_active=True)[:5]
        from django.utils import timezone

        return Response({
            "app": {
                "name": get_setting("app", "name", "CV Maker"),
                "min_app_version": get_setting("app", "min_app_version", "1.0.0"),
                "force_update": bool(get_setting("app", "force_update", False)),
                "support_email": get_setting("app", "support_email", ""),
            },
            "maintenance": get_setting("maintenance", default={"enabled": False, "message": ""}),
            "ads": {
                "app_open_enabled": ads.app_open_enabled,
                "app_open_skip_first_launch": ads.app_open_skip_first_launch,
                "app_open_max_per_day": ads.app_open_max_per_day,
                "native_dashboard_enabled": ads.native_dashboard_enabled,
                "native_gallery_enabled": ads.native_gallery_enabled,
                "banner_enabled": ads.banner_enabled,
                "test_mode": ads.test_mode,
                "ad_unit_ids": ads.ad_unit_ids,
            },
            "rewards": {
                "rewarded_enabled": ads.rewarded_enabled,
                "ai": ai_rewards.required_ads if ai_rewards else 5,
                "export": export_rewards.required_ads if export_rewards else 5,
            },
            "announcements": [
                {"id": a.pk, "title": a.title, "body": a.body, "created_at": a.created_at} for a in announcements
            ],
        })
