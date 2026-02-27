from __future__ import annotations

import json
import os
from pathlib import Path

import librosa
import numpy as np
from tqdm import tqdm


def _canonical_split(split: str) -> str:
    value = split.strip().lower()
    if value == "vocal":
        return "vocals"
    return value


def _safe_peak(signal: np.ndarray) -> float:
    peak = float(np.max(np.abs(signal))) if signal.size else 0.0
    return peak if peak > 0 else 1.0


def write_ahap_file(output_ahap: str, ahap_data: dict[str, object]) -> None:
    with open(output_ahap, "w", encoding="utf-8") as f:
        json.dump(ahap_data, f, indent=2)


def calculate_parameters(
    audio_data: np.ndarray,
    time: float,
    sample_rate: int,
    split: str,
    sharpness_factor: float = 3.0,
    intensity_factor: float = 2.5,
) -> tuple[float, float]:
    split = _canonical_split(split)

    window_size = int(sample_rate * 0.02)
    start_index = max(0, int((time - 0.01) * sample_rate))
    end_index = min(len(audio_data), start_index + window_size)

    window = audio_data[start_index:end_index]
    if window.size == 0:
        return 0.0, 0.0

    energy = float(np.sqrt(np.mean(window**2)))

    centroid_window_size = int(sample_rate * 0.05)
    centroid_start = max(0, int((time - 0.025) * sample_rate))
    centroid_end = min(len(audio_data), centroid_start + centroid_window_size)

    centroid_window = audio_data[centroid_start:centroid_end]
    if centroid_window.size == 0:
        return min(max(energy * intensity_factor, 0.0), 1.0), 0.0

    spectral_centroid = librosa.feature.spectral_centroid(y=centroid_window, sr=sample_rate)
    sharpness = float(np.mean(spectral_centroid))

    scaled_energy = np.clip(energy / _safe_peak(audio_data), 0, 1) * intensity_factor
    scaled_energy = float(np.clip(scaled_energy, 0, 1))

    scaled_sharpness = np.clip(sharpness / _safe_peak(spectral_centroid), 0, 1) * sharpness_factor
    scaled_sharpness = float(np.clip(scaled_sharpness, 0, 1))

    profile_multiplier = {
        "vocals": (1.2, 1.1),
        "drums": (1.5, 1.3),
        "bass": (1.4, 0.9),
        "other": (1.3, 1.2),
    }

    energy_mult, sharpness_mult = profile_multiplier.get(split, (1.0, 1.0))
    scaled_energy = float(np.clip(scaled_energy * energy_mult, 0, 1))
    scaled_sharpness = float(np.clip(scaled_sharpness * sharpness_mult, 0, 1))

    return scaled_energy, scaled_sharpness


def create_event(
    event_type: str,
    time: float,
    audio_data: np.ndarray,
    sample_rate: int,
    split: str,
    sharpness_factor: float,
    intensity_factor: float,
) -> dict[str, object]:
    intensity, sharpness = calculate_parameters(
        audio_data,
        time,
        sample_rate,
        split,
        sharpness_factor=sharpness_factor,
        intensity_factor=intensity_factor,
    )

    event: dict[str, object] = {
        "Event": {
            "Time": float(time),
            "EventType": event_type,
            "EventParameters": [
                {"ParameterID": "HapticIntensity", "ParameterValue": float(intensity)},
                {"ParameterID": "HapticSharpness", "ParameterValue": float(sharpness)},
            ],
        }
    }

    if event_type == "HapticContinuous":
        event["Event"]["EventDuration"] = 0.1

    return event


def determine_haptic_mode(
    audio_data: np.ndarray,
    time: float,
    sample_rate: int,
    mode: str,
    harmonic: np.ndarray,
    percussive: np.ndarray,
    bass: np.ndarray,
) -> str:
    window_size = int(sample_rate * 0.02)
    start_index = max(0, int((time - 0.01) * sample_rate))
    end_index = min(len(audio_data), start_index + window_size)

    window = audio_data[start_index:end_index]
    if window.size == 0:
        return "continuous"

    energy = float(np.sqrt(np.mean(window**2)))

    _ = float(np.sqrt(np.mean(bass[start_index:end_index] ** 2))) if bass[start_index:end_index].size else 0.0
    _ = (
        float(np.sqrt(np.mean(percussive[start_index:end_index] ** 2)))
        if percussive[start_index:end_index].size
        else 0.0
    )
    _ = float(np.sqrt(np.mean(harmonic[start_index:end_index] ** 2))) if harmonic[start_index:end_index].size else 0.0

    centroid_window_size = int(sample_rate * 0.05)
    centroid_start = max(0, int((time - 0.025) * sample_rate))
    centroid_end = min(len(audio_data), centroid_start + centroid_window_size)
    centroid_window = audio_data[centroid_start:centroid_end]

    if centroid_window.size == 0:
        return "continuous"

    spectral_centroid = librosa.feature.spectral_centroid(y=centroid_window, sr=sample_rate)
    spectral_centroid_mean = float(np.mean(spectral_centroid))

    if mode == "sfx":
        transient_rms_threshold = 0.5
        continuous_rms_threshold = 0.2
        spectral_threshold = float(np.percentile(spectral_centroid, 90))
    else:
        transient_rms_threshold = 0.2
        continuous_rms_threshold = 0.1
        spectral_threshold = float(np.percentile(spectral_centroid, 70))

    if energy > transient_rms_threshold and spectral_centroid_mean > spectral_threshold:
        return "transient"
    if energy < continuous_rms_threshold:
        return "continuous"
    return "both"


