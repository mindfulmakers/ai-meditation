from __future__ import annotations

import io
import re
import wave
from typing import Any, Mapping

import requests

from .config import (
    get_elevenlabs_api_key,
    get_elevenlabs_voice_id,
    load_project_env,
)
from .types import TTSRequest, TTSResult, coerce_tts_request

_ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
_ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"
_PAUSE_PATTERN = re.compile(r"\[\s*(\d+(?:\.\d+)?)\s*s\s*\]")


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


def _pause_seconds_to_break_tags(seconds: float) -> str:
    # ElevenLabs break tags support up to 3 seconds per tag.
    max_chunk_seconds = 3.0
    remaining = max(seconds, 0.0)
    chunks: list[str] = []

    while remaining > 0:
        chunk = min(remaining, max_chunk_seconds)
        chunks.append(f'<break time="{chunk:g}s" />')
        remaining -= chunk

    return " ".join(chunks)


def _convert_iembrace_pause_tokens(text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        seconds = float(match.group(1))
        return _pause_seconds_to_break_tags(seconds)

    return _PAUSE_PATTERN.sub(_replace, text)


def generate_tts_audio_elevenlabs(
    request: TTSRequest | Mapping[str, Any],
    *,
    timeout: int = 60,
    voice_id: str | None = None,
) -> TTSResult:
    """Generate meditation TTS with ElevenLabs from the same request shape as iEmbrace.

    Pause tokens like ``[2s]`` and ``[30s]`` in `request.text` are converted to
    ElevenLabs-compatible break tags before synthesis.
    """
    load_project_env()

    normalized_request = coerce_tts_request(request)
    chosen_voice_id = voice_id or get_elevenlabs_voice_id()
    api_key = get_elevenlabs_api_key()
    output_format = _output_format_to_elevenlabs(normalized_request.outputFormat)

    url = f"{_ELEVENLABS_BASE_URL}/text-to-speech/{chosen_voice_id}"
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    params = {"output_format": output_format}
    body = {
        "text": _convert_iembrace_pause_tokens(normalized_request.text),
        "model_id": _ELEVENLABS_MODEL_ID,
    }

    response = requests.post(
        url,
        headers=headers,
        params=params,
        json=body,
        timeout=timeout,
    )
    response.raise_for_status()

    audio_bytes = response.content
    if normalized_request.outputFormat == "wav":
        audio_bytes = _pcm16le_to_wav(audio_bytes)

    return TTSResult(
        success=True,
        provider="elevenlabs",
        audioUrl=None,
        audioBytes=audio_bytes,
        mimeType=_output_format_to_mime_type(normalized_request.outputFormat),
        voiceId=chosen_voice_id,
        raw=None,
    )
