from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

_ALLOWED_OUTPUT_FORMATS = {"wav", "mp3", "ogg"}


@dataclass(slots=True)
class TTSRequest:
    """Input payload matching the iEmbrace TTS service shape."""

    text: str
    languageCode: str = "en-US"
    outputFormat: str = "wav"

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("text must not be empty")

        if self.outputFormat not in _ALLOWED_OUTPUT_FORMATS:
            raise ValueError("outputFormat must be one of: wav, mp3, ogg")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> TTSRequest:
        return cls(
            text=str(payload.get("text", "")),
            languageCode=str(payload.get("languageCode", "en-US")),
            outputFormat=str(payload.get("outputFormat", "wav")),
        )

    def as_payload(self) -> dict[str, str]:
        return {
            "text": self.text,
            "languageCode": self.languageCode,
            "outputFormat": self.outputFormat,
        }


@dataclass(slots=True)
class TTSResult:
    """Normalized TTS result that can represent both iEmbrace and ElevenLabs output."""

    success: bool
    provider: str
    audioUrl: str | None = None
    audioBytes: bytes | None = None
    mimeType: str | None = None
    voiceId: str | None = None
    raw: dict[str, Any] | None = None


def coerce_tts_request(request: TTSRequest | Mapping[str, Any]) -> TTSRequest:
    if isinstance(request, TTSRequest):
        return request
    return TTSRequest.from_mapping(request)


@dataclass(slots=True)
class SFXRequest:
    """Input payload for ElevenLabs sound effect generation."""

    text: str
    durationSeconds: float = 4.0
    promptInfluence: float = 0.3
    outputFormat: str = "wav"

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("text must not be empty")

        if self.durationSeconds <= 0:
            raise ValueError("durationSeconds must be greater than 0")

        if self.promptInfluence < 0 or self.promptInfluence > 1:
            raise ValueError("promptInfluence must be between 0 and 1")

        if self.outputFormat not in _ALLOWED_OUTPUT_FORMATS:
            raise ValueError("outputFormat must be one of: wav, mp3, ogg")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SFXRequest:
        duration_seconds = payload.get("durationSeconds", payload.get("duration_seconds", 4.0))
        prompt_influence = payload.get("promptInfluence", payload.get("prompt_influence", 0.3))
        return cls(
            text=str(payload.get("text", "")),
            durationSeconds=float(duration_seconds),
            promptInfluence=float(prompt_influence),
            outputFormat=str(payload.get("outputFormat", "wav")),
        )

    def as_payload(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "duration_seconds": self.durationSeconds,
            "prompt_influence": self.promptInfluence,
        }


@dataclass(slots=True)
class SFXResult:
    """Normalized sound effect result for ElevenLabs output."""

    success: bool
    provider: str
    audioBytes: bytes | None = None
    mimeType: str | None = None
    raw: dict[str, Any] | None = None


def coerce_sfx_request(request: SFXRequest | Mapping[str, Any]) -> SFXRequest:
    if isinstance(request, SFXRequest):
        return request
    return SFXRequest.from_mapping(request)
