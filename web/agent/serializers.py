from __future__ import annotations

from rest_framework import serializers


class LiveKitRoomTokenSerializer(serializers.Serializer):
    graph_name = serializers.CharField(required=True)
    livekit_dispatch_agent_name = serializers.CharField(required=True)
    thread_id = serializers.CharField(required=False, allow_null=True, default=None)
