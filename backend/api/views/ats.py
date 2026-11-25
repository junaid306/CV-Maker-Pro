from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ats_checker.services import analyze_resume, analyze_text
from apps.system_settings.models import get_setting
from apps.ats_checker.services import analyze_resume

from api.permissions import IsActiveUser
from api.serializers.ats import AtsAnalysisSerializer, AtsResumeAnalyzeSerializer, AtsTextAnalyzeSerializer


class AtsAnalyzeView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def post(self, request):
        ats_settings = get_setting("ats")
        if not ats_settings.get("basic_enabled", True):
            return Response({"detail": "Basic ATS checking is disabled by the administrator."}, status=400)
        serializer = AtsTextAnalyzeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        analysis = analyze_text(
            request.user, data["text"], job_description=data.get("job_description") or None
        )
        return Response(AtsAnalysisSerializer(analysis).data)


class AtsJobMatchView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def post(self, request):
        ats_settings = get_setting("ats")
        if not ats_settings.get("job_match_enabled", True):
            return Response({"detail": "Job matching is disabled by the administrator."}, status=400)
        serializer = AtsResumeAnalyzeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        from apps.resumes.models import Resume

        resume = get_object_or_404(Resume, pk=data["resume"], user=request.user)
        analysis = analyze_resume(resume, job_description=data.get("job_description") or None)
        return Response(AtsAnalysisSerializer(analysis).data)


class AtsAnalysisDetailView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request, pk):
        from apps.ats_checker.models import AtsAnalysis

        analysis = get_object_or_404(AtsAnalysis, pk=pk, user=request.user)
        return Response(AtsAnalysisSerializer(analysis).data)
