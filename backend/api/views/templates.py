from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.templates_manager.models import FavoriteTemplate, Template, TemplateCategory

from api.permissions import IsActiveUser
from api.serializers.templates import TemplateCategorySerializer, TemplateSerializer


class TemplateListView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request):
        queryset = Template.objects.filter(status=Template.STATUS_PUBLISHED).select_related("category", "current_version")
        category_slug = request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        from rest_framework.pagination import PageNumberPagination

        pagination = PageNumberPagination()
        page = pagination.paginate_queryset(queryset, request)
        return pagination.get_paginated_response(TemplateSerializer(page, many=True, context={"request": request}).data)


class TemplateListViewMeta(APIView):
    """Categories for the gallery filter bar."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(TemplateCategorySerializer(TemplateCategory.objects.filter(is_active=True), many=True).data)


class TemplateDetailView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def get(self, request, pk):
        template = get_object_or_404(
            Template.objects.select_related("category", "current_version"),
            pk=pk, status=Template.STATUS_PUBLISHED,
        )
        return Response(TemplateSerializer(template, context={"request": request}).data)


class TemplateFavoriteView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def post(self, request, pk):
        template = get_object_or_404(Template, pk=pk, status=Template.STATUS_PUBLISHED)
        favorite, created = FavoriteTemplate.objects.get_or_create(user=request.user, template=template)
        if not created:
            favorite.delete()
        return Response({"is_favorite": created})
