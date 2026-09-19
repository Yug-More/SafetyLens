"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { Loader2, Radar, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import {
  fetchDetectorEvents,
  ingestDetectorEvent,
  retryDetectorEvent,
} from "@/lib/api";
import type { ApiDetectorEvent } from "@/lib/api/types";
import { useApiResource } from "@/hooks/useApiResource";
import { ConnectionBanner } from "@/components/ConnectionBanner";

function statusLabel(status: ApiDetectorEvent["status"]): string {
  switch (status) {
    case "received":
      return "Suspected event received";
    case "uploading":
      return "Incident clip importing";
    case "processing":
      return "Processing detector clip";
    case "ready":
      return "Incident clip exported / ready";
    case "analyzing":
      return "AI analysis requested";
    case "completed":
      return "Handoff completed";
    case "failed":
      return "Handoff failed";
    case "detector_unavailable":
      return "Detector unavailable";
    default:
      return status;
  }
}

export function DetectorHandoffPanel({
  onOpenAsset,
}: {
  onOpenAsset?: (assetCode: string, jobCode: string | null) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [clipFile, setClipFile] = useState<File | null>(null);

  const loader = useCallback(async () => {
    const response = await fetchDetectorEvents(10);
    return response.data;
  }, []);

  const { data, error, source, isLoading, reload } = useApiResource({
    loader,
    fallback: () => [] as ApiDetectorEvent[],
    allowFallback: false,
  });

  const events = data ?? [];

  async function handleIngest() {
    if (!clipFile) {
      setActionError("Choose a detector evidence clip before ingesting.");
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      const eventId = `evt-ui-${Date.now()}`;
      const event = await ingestDetectorEvent({
        clip: clipFile,
        event: {
          schema_version: "1.0",
          event_id: eventId,
          event_type: "possible_person_down",
          source_id: "demo-camera-04",
          camera_id: "cam-04",
          track_id: "track-ui-1",
          occurred_at: new Date().toISOString(),
          source_timestamp_seconds: 2,
          clip_event_offset_seconds: 2,
          state: "incident",
          trigger_signals: ["rapid_drop", "demo_ingest"],
          pose_quality: 0.9,
          heuristic_score: null,
          metrics: {},
          limitations: ["demo_ui_ingest", "requires_human_verification"],
        },
      });
      if (event.asset_code && onOpenAsset) {
        onOpenAsset(event.asset_code, event.job_code);
      }
      reload();
    } catch (err) {
      setActionError(
        err instanceof ApiError
          ? err.message
          : "Detector ingest failed. Uploaded-video demo remains available."
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleRetry(eventId: string) {
    setBusy(true);
    setActionError(null);
    try {
      await retryDetectorEvent(eventId);
      reload();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Retry failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-3 rounded-xl border border-border bg-panel p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">Detector handoff</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Optional Stage 7 path: ingest Sean&apos;s contract event + clip into the existing
            upload/analyze pipeline. Uploaded-video demo works even if the detector process is
            offline.
          </p>
        </div>
        <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-100">
          pose_quality ≠ fall probability
        </span>
      </div>

      <ConnectionBanner
        mode={source === "fallback" ? "fallback" : source === "error" ? "error" : "api"}
        message={
          error
            ? `${error} Detector API unavailable — continue with Upload Demo Video.`
            : null
        }
        onRetry={reload}
      />

      <div className="flex flex-wrap items-end gap-2">
        <label className="space-y-1 text-xs text-muted-foreground">
          Evidence clip
          <input
            type="file"
            accept="video/mp4,video/quicktime,video/webm"
            className="block w-full text-sm text-foreground"
            onChange={(event) => setClipFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <Button size="sm" disabled={busy || !clipFile} onClick={() => void handleIngest()}>
          {busy ? (
            <Loader2 className="size-4 animate-spin" data-icon="inline-start" />
          ) : (
            <Radar data-icon="inline-start" />
          )}
          Ingest detector event
        </Button>
        <Button size="sm" variant="outline" disabled={isLoading || busy} onClick={reload}>
          <RefreshCw data-icon="inline-start" />
          Refresh
        </Button>
      </div>

      {actionError ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-red-200" role="alert">
          {actionError}
        </div>
      ) : null}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading detector events…</p>
      ) : events.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No detector events yet. Use known-video upload for the reliable demo path.
        </p>
      ) : (
        <ul className="space-y-2">
          {events.map((event) => (
            <li key={event.id} className="rounded-lg border border-border bg-background/40 p-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-medium text-foreground">{event.event_id}</p>
                <span className="text-xs text-muted-foreground">{statusLabel(event.status)}</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                source {event.source_id}
                {event.camera_id ? ` · camera ${event.camera_id}` : ""}
                {event.track_id ? ` · track ${event.track_id}` : ""}
                {event.trigger_signals.length
                  ? ` · signals ${event.trigger_signals.join(", ")}`
                  : ""}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Pose quality:{" "}
                {event.pose_quality != null ? event.pose_quality.toFixed(2) : "n/a"} (
                {event.pose_quality_label})
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Asset {event.asset_code ?? "—"} · Analysis {event.analysis_code ?? "—"} · Incident{" "}
                {event.incident_code ?? "—"}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {event.asset_code ? (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onOpenAsset?.(event.asset_code!, event.job_code)}
                  >
                    Open evidence
                  </Button>
                ) : null}
                <Link
                  href="/response"
                  className="inline-flex h-7 items-center rounded-lg border border-border bg-background px-2.5 text-[0.8rem] font-medium hover:bg-muted"
                >
                  Response Center
                </Link>
                <Link
                  href="/reports"
                  className="inline-flex h-7 items-center rounded-lg border border-border bg-background px-2.5 text-[0.8rem] font-medium hover:bg-muted"
                >
                  Reports
                </Link>
                {event.status === "failed" ? (
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={busy}
                    onClick={() => void handleRetry(event.event_id)}
                  >
                    Retry handoff
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