def add_continuous_events(
    pattern: list[dict[str, object]],
    audio_data: np.ndarray,
    sample_rate: int,
    harmonic: np.ndarray,
    bass: np.ndarray,
    duration: float,
    time_step: float,
    intensity_factor: float = 2.5,
    sharpness_factor: float = 3.0,
) -> None:
    num_steps = int(duration / time_step) if duration > 0 else 0

    for t in tqdm(np.arange(0, duration, time_step), total=num_steps, desc="Processing continuous events"):
        start = int(t * sample_rate)
        end = int((t + time_step) * sample_rate)

        bass_window = bass[start:end]
        harmonic_window = harmonic[start:end]
        if bass_window.size == 0 or harmonic_window.size == 0:
            continue

        bass_energy = float(np.sqrt(np.mean(bass_window**2)))
        harmonic_energy = float(np.sqrt(np.mean(harmonic_window**2)))

        intensity = np.clip(bass_energy / _safe_peak(bass), 0, 1) * intensity_factor
        intensity = float(np.clip(intensity, 0, 1))

        sharpness = np.clip(harmonic_energy / _safe_peak(harmonic), 0, 1) * sharpness_factor
        sharpness = float(np.clip(sharpness, 0, 1))

        pattern.append(
            {
                "Event": {
                    "Time": float(t),
                    "EventType": "HapticContinuous",
                    "EventDuration": time_step,
                    "EventParameters": [
                        {"ParameterID": "HapticIntensity", "ParameterValue": intensity},
                        {"ParameterID": "HapticSharpness", "ParameterValue": sharpness},
                    ],
                }
            }
        )


def generate_ahap(
    audio_data: np.ndarray,
    sample_rate: int,
    mode: str,
    harmonic: np.ndarray,
    percussive: np.ndarray,
    bass: np.ndarray,
    duration: float,
    split: str,
    sharpness_factor: float,
    intensity_factor: float,
) -> dict[str, object]:
    """Generate AHAP payload data from prepared audio arrays and decomposition tracks."""
    pattern: list[dict[str, object]] = []

    onsets = librosa.onset.onset_detect(y=audio_data, sr=sample_rate)
    event_times = librosa.frames_to_time(onsets, sr=sample_rate)

    for event_time in tqdm(event_times, total=len(event_times), desc="Processing transient events"):
        haptic_mode = determine_haptic_mode(
            audio_data,
            float(event_time),
            sample_rate,
            mode,
            harmonic,
            percussive,
            bass,
        )

        if haptic_mode in {"transient", "both"}:
            pattern.append(
                create_event(
                    "HapticTransient",
                    float(event_time),
                    audio_data,
                    sample_rate,
                    split,
                    sharpness_factor=sharpness_factor,
                    intensity_factor=intensity_factor,
                )
            )

        if haptic_mode in {"continuous", "both"}:
            pattern.append(
                create_event(
                    "HapticContinuous",
                    float(event_time),
                    audio_data,
                    sample_rate,
                    split,
                    sharpness_factor=sharpness_factor,
                    intensity_factor=intensity_factor,
                )
            )

    add_continuous_events(
        pattern,
        audio_data,
        sample_rate,
        harmonic,
        bass,
        duration,
        time_step=0.1,
        intensity_factor=intensity_factor,
        sharpness_factor=sharpness_factor,
    )

    return {"Version": 1.0, "Pattern": pattern}


def convert_wav_to_ahap(
    input_wav: str,
    output_dir: str | None,
    mode: str,
    split: str,
    sample_rate: int = 44100,
    sharpness_factor: float = 3.0,
    intensity_factor: float = 2.5,
) -> list[str]:
    """Convert an input audio file into one or more `.ahap` files."""
    split = _canonical_split(split)

    if not output_dir:
        output_dir = str(Path(input_wav).resolve().parent)

    os.makedirs(output_dir, exist_ok=True)

    audio_data, loaded_sample_rate = librosa.load(input_wav, sr=sample_rate, mono=True)
    duration = len(audio_data) / loaded_sample_rate if loaded_sample_rate else 0.0

    harmonic, percussive = librosa.effects.hpss(audio_data)
    bass = librosa.effects.hpss(audio_data, margin=(1.0, 20.0))[0]

    output_files: list[str] = []
    input_base = Path(input_wav).name

    if split == "none":
        ahap_data = generate_ahap(
            audio_data,
            loaded_sample_rate,
            mode,
            harmonic,
            percussive,
            bass,
            duration,
            split,
            sharpness_factor=sharpness_factor,
            intensity_factor=intensity_factor,
        )
        output_ahap = os.path.join(output_dir, input_base.replace(Path(input_wav).suffix, ".ahap"))
        output_ahap = output_ahap.replace("_background", "")
        write_ahap_file(output_ahap, ahap_data)
        output_files.append(output_ahap)
        return output_files

    split_targets = ["bass", "vocals", "drums", "other"] if split == "all" else [split]

    for split_type in split_targets:
        ahap_data = generate_ahap(
            audio_data,
            loaded_sample_rate,
            mode,
            harmonic,
            percussive,
            bass,
            duration,
            split_type,
            sharpness_factor=sharpness_factor,
            intensity_factor=intensity_factor,
        )
        output_ahap = os.path.join(
            output_dir,
            input_base.replace(Path(input_wav).suffix, f"_{split_type}.ahap"),
        )
        write_ahap_file(output_ahap, ahap_data)
        output_files.append(output_ahap)

    return output_files


def generate_ahap_from_file(background_file: str, output_dir: str = "ahap_outputs") -> str:
    """Generate a single `.ahap` output file from a background audio file path."""
    outputs = convert_wav_to_ahap(background_file, output_dir, mode="sfx", split="none")
    return outputs[0]
