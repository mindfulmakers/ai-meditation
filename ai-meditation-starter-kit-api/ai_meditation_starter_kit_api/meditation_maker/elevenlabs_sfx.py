from __future__ import annotations

import io
import wave
from typing import Any, Mapping

import requests

from .config import get_elevenlabs_api_key, load_project_env
from .types import SFXRequest, SFXResult, coerce_sfx_request

_ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


def _output_format_to_elevenlabs(value: str) -> str:
    mapping = {
        "mp3": "mp3_44100_128",
        "ogg": "ogg_44100_128",
        "wav": "pcm_44100",
    }
    return mapping[value]


def _output_format_to_mime_type(value: str) -> str:
    mapping = {
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "wav": "audio/wav",
    }
    return mapping[value]


def _pcm16le_to_wav(pcm_bytes: bytes, *, sample_rate: int = 44100) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return buffer.getvalue()


def generate_sfx_audio_elevenlabs(
    request: SFXRequest | Mapping[str, Any],
    *,
    timeout: int = 60,
) -> SFXResult:
    """Generate a meditation sound effect clip with ElevenLabs."""
    load_project_env()

    normalized_request = coerce_sfx_request(request)
    api_key = get_elevenlabs_api_key()
    output_format = _output_format_to_elevenlabs(normalized_request.outputFormat)

    url = f"{_ELEVENLABS_BASE_URL}/sound-generation"
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    params = {"output_format": output_format}

    response = requests.post(
        url,
        headers=headers,
        params=params,
        json=normalized_request.as_payload(),
        timeout=timeout,
    )
    response.raise_for_status()

    audio_bytes = response.content
    if normalized_request.outputFormat == "wav":
        audio_bytes = _pcm16le_to_wav(audio_bytes)

    return SFXResult(
        success=True,
        provider="elevenlabs",
        audioBytes=audio_bytes,
        mimeType=_output_format_to_mime_type(normalized_request.outputFormat),
        raw=None,
    )
