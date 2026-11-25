from rest_framework import serializers


class AiGenerateInputSerializer(serializers.Serializer):
    feature = serializers.CharField()
    input = serializers.CharField(required=False, allow_blank=True, default="")
    role = serializers.CharField(required=False, allow_blank=True, default="")
    resume = serializers.IntegerField(required=False, allow_null=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, default="")


class AiGenerateOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    feature = serializers.CharField()
    status = serializers.CharField()
    output = serializers.CharField()
    provider = serializers.CharField()
    error = serializers.CharField()


class AiRewardsSessionInputSerializer(serializers.Serializer):
    purpose = serializers.ChoiceField(choices=("ai", "export"))
    feature = serializers.CharField(required=False, allow_blank=True, default="")


class SsvInputSerializer(serializers.Serializer):
    """Forwarded AdMob SSV callback. `query` is the raw callback query string."""

    query = serializers.CharField()
    transaction_id = serializers.CharField(required=False, allow_blank=True, default="")
    purpose = serializers.ChoiceField(choices=("ai", "export"), required=False, default="ai")
    session = serializers.IntegerField(required=False, allow_null=True, default=None)
