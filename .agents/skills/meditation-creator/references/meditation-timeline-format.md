# Meditation Timeline JSON Format

## File Location

Store meditation files in:
`./.codex/skills/meditation-creator/assets/meditations/`

## Top-Level Shape

```json
{
  "version": 1,
  "id": "box-breath-5-min",
  "title": "5 Minute Box Breath",
  "durationMs": 300000,
  "timeline": []
}
```

## Timeline Event Types

Each item in `timeline` must include:
- `atMs` (number): start time in milliseconds from the session start.
- `kind` (string): one of `wav`, `ahap`, `effect`.

Kind-specific fields:
- `wav`:
  - `file` (string): wav asset path.
  - `gain` (number, optional): volume multiplier, usually `0.0` to `1.0`.
- `ahap`:
  - `file` (string): ahap file path.
  - `platform` (string, optional): usually `"ios"`.
- `effect`:
  - `effectId` (string): visual effect identifier (project-defined string).

## Validation Rules

- Keep `timeline` sorted by `atMs` ascending.
- Multiple events may use the same `atMs`.
- Keep `id` lowercase kebab-case and match the filename (`<id>.json`).
- Use relative paths for `file` values.
