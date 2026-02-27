export interface MeditationRecord {
  id: string;
  title: string;
  durationMs: number;
  timeline: unknown;
}

const defaultMeditationsEndpoint = "/api/ai_meditation_starter_kit/meditations/";
const meditationsEndpoint =
  import.meta.env.VITE_MEDITATIONS_API_PATH ?? defaultMeditationsEndpoint;

function isMeditationRecord(value: unknown): value is MeditationRecord {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.id === "string" &&
    typeof candidate.title === "string" &&
    typeof candidate.durationMs === "number" &&
    "timeline" in candidate
  );
}

export async function fetchMeditations(
  signal?: AbortSignal
): Promise<MeditationRecord[]> {
  const response = await fetch(meditationsEndpoint, {
    method: "GET",
    credentials: "include",
    signal,
  });

  if (!response.ok) {
    throw new Error(`Unable to fetch meditations (${response.status}).`);
  }

  const payload = await response.json();
  if (!Array.isArray(payload)) {
    return [];
  }

  return payload.filter(isMeditationRecord);
}
