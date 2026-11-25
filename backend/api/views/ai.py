from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_tools import services as ai_services
from apps.ai_tools.models import AiGeneration, FEATURE_KEYS
from apps.rewards.models import AiGenerationCredit
from apps.rewards.services import open_reward_session

from api.permissions import IsActiveUser
from api.serializers.ai import AiGenerateInputSerializer, AiRewardsSessionInputSerializer


class AiConfigView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request):
        features = []
        for key in FEATURE_KEYS:
            setting = ai_services.get_feature_setting(key)
            enabled = bool(setting and setting.enabled)
            features.append({
                "key": key, "enabled": enabled,
                "required_ads": ai_services.required_ads(key),
                "has_credit": AiGenerationCredit.objects.filter(
                    user=request.user, feature__in=[key, ""]
                ).exists() if enabled else False,
                "daily_limit": setting.daily_limit if setting else 10,
            })
        return Response({"features": features})


class AiRewardsSessionView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def post(self, request):
        serializer = AiRewardsSessionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purpose = serializer.validated_data["purpose"]
        feature = serializer.validated_data.get("feature") or ""
        if purpose == "ai":
            if not ai_services.is_feature_enabled(feature):
                return Response({"detail": "This AI feature is disabled."}, status=400)
        try:
            session = open_reward_session(request.user, purpose, feature or None)
        except PermissionError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({
            "session_id": session.pk, "purpose": session.purpose, "feature": session.feature,
            "required_count": session.required_count, "verified_count": session.verified_count,
            "status": session.status,
        })


class AiRewardsProgressView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request):
        sessions = []
        session_id = request.query_params.get("session")
        query = request.user.ad_sessions.all()
        if session_id:
            query = query.filter(pk=session_id)
        for session in query.order_by("-created_at")[:10]:
            sessions.append({
                "session_id": session.pk, "purpose": session.purpose, "feature": session.feature,
                "required_count": session.required_count, "verified_count": session.verified_count,
                "status": session.status,
            })
        return Response({"sessions": sessions})


class AiGenerateView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def post(self, request):
        serializer = AiGenerateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            generation = ai_services.run_generation(
                request.user, data["feature"], input_text=data.get("input", ""),
                role=data.get("role", ""), idempotency_key=data.get("idempotency_key") or None,
            )
        except ai_services.FeatureDisabled as exc:
            return Response({"detail": str(exc)}, status=400)
        except ai_services.DailyLimitReached as exc:
            return Response({"detail": str(exc)}, status=429)
        except ai_services.AiRuntimeError as exc:
            return Response({"detail": str(exc)}, status=402)
        return Response({
            "id": generation.pk, "feature": generation.feature, "status": generation.status,
            "output": generation.output_text, "provider": generation.provider, "error": generation.error,
        })


class AiGenerationDetailView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request, pk):
        generation = get_object_or_404(AiGeneration, pk=pk, user=request.user)
        return Response({
            "id": generation.pk, "feature": generation.feature, "status": generation.status,
            "output": generation.output_text, "provider": generation.provider, "error": generation.error,
        })
