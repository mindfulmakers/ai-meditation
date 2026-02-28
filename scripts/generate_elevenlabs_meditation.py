"""Generate a basic meditation using ElevenLabs TTS and SFX.

Produces WAV audio files and a meditation JSON definition. AHAP haptic files
are generated afterward if librosa is available.
"""

from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

# Ensure the meditation_maker package is importable.
REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "ai-meditation-starter-kit-api"
sys.path.insert(0, str(API_ROOT))

from ai_meditation_starter_kit_api.meditation_maker.elevenlabs_tts import (
    generate_tts_audio_elevenlabs,
)
from ai_meditation_starter_kit_api.meditation_maker.types import TTSRequest

MEDITATION_ID = "basic-elevenlabs-wav-meditation"
AUDIO_DIR = REPO_ROOT / "audio"
HAPTICS_DIR = REPO_ROOT / "haptics"
MEDITATIONS_DIR = REPO_ROOT / "meditations"

# Speech segments with the text to synthesize.
SEGMENTS = [
    (
        "intro",
        "Welcome. Find a comfortable position, and gently close your eyes. Let your body settle into stillness.",
    ),
    ("inhale", "Now, breathe in slowly and deeply."),
    ("exhale", "And breathe out, releasing any tension."),
    (
        "close",
        "Gently bring your awareness back. When you are ready, open your eyes. Namaste.",
    ),
]


def _wav_duration_ms(path: Path) -> int:
    with wave.open(str(path), "rb") as wf:
        rate = wf.getframerate()
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        # nframes can be INT32_MAX when WAV was written via pipe; derive from file size.
        data_bytes = path.stat().st_size - 44  # 44-byte WAV header
        frames = data_bytes // (channels * sampwidth)
        return int(frames / rate * 1000)


def main() -> None:
    AUDIO_DIR.mkdir(exist_ok=True)
    HAPTICS_DIR.mkdir(exist_ok=True)
    MEDITATIONS_DIR.mkdir(exist_ok=True)

    audio_files: dict[str, Path] = {}

    # Use the existing bell SFX that was already generated.
    bell_path = AUDIO_DIR / f"{MEDITATION_ID}-bell.wav"
    if not bell_path.exists():
        print(f"ERROR: Expected bell audio at {bell_path}")
        sys.exit(1)
    audio_files["bell"] = bell_path
    print(f"Using existing bell: {bell_path}")

    # Generate TTS for each speech segment.
    for name, text in SEGMENTS:
        out_path = AUDIO_DIR / f"{MEDITATION_ID}-{name}.wav"
        print(f"Generating TTS for '{name}'...")
        result = generate_tts_audio_elevenlabs(TTSRequest(text=text))
        if not result.success or not result.audioBytes:
            print(f"  ERROR: TTS failed for '{name}'")
            sys.exit(1)
        out_path.write_bytes(result.audioBytes)
        audio_files[name] = out_path
        dur = _wav_duration_ms(out_path)
        print(f"  Saved {out_path.name} ({dur} ms)")

    # Build timeline using the same structure as the iEmbrace meditation.
    bell_dur = _wav_duration_ms(audio_files["bell"])
    intro_dur = _wav_duration_ms(audio_files["intro"])
    inhale_dur = _wav_duration_ms(audio_files["inhale"])
    exhale_dur = _wav_duration_ms(audio_files["exhale"])
    close_dur = _wav_duration_ms(audio_files["close"])

    # Timing: bell -> pause -> intro -> pause -> inhale -> effect -> pause -> exhale -> effect -> pause -> close
    t = 0
    timeline = []

    # Bell + calm-breath effect at start.
    timeline.append({"atMs": t, "kind": "effect", "effectId": "calm-breath"})
    timeline.append(
        {"atMs": t, "kind": "wav", "file": f"audio/{MEDITATION_ID}-bell.wav"}
    )
    t += bell_dur + 2000  # 2s pause after bell

    # Intro
    timeline.append(
        {"atMs": t, "kind": "wav", "file": f"audio/{MEDITATION_ID}-intro.wav"}
    )
    t += intro_dur + 1500  # 1.5s pause

    # Inhale
    timeline.append(
        {"atMs": t, "kind": "wav", "file": f"audio/{MEDITATION_ID}-inhale.wav"}
    )
    inhale_start = t
    t += inhale_dur
    # Soft-pulse effect during inhale
    timeline.append(
        {"atMs": inhale_start + 1500, "kind": "effect", "effectId": "soft-pulse"}
    )
    t += 5000  # 5s breathing pause

    # Exhale
    timeline.append(
        {"atMs": t, "kind": "wav", "file": f"audio/{MEDITATION_ID}-exhale.wav"}
    )
    t += exhale_dur
    # Starfield effect during exhale
    timeline.append({"atMs": t - 1000, "kind": "effect", "effectId": "starfield"})
    t += 3000  # 3s pause

    # Close
    timeline.append(
        {"atMs": t, "kind": "wav", "file": f"audio/{MEDITATION_ID}-close.wav"}
    )
    t += close_dur

    total_duration = t

    # Sort timeline by atMs for cleanliness.
    timeline.sort(key=lambda e: (e["atMs"], e.get("kind", "")))

    meditation = {
        "version": 1,
        "id": MEDITATION_ID,
        "title": "Basic ElevenLabs WAV Meditation",
        "durationMs": total_duration,
        "timeline": timeline,
    }

    out_json = MEDITATIONS_DIR / f"{MEDITATION_ID}.json"
    out_json.write_text(json.dumps(meditation, indent=2) + "\n")
    print(f"\nMeditation JSON written to {out_json}")
    print(f"Total duration: {total_duration} ms ({total_duration / 1000:.1f}s)")

    # Generate AHAP haptic files from audio.
    try:
        from ai_meditation_starter_kit_api.meditation_maker.ahap import (
            convert_wav_to_ahap,
        )

        print("\nGenerating AHAP haptic files...")
        for name, path in audio_files.items():
            print(f"  Processing {name}...")
            convert_wav_to_ahap(str(path), str(HAPTICS_DIR), mode="sfx", split="none")
        print("AHAP generation complete.")

        # Add AHAP entries to the timeline.
        ahap_entries = []
        for entry in timeline:
            if entry["kind"] == "wav":
                wav_file = entry["file"]
                ahap_file = wav_file.replace("audio/", "haptics/").replace(
                    ".wav", ".ahap"
                )
                ahap_path = REPO_ROOT / ahap_file
                if ahap_path.exists():
                    ahap_entries.append(
                        {
                            "atMs": entry["atMs"],
                            "kind": "ahap",
                            "file": ahap_file,
                            "platform": "ios",
                        }
                    )
        timeline.extend(ahap_entries)
        timeline.sort(key=lambda e: (e["atMs"], e.get("kind", "")))

        meditation["timeline"] = timeline
        out_json.write_text(json.dumps(meditation, indent=2) + "\n")
        print("Updated meditation JSON with AHAP entries.")

    except ImportError:
        print("\nlibrosa not available — skipping AHAP generation.")
        print("Run with a venv that has librosa to generate haptics.")


if __name__ == "__main__":
    main()
