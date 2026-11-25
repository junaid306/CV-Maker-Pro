from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.shared_assets.models import SharedAsset, UserAsset
from apps.shared_assets.services import validate_image_upload

from api.permissions import IsActiveUser
from api.serializers.assets import SharedAssetSerializer, UserAssetSerializer


class UserAssetUploadView(APIView):
    permission_classes = (IsAuthenticated, IsActiveUser)

    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response({"detail": "file is required"}, status=400)
        validate_image_upload(uploaded)
        UserAsset.objects.create(user=request.user, file=uploaded)
        asset = UserAsset.objects.filter(user=request.user).latest("uploaded_at")
        return Response(UserAssetSerializer(asset).data, status=201)

    def get(self, request):
        return Response(UserAssetSerializer(UserAsset.objects.filter(user=request.user)[:10], many=True).data)


class SharedAssetsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(SharedAssetSerializer(SharedAsset.objects.filter(is_active=True), many=True).data)
