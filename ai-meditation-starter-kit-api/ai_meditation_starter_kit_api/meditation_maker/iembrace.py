from __future__ import annotations

import json
from typing import Any, Mapping

import requests

from .config import get_api_base_url, get_user_email, load_project_env
from .types import TTSRequest, TTSResult, coerce_tts_request


def _unwrap_lambda_payload(payload: Any) -> Any:
    if (
        isinstance(payload, dict)
        and payload.get("statusCode") == 200
        and isinstance(payload.get("body"), str)
    ):
        try:
            return json.loads(payload["body"])
        except json.JSONDecodeError:
            return payload

    if isinstance(payload, dict) and isinstance(payload.get("body"), str):
        try:
            return json.loads(payload["body"])
        except json.JSONDecodeError:
            return payload

    return payload


def generate_personalized_meditation(
    mood: str,
    goal: str,
    message_to_loved_one: str,
    *,
    timeout: int = 30,
) -> str:
    """Generate a personalized meditation script from the iEmbrace API."""
    load_project_env()

    base_url = get_api_base_url()
    user_email = get_user_email()

    url = f"{base_url}/personalization"
    headers = {
        "Content-Type": "application/json",
        "X-User-Email": user_email,
    }
    body = {
        "mood": mood,
        "goal": goal,
        "message_to_loved_one": message_to_loved_one,
    }

    response = requests.post(url, headers=headers, json=body, timeout=timeout)
    response.raise_for_status()

    payload = _unwrap_lambda_payload(response.json())
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected response payload type: {type(payload)}")

    script = payload.get("script")
    if not script:
        raise RuntimeError(f"API returned no script. Payload: {json.dumps(payload)}")

    return str(script)


def generate_tts_audio_iembrace(
    request: TTSRequest | Mapping[str, Any],
    *,
    timeout: int = 60,
) -> TTSResult:
    """Generate meditation TTS through iEmbrace using the shared `TTSRequest` shape."""
    load_project_env()

    normalized_request = coerce_tts_request(request)
    base_url = get_api_base_url()
    user_email = get_user_email()

    url = f"{base_url}/personalization/tts_service"
    headers = {
        "Content-Type": "application/json",
        "X-User-Email": user_email,
    }

    response = requests.post(
        url,
        headers=headers,
        json=normalized_request.as_payload(),
        timeout=timeout,
    )
    response.raise_for_status()

    payload = _unwrap_lambda_payload(response.json())
    if not isinstance(payload, dict):
        raise RuntimeError(f"Unexpected response payload type: {type(payload)}")

    if payload.get("success") is not True:
        raise RuntimeError(
            f"TTS API did not return success. Payload: {json.dumps(payload)}"
        )

    audio_url = payload.get("audioUrl")
    if not audio_url:
        raise RuntimeError(
            f"TTS API returned no audioUrl. Payload: {json.dumps(payload)}"
        )

    mime_type = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
    }[normalized_request.outputFormat]

    return TTSResult(
        success=True,
        provider="iembrace",
        audioUrl=str(audio_url),
        audioBytes=None,
        mimeType=mime_type,
        voiceId=None,
        raw=payload,
    )
