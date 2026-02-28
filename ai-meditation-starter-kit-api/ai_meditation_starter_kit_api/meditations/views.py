from __future__ import annotations

import json
import mimetypes
import os
from pathlib import Path, PurePosixPath

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Meditation, MeditationAudio, MeditationHaptic
from .serializers import MeditationModelSerializer, MeditationSerializer

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MEDITATIONS_DIRECTORY = WORKSPACE_ROOT / "meditations"
DEFAULT_AUDIO_DIRECTORY = WORKSPACE_ROOT / "audio"
DEFAULT_HAPTICS_DIRECTORY = WORKSPACE_ROOT / "haptics"
TRUTHY_VALUES = {"1", "true", "t", "yes", "y", "on"}
AUDIO_ROUTE_NAME = "meditations-audio"
HAPTICS_ROUTE_NAME = "meditations-haptics"


def _use_json_meditations() -> bool:
    return os.environ.get("MEDITATIONS_FROM_JSON_FILES", "1").strip().lower() in TRUTHY_VALUES


def _get_meditations_directory() -> Path:
    return Path(os.environ.get("MEDITATIONS_JSON_DIRECTORY", str(DEFAULT_MEDITATIONS_DIRECTORY)))


def _get_audio_directory() -> Path:
    return Path(os.environ.get("MEDITATIONS_AUDIO_DIRECTORY", str(DEFAULT_AUDIO_DIRECTORY)))


def _get_haptics_directory() -> Path:
    return Path(
        os.environ.get("MEDITATIONS_HAPTICS_DIRECTORY", str(DEFAULT_HAPTICS_DIRECTORY))
    )


def _normalize_audio_key(raw_key: str) -> str:
    normalized = str(PurePosixPath(raw_key.strip().lstrip("/")))
    if normalized in {"", "."}:
        msg = "Audio path is required."
        raise NotFound(msg)

    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        msg = "Audio path is invalid."
        raise NotFound(msg)

    return normalized


def _to_audio_serving_url(request, file_value: str) -> str:
    normalized_key = _normalize_audio_key(file_value)
    serving_key = (
        normalized_key.removeprefix("audio/")
        if normalized_key.startswith("audio/")
        else normalized_key
    )
    url = reverse(AUDIO_ROUTE_NAME, kwargs={"audio_path": serving_key})
    return request.build_absolute_uri(url)


def _to_haptics_serving_url(request, file_value: str) -> str:
    normalized_key = _normalize_audio_key(file_value)
    serving_key = (
        normalized_key.removeprefix("haptics/")
        if normalized_key.startswith("haptics/")
        else normalized_key
    )
    url = reverse(HAPTICS_ROUTE_NAME, kwargs={"haptic_path": serving_key})
    return request.build_absolute_uri(url)


def _rewrite_timeline_audio_urls(request, timeline: object) -> object:
    if not isinstance(timeline, list):
        return timeline

    updated_timeline: list[object] = []
    for entry in timeline:
        if not isinstance(entry, dict):
            updated_timeline.append(entry)
            continue

        kind = entry.get("kind")
        file_value = entry.get("file")
        if (
            kind == "wav"
            and isinstance(file_value, str)
            and file_value
            and not file_value.startswith("http://")
            and not file_value.startswith("https://")
        ):
            updated_entry = dict(entry)
            updated_entry["file"] = _to_audio_serving_url(request, file_value)
            updated_timeline.append(updated_entry)
            continue
        if (
            kind == "ahap"
            and isinstance(file_value, str)
            and file_value
            and not file_value.startswith("http://")
            and not file_value.startswith("https://")
        ):
            updated_entry = dict(entry)
            updated_entry["file"] = _to_haptics_serving_url(request, file_value)
            updated_timeline.append(updated_entry)
            continue

        updated_timeline.append(entry)

    return updated_timeline


def _rewrite_payload_audio_urls(request, payload: dict[str, object]) -> dict[str, object]:
    updated_payload = dict(payload)
    updated_payload["timeline"] = _rewrite_timeline_audio_urls(request, payload.get("timeline"))
    return updated_payload


def _resolve_json_audio_path(audio_key: str) -> Path:
    normalized_key = _normalize_audio_key(audio_key)
    relative_key = (
        normalized_key.removeprefix("audio/")
        if normalized_key.startswith("audio/")
        else normalized_key
    )
    audio_file_path = _get_audio_directory() / relative_key
    if not audio_file_path.exists() or not audio_file_path.is_file():
        msg = "Audio file not found."
        raise NotFound(msg)
    return audio_file_path


def _resolve_json_haptic_path(haptic_key: str) -> Path:
    normalized_key = _normalize_audio_key(haptic_key)
    relative_key = (
        normalized_key.removeprefix("haptics/")
        if normalized_key.startswith("haptics/")
        else normalized_key
    )
    haptic_file_path = _get_haptics_directory() / relative_key
    if not haptic_file_path.exists() or not haptic_file_path.is_file():
        msg = "Haptic file not found."
        raise NotFound(msg)
    return haptic_file_path


