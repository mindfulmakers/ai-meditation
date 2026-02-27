from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import timedelta

import livekit.api as livekit_api
from django.conf import settings
from payment.billing import consume_daily_user_quota
from payment.permissions import HasActiveSubscription
from rest_framework import permissions, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .serializers import LiveKitRoomTokenSerializer

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated, HasActiveSubscription])
def create_livekit_room_token(request):
    """Create a LiveKit room token for the authenticated user."""

    input_serializer = LiveKitRoomTokenSerializer(data=request.data)
    input_serializer.is_valid(raise_exception=True)

    api_key = os.environ.get("LIVEKIT_API_KEY")
    api_secret = os.environ.get("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        raise serializers.ValidationError(
            {"detail": "LiveKit credentials not configured"}
        )

    consume_daily_user_quota(
        user=request.user,
        quota_name="livekit_room_tokens",
        max_daily_actions=settings.BILLING_MAX_LIVEKIT_TOKENS_PER_DAY,
        detail="Daily agent usage limit reached for your account.",
    )

    graph_name = input_serializer.validated_data["graph_name"]
    livekit_dispatch_agent_name = input_serializer.validated_data[
        "livekit_dispatch_agent_name"
    ]

    room_name = f"room-{uuid.uuid4().hex[:12]}"

    thread_id = input_serializer.validated_data.get("thread_id")
    agent_metadata = {"graph_name": graph_name}
    if thread_id:
        agent_metadata["thread_id"] = thread_id

    logger.info(
        f"[LiveKit Token] user={request.user.email} graph={graph_name} agent={livekit_dispatch_agent_name} thread_id={thread_id} metadata={json.dumps(agent_metadata)}"
    )

    token = (
        livekit_api.AccessToken(api_key=api_key, api_secret=api_secret)
        .with_identity(request.user.email)
        .with_name(f"{request.user.first_name} {request.user.last_name}".strip())
        .with_grants(
            livekit_api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_room_config(
            livekit_api.RoomConfiguration(
                agents=[
                    livekit_api.RoomAgentDispatch(
                        agent_name=livekit_dispatch_agent_name,
                        metadata=json.dumps(agent_metadata),
                    )
                ],
            )
        )
        .with_ttl(timedelta(hours=1))
        .to_jwt()
    )

    return Response({"token": token, "room_name": room_name})
