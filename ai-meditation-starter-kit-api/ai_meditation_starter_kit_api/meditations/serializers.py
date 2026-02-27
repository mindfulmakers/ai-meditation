from __future__ import annotations

from config.serializers import BaseModelSerializer
from rest_framework import serializers

from .models import Meditation


class MeditationModelSerializer(BaseModelSerializer):
    id = serializers.SlugField(source="meditation_id")
    durationMs = serializers.IntegerField(source="duration_ms", min_value=0)  # noqa: N815
    timeline = serializers.JSONField()

    class Meta:
        model = Meditation
        fields = ["id", "title", "durationMs", "timeline"]


class MeditationSerializer(serializers.Serializer):
    id = serializers.SlugField()
    title = serializers.CharField()
    durationMs = serializers.IntegerField(min_value=0)  # noqa: N815
    timeline = serializers.JSONField()
