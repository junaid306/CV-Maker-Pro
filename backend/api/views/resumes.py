from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.exports.models import PdfExport
from apps.exports.services import ExportLocked, ExportRuntimeError, export_resume
from apps.resumes.models import Resume, ResumeSection, ResumeVersion
from apps.resumes.services import duplicate_resume, restore_version, snapshot_resume

from api.permissions import IsActiveUser
from api.serializers.resumes import ResumeSerializer, ResumeVersionSerializer, ResumeWriteSerializer


def user_resume(request, pk):
    return get_object_or_404(Resume, pk=pk, user=request.user, is_deleted=False)


class ResumeListCreateView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request):
        resumes = Resume.objects.filter(user=request.user, is_deleted=False)
        return Response(ResumeSerializer(resumes, many=True).data)

    def post(self, request):
        serializer = ResumeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = dict(serializer.validated_data)
        sections_data = validated.pop("sections", [])
        template = validated.pop("template", None)
        template_version_id = validated.pop("template_version", None)
        if template is None and template_version_id:
            from apps.templates_manager.models import TemplateVersion

            version = get_object_or_404(TemplateVersion, pk=template_version_id)
            template = version.template
            validated["template_version_id"] = template_version_id
        resume = Resume.objects.create(user=request.user, template=template, **validated)
        for order, section in enumerate(sections_data):
            section.pop("id", None)
            ResumeSection.objects.create(resume=resume, order=section.pop("order", order), **section)
        if template:
            from apps.templates_manager.models import Template

            Template.objects.filter(pk=template.pk).update(usage_count=F("usage_count") + 1)
        return Response(ResumeSerializer(resume).data, status=status.HTTP_201_CREATED)


class ResumeDetailView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request, pk):
        return Response(ResumeSerializer(user_resume(request, pk)).data)

    def put(self, request, pk):
        resume = user_resume(request, pk)
        was_autosave = bool(request.data.get("autosave", False))
        serializer = ResumeWriteSerializer(resume, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated = dict(serializer.validated_data)
        sections_data = validated.pop("sections", []) or []
        if "template_version" in validated:
            version_id = validated.pop("template_version")
            if version_id:
                from apps.templates_manager.models import TemplateVersion

                version = get_object_or_404(TemplateVersion, pk=version_id)
                resume.template = version.template
                resume.template_version_id = version_id
        if not was_autosave:
            snapshot_resume(resume, note="snapshot before save")
        for field, value in validated.items():
            setattr(resume, field, value)
        resume.autosaved_at = timezone.now()
        resume.save()

        if sections_data:
            keep_ids = []
            for order, section in enumerate(sections_data):
                section_id = section.pop("id", None)
                if section_id:
                    existing = resume.sections.filter(pk=section_id, resume=resume).first()
                    if existing:
                        for field, value in section.items():
                            setattr(existing, field, value)
                        existing.save()
                        keep_ids.append(existing.pk)
                        continue
                section.pop("order", None)
                created = ResumeSection.objects.create(resume=resume, order=section.get("order", order), **section)
                keep_ids.append(created.pk)
            resume.sections.exclude(pk__in=keep_ids).delete()
        return Response(ResumeSerializer(resume).data)

    def delete(self, request, pk):
        resume = user_resume(request, pk)
        if request.query_params.get("hard") != "true":
            resume.is_deleted = True
            resume.deleted_at = timezone.now()
            resume.save(update_fields=["is_deleted", "deleted_at"])
        else:
            resume.delete()
        return Response({"detail": "ok"})


class ResumeDuplicateView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def post(self, request, pk):
        clone = duplicate_resume(user_resume(request, pk))
        return Response(ResumeSerializer(clone).data, status=status.HTTP_201_CREATED)


class ResumeVersionsView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request, pk):
        resume = user_resume(request, pk)
        return Response(ResumeVersionSerializer(resume.versions.all(), many=True).data)

    def post(self, request, pk):
        resume = user_resume(request, pk)
        version = get_object_or_404(ResumeVersion, pk=request.data.get("version_id"), resume=resume)
        restore_version(resume, version)
        return Response(ResumeSerializer(resume).data)


class ResumeExportView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def post(self, request, pk):
        resume = user_resume(request, pk)
        try:
            export = export_resume(resume, page_size=request.data.get("page_size"))
        except ExportLocked as exc:
            return Response({"detail": str(exc), "reason": "locked"}, status=402)
        except ExportRuntimeError as exc:
            return Response({"detail": str(exc), "credit_released": True}, status=500)
        return Response({
            "id": export.pk, "status": export.status, "page_size": export.page_size,
            "download": export.file.url if export.file else None,
            "created_at": export.created_at,
        }, status=status.HTTP_201_CREATED)

    def get(self, request, pk):
        resume = user_resume(request, pk)
        exports = PdfExport.objects.filter(resume=resume).order_by("-created_at")
        return Response([
            {"id": e.pk, "status": e.status, "page_size": e.page_size,
             "file": e.file.url if e.file else None, "created_at": e.created_at} for e in exports
        ])
