import DashboardLayout from "@/components/layouts/ExampleLayout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { isVisualEffectId } from "@/features/timeline-visuals/effectIds";
import {
  extractPlaybackEvents,
  PlaybackEvent,
} from "@/features/timeline-visuals/timelineEvents";
import { PixiTimelineVisuals } from "@/features/timeline-visuals/pixiTimelineVisuals";
import { useToast } from "@/hooks/use-toast";
import { fetchMeditations, MeditationRecord } from "@/services/meditations";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

function getEventKindLabel(event: PlaybackEvent): string {
  return event.kind === "unknown" ? event.rawKind : event.kind;
}

function getEventTargetLabel(event: PlaybackEvent): string {
  if (event.kind === "wav" || event.kind === "ahap") {
    return event.file ?? "trigger";
  }

  if (event.kind === "effect") {
    return event.effectId;
  }

  return event.file ?? event.effectId ?? "trigger";
}

const Dashboard = () => {
  const { toast } = useToast();
  const [meditations, setMeditations] = useState<MeditationRecord[]>([]);
  const [isLoadingMeditations, setIsLoadingMeditations] = useState(true);
  const [selectedMeditationId, setSelectedMeditationId] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentMs, setCurrentMs] = useState(0);
  const [recentTriggers, setRecentTriggers] = useState<string[]>([]);

  const playbackTimeoutsRef = useRef<number[]>([]);
  const playbackTickerRef = useRef<number | null>(null);
  const activeAudioRef = useRef<HTMLAudioElement[]>([]);
  const visualsContainerRef = useRef<HTMLDivElement | null>(null);
  const visualsRef = useRef<PixiTimelineVisuals | null>(null);

  const selectedMeditation = useMemo(
    () => meditations.find((item) => item.id === selectedMeditationId) ?? null,
    [meditations, selectedMeditationId]
  );

  const selectedTimeline = useMemo(
    () => extractPlaybackEvents(selectedMeditation?.timeline),
    [selectedMeditation?.timeline]
  );

  const clearPlayback = useCallback(() => {
    for (const timeoutId of playbackTimeoutsRef.current) {
      window.clearTimeout(timeoutId);
    }
    playbackTimeoutsRef.current = [];

    if (playbackTickerRef.current !== null) {
      window.clearInterval(playbackTickerRef.current);
      playbackTickerRef.current = null;
    }

    for (const audio of activeAudioRef.current) {
      audio.pause();
      audio.currentTime = 0;
    }
    activeAudioRef.current = [];

    void visualsRef.current?.reset();
  }, []);

  const stopPlayback = useCallback(
    (resetMs = false) => {
      clearPlayback();
      setIsPlaying(false);
      if (resetMs) {
        setCurrentMs(0);
      }
    },
    [clearPlayback]
  );

  useEffect(() => {
    const hostElement = visualsContainerRef.current;

    if (!hostElement) {
      return;
    }

    const visuals = new PixiTimelineVisuals(hostElement);
    visualsRef.current = visuals;

    return () => {
      visuals.destroy();
      visualsRef.current = null;
    };
  }, []);

  useEffect(() => {
    const abortController = new AbortController();
    setIsLoadingMeditations(true);

    fetchMeditations(abortController.signal)
      .then((payload) => {
        setMeditations(payload);
        if (payload.length > 0) {
          setSelectedMeditationId((prev) => prev ?? payload[0].id);
        }
      })
      .catch((error: Error) => {
        toast({
          title: "Failed to load meditations",
          description: error.message,
          variant: "destructive",
        });
      })
      .finally(() => {
        setIsLoadingMeditations(false);
      });

    return () => {
      abortController.abort();
    };
  }, [toast]);

  useEffect(() => () => stopPlayback(), [stopPlayback]);

  const handleMeditationSelect = useCallback(
    (meditationId: string) => {
      stopPlayback(true);
      setRecentTriggers([]);
      setSelectedMeditationId(meditationId);
    },
    [stopPlayback]
  );

  const playSelectedMeditation = useCallback(() => {
    if (!selectedMeditation) {
      return;
    }

    stopPlayback(true);
    setRecentTriggers([]);
    setIsPlaying(true);

    const startAt = Date.now();
    playbackTickerRef.current = window.setInterval(() => {
      setCurrentMs(Math.max(0, Date.now() - startAt));
    }, 100);

    const duration = Math.max(0, selectedMeditation.durationMs);
    const timelineEvents = extractPlaybackEvents(selectedMeditation.timeline);

    for (const event of timelineEvents) {
      const timeoutId = window.setTimeout(() => {
        if (event.kind === "wav") {
          const audio = new Audio(event.file);
          activeAudioRef.current.push(audio);
          void audio.play();
        }

        if (event.kind === "effect") {
          if (!isVisualEffectId(event.effectId)) {
            const unknownEffectMessage =
              `No Pixi animation mapped for effect \"${event.effectId}\".`;

            setRecentTriggers((existing) => [
              `[${event.atMs}ms] effect error: ${event.effectId}`,
              ...existing,
            ].slice(0, 8));

            toast({
              title: "Unknown visual effect",
              description: unknownEffectMessage,
              variant: "destructive",
            });

            setCurrentMs(event.atMs);
            stopPlayback();
            return;
          }

          void visualsRef.current?.switchTo(event.effectId);
        }

        const triggerDescription =
          event.kind === "effect"
            ? `[${event.atMs}ms] effect: ${event.effectId}`
            : event.kind === "wav"
              ? `[${event.atMs}ms] wav: ${event.file}`
              : event.kind === "ahap"
                ? `[${event.atMs}ms] ahap${event.file ? `: ${event.file}` : ""}`
                : `[${event.atMs}ms] ${event.rawKind}`;

        setRecentTriggers((existing) => [triggerDescription, ...existing].slice(0, 8));
      }, event.atMs);

      playbackTimeoutsRef.current.push(timeoutId);
    }

    const completionTimeout = window.setTimeout(() => {
      stopPlayback();
      setCurrentMs(duration);
    }, duration);
    playbackTimeoutsRef.current.push(completionTimeout);
  }, [selectedMeditation, stopPlayback, toast]);

  const progressValue = selectedMeditation
    ? Math.min(100, (Math.max(0, currentMs) / Math.max(1, selectedMeditation.durationMs)) * 100)
    : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Meditation Library</h1>
          <p className="text-sm text-muted-foreground">
            Select a meditation and play its timeline events.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Available Meditations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {isLoadingMeditations ? (
                <p className="text-sm text-muted-foreground">Loading meditations...</p>
              ) : meditations.length === 0 ? (
                <p className="text-sm text-muted-foreground">No meditations available.</p>
              ) : (
                meditations.map((meditation) => (
                  <Button
                    key={meditation.id}
                    variant={
                      selectedMeditation?.id === meditation.id ? "default" : "outline"
                    }
                    className="w-full justify-start"
                    onClick={() => handleMeditationSelect(meditation.id)}
                  >
                    {meditation.title}
                  </Button>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-4">
                <CardTitle className="text-base">
                  {selectedMeditation?.title ?? "Select a meditation"}
                </CardTitle>
                <Badge variant="secondary">
                  {selectedMeditation ? `${selectedMeditation.durationMs} ms` : "No selection"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Progress value={progressValue} />
                <div className="text-xs text-muted-foreground">
                  {currentMs}ms / {selectedMeditation?.durationMs ?? 0}ms
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={playSelectedMeditation}
                  disabled={!selectedMeditation || isPlaying}
                >
                  Play Timeline
                </Button>
                <Button
                  variant="outline"
                  onClick={() => stopPlayback(true)}
                  disabled={!isPlaying && currentMs === 0}
                >
                  Stop
                </Button>
              </div>

              <div className="rounded-md border p-3">
                <p className="mb-2 text-sm font-medium">Visuals</p>
                <div
                  ref={visualsContainerRef}
                  data-testid="visuals-canvas-host"
                  className="h-56 w-full overflow-hidden rounded bg-slate-900/90"
                />
              </div>

              <div className="rounded-md border p-3">
                <p className="mb-2 text-sm font-medium">Timeline Events</p>
                {selectedTimeline.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    This meditation has no timeline events.
                  </p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-24">Time</TableHead>
                        <TableHead className="w-28">Type</TableHead>
                        <TableHead>Target</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedTimeline.map((event, index) => (
                        <TableRow key={`${event.atMs}-${event.kind}-${index}`}>
                          <TableCell className="font-mono text-xs">{event.atMs}ms</TableCell>
                          <TableCell className="text-xs">{getEventKindLabel(event)}</TableCell>
                          <TableCell className="truncate text-xs">
                            {getEventTargetLabel(event)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>

              <div className="rounded-md border p-3">
                <p className="mb-2 text-sm font-medium">Recent Triggers</p>
                {recentTriggers.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No events triggered yet.</p>
                ) : (
                  <ul className="space-y-1">
                    {recentTriggers.map((entry, index) => (
                      <li key={`${entry}-${index}`} className="text-xs text-muted-foreground">
                        {entry}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