def _resolve_model_audio_asset(audio_key: str) -> MeditationAudio:
    normalized_key = _normalize_audio_key(audio_key)
    audio_asset = MeditationAudio.objects.filter(audio_key=normalized_key).first()
    if audio_asset is not None:
        return audio_asset

    prefixed_key = f"audio/{normalized_key}"
    if not normalized_key.startswith("audio/"):
        audio_asset = MeditationAudio.objects.filter(audio_key=prefixed_key).first()
    if audio_asset is not None:
        return audio_asset

    if normalized_key.startswith("audio/"):
        unprefixed_key = normalized_key.removeprefix("audio/")
        audio_asset = MeditationAudio.objects.filter(audio_key=unprefixed_key).first()
    if audio_asset is not None:
        return audio_asset

    msg = "Audio file not found."
    raise NotFound(msg)


def _resolve_model_haptic_asset(haptic_key: str):
    normalized_key = _normalize_audio_key(haptic_key)
    haptic_asset = MeditationHaptic.objects.filter(haptic_key=normalized_key).first()
    if haptic_asset is not None:
        return haptic_asset

    prefixed_key = f"haptics/{normalized_key}"
    if not normalized_key.startswith("haptics/"):
        haptic_asset = MeditationHaptic.objects.filter(haptic_key=prefixed_key).first()
    if haptic_asset is not None:
        return haptic_asset

    if normalized_key.startswith("haptics/"):
        unprefixed_key = normalized_key.removeprefix("haptics/")
        haptic_asset = MeditationHaptic.objects.filter(haptic_key=unprefixed_key).first()
    if haptic_asset is not None:
        return haptic_asset

    msg = "Haptic file not found."
    raise NotFound(msg)


class MeditationViewSet(viewsets.ViewSet):
    def list(self, request):
        if _use_json_meditations():
            meditations_directory = _get_meditations_directory()
            meditations_payload = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted(meditations_directory.glob("*.json"))
            ]
            serializer = MeditationSerializer(data=meditations_payload, many=True)
            serializer.is_valid(raise_exception=True)
            payload = [
                _rewrite_payload_audio_urls(request, dict(item))
                for item in serializer.validated_data
            ]
            return Response(payload)

        serializer = MeditationModelSerializer(Meditation.objects.all(), many=True)
        payload = [_rewrite_payload_audio_urls(request, dict(item)) for item in serializer.data]
        return Response(payload)

    def retrieve(self, request, pk=None):
        if not pk:
            msg = "Meditation id is required."
            raise NotFound(msg)

        if _use_json_meditations():
            meditations_directory = _get_meditations_directory()
            meditation_path = meditations_directory / f"{pk}.json"
            meditation_payload = None

            if meditation_path.exists():
                meditation_payload = json.loads(meditation_path.read_text(encoding="utf-8"))
            else:
                for path in sorted(meditations_directory.glob("*.json")):
                    parsed_payload = json.loads(path.read_text(encoding="utf-8"))
                    if parsed_payload.get("id") == pk:
                        meditation_payload = parsed_payload
                        break

            if meditation_payload is None:
                msg = "Meditation not found."
                raise NotFound(msg)

            serializer = MeditationSerializer(data=meditation_payload)
            serializer.is_valid(raise_exception=True)
            payload = _rewrite_payload_audio_urls(request, dict(serializer.validated_data))
            return Response(payload)

        meditation = get_object_or_404(Meditation, meditation_id=pk)
        serializer = MeditationModelSerializer(meditation)
        payload = _rewrite_payload_audio_urls(request, dict(serializer.data))
        return Response(payload)


class MeditationAudioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, audio_path: str) -> FileResponse:
        if _use_json_meditations():
            file_path = _resolve_json_audio_path(audio_path)
            content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            return FileResponse(file_path.open("rb"), content_type=content_type)

        audio_asset = _resolve_model_audio_asset(audio_path)
        content_type = mimetypes.guess_type(audio_asset.file.name)[0] or "application/octet-stream"
        return FileResponse(audio_asset.file.open("rb"), content_type=content_type)


class MeditationHapticView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, haptic_path: str) -> FileResponse:
        if _use_json_meditations():
            file_path = _resolve_json_haptic_path(haptic_path)
            content_type = mimetypes.guess_type(file_path.name)[0] or "application/json"
            return FileResponse(file_path.open("rb"), content_type=content_type)

        haptic_asset = _resolve_model_haptic_asset(haptic_path)
        content_type = mimetypes.guess_type(haptic_asset.file.name)[0] or "application/json"
        return FileResponse(haptic_asset.file.open("rb"), content_type=content_type)
