from .elevenlabs_sfx import generate_sfx_audio_elevenlabs
from .elevenlabs_tts import generate_tts_audio_elevenlabs
from .iembrace import generate_personalized_meditation, generate_tts_audio_iembrace
from .types import SFXRequest, SFXResult, TTSRequest, TTSResult

_ahap_import_error: Exception | None = None
try:
    from .ahap import convert_wav_to_ahap, generate_ahap, generate_ahap_from_file
except ModuleNotFoundError as exc:
    _ahap_import_error = exc

    def _raise_missing_ahap_dependency(*args, **kwargs):  # type: ignore[no-untyped-def]
        msg = "AHAP generation requires optional dependency 'librosa'."
        raise RuntimeError(msg) from _ahap_import_error

    convert_wav_to_ahap = _raise_missing_ahap_dependency
    generate_ahap = _raise_missing_ahap_dependency
    generate_ahap_from_file = _raise_missing_ahap_dependency

__all__ = [
    "SFXRequest",
    "SFXResult",
    "TTSRequest",
    "TTSResult",
    "generate_personalized_meditation",
    "generate_tts_audio_iembrace",
    "generate_tts_audio_elevenlabs",
    "generate_sfx_audio_elevenlabs",
    "generate_ahap",
    "convert_wav_to_ahap",
    "generate_ahap_from_file",
]
