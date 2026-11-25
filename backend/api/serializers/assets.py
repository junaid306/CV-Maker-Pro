from rest_framework import serializers

from apps.shared_assets.models import SharedAsset, UserAsset


class UserAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAsset
        fields = ("id", "file", "thumbnail", "uploaded_at")


class SharedAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedAsset
        fields = ("id", "key", "kind", "file", "is_active")
