#!/usr/bin/env python3
"""Create a new meditation timeline JSON file in this skill's meditations directory."""

import argparse
import json
import re
from pathlib import Path


def normalize_id(raw_id: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", raw_id.lower()).strip("-")
    return re.sub(r"-{2,}", "-", normalized)


def build_document(meditation_id: str, title: str, duration_ms: int) -> dict[str, object]:
    return {
        "version": 1,
        "id": meditation_id,
        "title": title,
        "durationMs": duration_ms,
        "timeline": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a meditation timeline JSON scaffold.",
    )
    parser.add_argument("--id", required=True, help="Meditation id (kebab-case recommended).")
    parser.add_argument("--title", required=True, help="Human-readable meditation title.")
    parser.add_argument("--duration-ms", type=int, default=300000, help="Meditation duration in milliseconds.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite file if it already exists.")
    args = parser.parse_args()

    meditation_id = normalize_id(args.id)
    if not meditation_id:
        raise SystemExit("Error: meditation id must contain at least one alphanumeric character.")

    skill_dir = Path(__file__).resolve().parents[1]
    meditations_dir = skill_dir / "assets" / "meditations"
    meditations_dir.mkdir(parents=True, exist_ok=True)
    output_path = meditations_dir / f"{meditation_id}.json"

    if output_path.exists() and not args.overwrite:
        raise SystemExit(f"Error: file already exists at {output_path}. Use --overwrite to replace it.")

    document = build_document(meditation_id=meditation_id, title=args.title, duration_ms=args.duration_ms)
    output_path.write_text(f"{json.dumps(document, indent=2)}\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
