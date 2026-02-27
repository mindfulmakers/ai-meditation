---
name: meditation-creator
description: Use this skill when creating or editing meditation timeline JSON files with timestamped wav audio cues, optional ahap haptic cues, and visual effect trigger events in this project.
---

# Meditation Creator

## Overview

This skill creates and updates meditation timeline JSON files.

## Workflow

1. Read `references/meditation-timeline-format.md` for the canonical JSON shape.
2. Keep timeline events ordered by `atMs` ascending.
3. Validate that each event uses one of the supported kinds:
   `wav`, `ahap`, `effect`.

## Event Rules

- `wav`: Play a wav file at a timestamp.
- `ahap`: iOS haptic cue (supported in schema, optional for now).
- `effect`: Trigger a visual effect by string identifier.
- Use relative asset paths (for example, `audio/chime.wav` or `haptics/rise.ahap`).
- Multiple events can share the same `atMs`.

## Output Location

- Always place meditation JSON files in the project's
  `./meditations/`
- Place generated meditation audio files in:
  `./audio/`
  (directory tracked by
  `./audio/.gitkeep`).
- Keep IDs lowercase kebab-case and match file names (`<id>.json`).
