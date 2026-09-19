"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import {
  Camera,
  Circle,
  Crosshair,
  Loader2,
  Upload,
  Grid3X3,
  AlertTriangle,
} from "lucide-react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { LiveClock } from "@/components/LiveClock";
import type { Camera as CameraType } from "@/types";

export const MONITOR_CAMERA_SLOTS = [
  { id: "cam-01", name: "Camera 01", location: "Main Entrance" },
  { id: "cam-02", name: "Camera 02", location: "Loading Bay" },
  { id: "cam-03", name: "Camera 03", location: "Warehouse Aisle" },
  { id: "cam-04", name: "Camera 04", location: "Production Floor" },
] as const;

export const DEFAULT_UPLOAD_CAMERA_ID = "cam-03";
export const DEFAULT_UPLOAD_LOCATION = "Warehouse Aisle";

export type CameraOperationalState =
  | "safe"
  | "monitoring"
  | "processing"
  | "analyzing"
  | "incident"
  | "warning"
  | "offline";

export function resolveMonitorCamera(
  slot: (typeof MONITOR_CAMERA_SLOTS)[number],
  apiCameras: CameraType[]
): CameraType {
  const matched = apiCameras.find((camera) => camera.id === slot.id);
  if (matched) {
    return matched;
  }
  return {
    id: slot.id,
    name: slot.name,
    location: slot.location,
    status: "offline",
    monitoringActive: false,
    lastHeartbeat: "—",
  };
}

function operationalLabel(state: CameraOperationalState): string {
  switch (state) {
    case "safe":
      return "Safe";
    case "monitoring":
      return "Monitoring";
    case "processing":
      return "Processing";
    case "analyzing":
      return "Analyzing";
    case "incident":
      return "Incident";
    case "warning":
      return "Warning";
    case "offline":
      return "Offline";
    default:
      return "Monitoring";
  }
}

function operationalColor(state: CameraOperationalState): string {
  switch (state) {
    case "safe":
    case "monitoring":
      return "text-emerald-300";
    case "processing":
    case "analyzing":
      return "text-amber-300";
    case "incident":
      return "text-red-300";
    case "warning":
      return "text-amber-300";
    case "offline":
      return "text-slate-400";
    default:
      return "text-emerald-300";
  }
}

function operationalDot(state: CameraOperationalState): string {
  switch (state) {
    case "safe":
    case "monitoring":
      return "bg-emerald-400";
    case "processing":
    case "analyzing":
      return "bg-amber-400 animate-pulse";
    case "incident":
      return "bg-red-400 animate-pulse";
    case "warning":
      return "bg-amber-400";
    case "offline":
      return "bg-slate-500";
    default:
      return "bg-emerald-400";
  }
}

interface CameraMonitorProps {
  camera: CameraType;
  size?: "default" | "large";
  showActions?: boolean;
  className?: string;
  onUploadClick?: () => void;
  videoUrl?: string | null;
  recordedLabel?: boolean;
}

