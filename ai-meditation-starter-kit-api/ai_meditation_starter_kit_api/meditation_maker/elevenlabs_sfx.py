from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Any

import requests

from .config import get_elevenlabs_api_key, load_project_env
from .types import SFXResult, coerce_sfx_request

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .types import SFXRequest

_ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


def _output_format_to_elevenlabs(value: str) -> str:
    mapping = {
        "mp3": "mp3_44100_128",
        "ogg": "ogg_44100_128",
        # pcm_44100 requires Pro tier, so request MP3 and convert to WAV locally.
        "wav": "mp3_44100_128",
    }
    return mapping[value]


def _output_format_to_mime_type(value: str) -> str:
    mapping = {
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "wav": "audio/wav",
    }
    return mapping[value]


def _mp3_to_wav(mp3_bytes: bytes) -> bytes:
    """Convert MP3 bytes to WAV using ffmpeg."""
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            "pipe:0",
            "-ar",
            "44100",
            "-ac",
            "1",
            "-sample_fmt",
            "s16",
            "-f",
            "wav",
            "pipe:1",
        ],
        input=mp3_bytes,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        msg = f"ffmpeg MP3-to-WAV conversion failed: {result.stderr.decode()}"
        raise RuntimeError(msg)
    return result.stdout


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
        audio_bytes = _mp3_to_wav(audio_bytes)

    return SFXResult(
        success=True,
        provider="elevenlabs",
        audioBytes=audio_bytes,
        mimeType=_output_format_to_mime_type(normalized_request.outputFormat),
        raw=None,
    )
