import logging

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.advertisements.verification import verify_ssv_query
from apps.rewards.models import RewardFraudLog
from apps.rewards.services import open_reward_session, record_verified_reward

from api.permissions import IsActiveUser
from api.serializers.ai import SsvInputSerializer

logger = logging.getLogger(__name__)


class SsvCallbackView(APIView):
    """AdMob SSV callback receiver (GET) and forwarded-callback endpoint (POST).

    Rewards are granted only after signature verification; duplicate
    transaction ids are rejected and logged.
    """

    permission_classes = (AllowAny,)

    def get(self, request):
        query_string = request.META.get("QUERY_STRING", "")
        signature = request.query_params.get("signature", "")
        key_id = request.query_params.get("key_id", "")
        transaction_id = request.query_params.get("transaction_id", "")
        if not verify_ssv_query(query_string, signature, key_id):
            RewardFraudLog.objects.create(
                transaction_id=transaction_id, reason="invalid_signature",
                detail={k: v for k, v in request.query_params.items()},
            )
            return Response({"detail": "invalid signature"}, status=400)
        params = dict(request.query_params.items())
        session = self._match_session(params)
        if session is None:
            return Response({"detail": "no open reward session"}, status=200)
        _record(session, transaction_id, params)
        return Response({"detail": "reward recorded"})

    def post(self, request):
        serializer = SsvInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not verify_ssv_query(data["query"], self._signature_from_query(data["query"]),
                                self._param_from_query(data["query"], "key_id")):
            RewardFraudLog.objects.create(transaction_id=data.get("transaction_id"), reason="invalid_signature")
            return Response({"detail": "invalid signature"}, status=400)
        session = None
        if data.get("session"):
            session = request.user.ad_sessions.filter(pk=data["session"], status="open").first()
        if session is None:
            session = request.user.ad_sessions.filter(status="open").order_by("-created_at").first()
        if session is None:
            return Response({"detail": "no open reward session"}, status=400)
        _record(session, data.get("transaction_id") or self._param_from_query(data["query"], "transaction_id"), {})
        return Response({"detail": "reward recorded"})

    def _match_session(self, params):
        from apps.advertisements.models import AdSession

        user_key = params.get("user_id") or params.get("userId")
        return AdSession.objects.filter(user__pk=user_key, status=AdSession.STATUS_OPEN).order_by("-created_at").first() if user_key else None

    def _signature_from_query(self, query):
        import urllib.parse

        params = urllib.parse.parse_qs(query, keep_blank_values=True)
        return params.get("signature", [""])[0]

    def _param_from_query(self, query, name):
        import urllib.parse

        params = urllib.parse.parse_qs(query, keep_blank_values=True)
        return params.get(name, [""])[0]


def _record(session, transaction_id, raw_params):
    if not transaction_id:
        RewardFraudLog.objects.create(user_id=session.user_id, reason="missing_transaction_id")
        return
    record_verified_reward(session, transaction_id, raw_params=raw_params)
