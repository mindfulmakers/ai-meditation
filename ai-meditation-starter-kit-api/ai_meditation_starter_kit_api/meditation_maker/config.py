from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_ELEVENLABS_VOICE_ID = "SAz9YHcvj6GT2YYXdXww"  # River - Relaxed, Neutral


def load_project_env() -> None:
    # Load .env from current working directory if present.
    load_dotenv()

    # If running from this repository, also load root .env explicitly.
    repo_root_env = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=repo_root_env, override=False)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        msg = f"Missing required environment variable: {name}"
        raise RuntimeError(msg)
    return value


def get_api_base_url() -> str:
    return require_env("API_BASE_URL").rstrip("/")


def get_user_email() -> str:
    return require_env("X_USER_EMAIL")


def get_elevenlabs_api_key() -> str:
    return require_env("ELEVENLABS_API_KEY")


def get_elevenlabs_voice_id() -> str:
    return os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID)