export function CameraMonitor({
  camera,
  size = "default",
  showActions = true,
  className,
  onUploadClick,
  videoUrl,
  recordedLabel = false,
}: CameraMonitorProps) {
  return (
    <section
      className={cn(
        "overflow-hidden rounded-xl border border-border bg-panel shadow-sm",
        className
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Live Monitor — {camera.name}
          </h2>
          <p className="text-sm text-muted-foreground">{camera.location}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {recordedLabel || videoUrl ? (
            <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-secondary px-2 py-1 font-medium text-slate-300">
              DEMO FEED
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-md border border-destructive/30 bg-destructive/10 px-2 py-1 font-medium text-red-300">
              <span className="live-pulse size-1.5 rounded-full bg-red-400" />
              LIVE
            </span>
          )}
          <span className="inline-flex items-center gap-1.5 rounded-md border border-success/30 bg-success/10 px-2 py-1 font-medium text-emerald-300">
            <Circle className="size-2 fill-current" aria-hidden="true" />
            Monitoring Active
          </span>
        </div>
      </div>

      <CameraFeedViewport
        camera={camera}
        videoUrl={videoUrl}
        size={size}
        showOverlayLabels
      />

      {showActions ? (
        <div className="flex flex-wrap items-center gap-2 border-t border-border px-4 py-3">
          <Button variant="outline" onClick={onUploadClick}>
            <Upload data-icon="inline-start" />
            Upload Demo Video
          </Button>
          <Button variant="secondary" render={<Link href="/monitor" />}>
            <Grid3X3 data-icon="inline-start" />
            View All Cameras
          </Button>
          <p className="ml-auto text-xs text-muted-foreground">Demo Environment</p>
        </div>
      ) : null}
    </section>
  );
}

interface CameraFeedViewportProps {
  camera: CameraType;
  videoUrl?: string | null;
  size?: "default" | "large" | "tile";
  showOverlayLabels?: boolean;
}

function CameraFeedViewport({
  camera,
  videoUrl,
  size = "default",
  showOverlayLabels = false,
}: CameraFeedViewportProps) {
  const [videoError, setVideoError] = useState(false);
  const showVideo = Boolean(videoUrl) && !videoError;

  const aspectClass =
    size === "large"
      ? "aspect-[16/9] min-h-[320px]"
      : size === "tile"
        ? "aspect-video min-h-[180px]"
        : "aspect-video min-h-[240px]";

  return (
    <div className={cn("relative overflow-hidden bg-[#070d18]", aspectClass)}>
      {showVideo ? (
        <video
          key={videoUrl ?? undefined}
          src={videoUrl ?? undefined}
          controls={size !== "tile"}
          muted={size === "tile"}
          autoPlay={size === "tile"}
          loop={size === "tile"}
          playsInline
          className="absolute inset-0 h-full w-full object-contain bg-black"
          preload="metadata"
          onError={() => setVideoError(true)}
        />
      ) : (
        <>
          <div className="camera-grid absolute inset-0" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(30,58,95,0.35),transparent_65%)]" />
          <div className="camera-scanline pointer-events-none absolute inset-x-0 h-24 bg-gradient-to-b from-transparent via-sky-400/15 to-transparent" />

          {showOverlayLabels ? (
            <>
              <div className="absolute top-3 left-3 flex flex-col gap-1.5">
                <span className="rounded-md border border-white/10 bg-black/45 px-2 py-1 text-xs font-medium text-slate-100 backdrop-blur-sm">
                  {camera.name}
                </span>
                <span className="rounded-md border border-white/10 bg-black/45 px-2 py-1 text-xs text-slate-300 backdrop-blur-sm">
                  {camera.location}
                </span>
              </div>

              <div className="absolute top-3 right-3 rounded-md border border-white/10 bg-black/45 px-2 py-1 text-xs text-slate-200 backdrop-blur-sm">
                <LiveClock showSeconds />
              </div>
            </>
          ) : null}

          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-center">
            <div className="rounded-full border border-white/10 bg-white/5 p-3 text-slate-300">
              <Camera className="size-6" aria-hidden="true" />
            </div>
            <p className="text-sm font-medium text-slate-200">Simulated Camera Feed</p>
            {size !== "tile" ? (
              <p className="max-w-xs text-xs text-slate-400">
                Upload a short workplace video to prepare Stage 4 analysis
              </p>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}

export interface CameraCardProps {
  camera: CameraType;
  displayName?: string;
  displayLocation?: string;
  className?: string;
  videoUrl?: string | null;
  highlighted?: boolean;
  highlightVariant?: "processing" | "incident";
  operationalState?: CameraOperationalState;
  focused?: boolean;
  onFocus?: () => void;
}

export function CameraCard({
  camera,
  displayName,
  displayLocation,
  className,
  videoUrl,
  highlighted = false,
  highlightVariant = "processing",
  operationalState,
  focused = false,
  onFocus,
}: CameraCardProps) {
  const name = displayName ?? camera.name;
  const location = displayLocation ?? camera.location;
  const connected = camera.status === "online";
  const state: CameraOperationalState =
    operationalState ??
    (camera.status === "offline"
      ? "offline"
      : camera.status === "degraded"
        ? "warning"
        : "monitoring");

  const statusColor =
    camera.status === "online"
      ? "bg-emerald-400"
      : camera.status === "degraded"
        ? "bg-amber-400"
        : "bg-red-400";

  const handleFocus = useCallback(() => {
    onFocus?.();
  }, [onFocus]);

  return (
    <article
      className={cn(
        "overflow-hidden rounded-xl border bg-panel shadow-sm transition",
        highlighted
          ? highlightVariant === "incident"
            ? "border-red-500/70 ring-2 ring-red-500/25"
            : "border-amber-500/70 ring-2 ring-amber-500/25"
          : focused
            ? "border-primary/60 ring-1 ring-primary/30"
            : "border-border hover:border-border/80 hover:bg-panel-elevated",
        className
      )}
    >
      <div className="relative">
        <CameraFeedViewport camera={camera} videoUrl={videoUrl} size="tile" />

        <div className="absolute top-2 left-2 rounded bg-black/50 px-1.5 py-0.5 text-[11px] text-slate-200 backdrop-blur-sm">
          {name}
        </div>

        <div className="absolute top-2 right-2 flex flex-col items-end gap-1">
          {videoUrl ? (
            <span className="rounded border border-white/10 bg-black/55 px-1.5 py-0.5 text-[10px] font-medium text-slate-200 backdrop-blur-sm">
              DEMO FEED
            </span>
          ) : null}
          <span className="inline-flex items-center gap-1 rounded bg-black/50 px-1.5 py-0.5 text-[11px] text-emerald-300 backdrop-blur-sm">
            <span className={cn("size-1.5 rounded-full", statusColor)} />
            {connected ? "Connected" : camera.status}
          </span>
        </div>

        <div className="absolute right-2 bottom-2 rounded bg-black/50 px-1.5 py-0.5 text-[10px] text-slate-300 backdrop-blur-sm">
          <LiveClock showSeconds />
        </div>

        {(state === "processing" || state === "analyzing") && highlighted ? (
          <div className="absolute inset-x-0 bottom-0 flex items-center justify-center gap-1.5 bg-black/60 py-1.5 text-[11px] text-amber-200 backdrop-blur-sm">
            <Loader2 className="size-3 animate-spin" />
            {state === "analyzing" ? "AI analysis running…" : "Processing frames…"}
          </div>
        ) : null}

        {state === "incident" && highlighted ? (
          <div className="absolute inset-x-0 bottom-0 flex items-center justify-center gap-1.5 bg-red-950/70 py-1.5 text-[11px] text-red-200 backdrop-blur-sm">
            <AlertTriangle className="size-3" />
            Incident detected — review required
          </div>
        ) : null}
      </div>

      <div className="space-y-2 p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="truncate text-sm font-medium text-foreground">{location}</h3>
            <p className="text-xs text-muted-foreground">
              Heartbeat {camera.lastHeartbeat}
            </p>
          </div>
          <Button
            size="sm"
            variant={focused ? "default" : "outline"}
            className="h-7 shrink-0 px-2 text-[11px]"
            onClick={handleFocus}
            aria-pressed={focused}
          >
            <Crosshair className="size-3" data-icon="inline-start" />
            Focus
          </Button>
        </div>

        <div className="flex items-center justify-between gap-2 text-[11px]">
          <span
            className={cn(
              "inline-flex items-center gap-1 font-medium",
              operationalColor(state)
            )}
          >
            <span className={cn("size-1.5 rounded-full", operationalDot(state))} />
            {operationalLabel(state)}
          </span>
          <span className="text-muted-foreground">
            {connected ? "Feed online" : "Feed unavailable"}
          </span>
        </div>
      </div>
    </article>
  );
}
