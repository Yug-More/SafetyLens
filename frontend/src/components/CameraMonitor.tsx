"use client";

import Link from "next/link";
import { toast } from "sonner";
import { Camera, Circle, Upload, Grid3X3 } from "lucide-react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { LiveClock } from "@/components/LiveClock";
import type { Camera as CameraType } from "@/types";

interface CameraMonitorProps {
  camera: CameraType;
  size?: "default" | "large";
  showActions?: boolean;
  className?: string;
}

export function CameraMonitor({
  camera,
  size = "default",
  showActions = true,
  className,
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
          <span className="inline-flex items-center gap-1.5 rounded-md border border-destructive/30 bg-destructive/10 px-2 py-1 font-medium text-red-300">
            <span className="live-pulse size-1.5 rounded-full bg-red-400" />
            LIVE
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-md border border-success/30 bg-success/10 px-2 py-1 font-medium text-emerald-300">
            <Circle className="size-2 fill-current" aria-hidden="true" />
            Monitoring Active
          </span>
        </div>
      </div>

      <div
        className={cn(
          "relative overflow-hidden bg-[#070d18]",
          size === "large" ? "aspect-[16/9] min-h-[320px]" : "aspect-video min-h-[240px]"
        )}
      >
        <div className="camera-grid absolute inset-0" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(30,58,95,0.35),transparent_65%)]" />
        <div className="camera-scanline pointer-events-none absolute inset-x-0 h-24 bg-gradient-to-b from-transparent via-sky-400/15 to-transparent" />

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

        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-center">
          <div className="rounded-full border border-white/10 bg-white/5 p-3 text-slate-300">
            <Camera className="size-6" aria-hidden="true" />
          </div>
          <p className="text-sm font-medium text-slate-200">Simulated Camera Feed</p>
          <p className="max-w-xs text-xs text-slate-400">
            Demo environment · Stage 1 placeholder monitor
          </p>
        </div>

        <div className="absolute bottom-3 left-3 inline-flex items-center gap-2 rounded-md border border-success/30 bg-black/50 px-2 py-1 text-xs text-emerald-300 backdrop-blur-sm">
          <span className="size-1.5 rounded-full bg-emerald-400" />
          Connected
        </div>

        <div className="absolute right-3 bottom-3 flex items-center gap-3 rounded-md border border-white/10 bg-black/50 px-2.5 py-1.5 text-[11px] text-slate-300 backdrop-blur-sm">
          <span className="inline-flex items-center gap-1">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            Safe
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="size-1.5 rounded-full bg-amber-400" />
            Warning
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="size-1.5 rounded-full bg-red-400" />
            Critical
          </span>
        </div>
      </div>

      {showActions ? (
        <div className="flex flex-wrap items-center gap-2 border-t border-border px-4 py-3">
          <Button
            variant="outline"
            onClick={() =>
              toast.message("Video analysis will be connected in Stage 2.")
            }
          >
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

interface CameraCardProps {
  camera: CameraType;
  className?: string;
}

export function CameraCard({ camera, className }: CameraCardProps) {
  const statusColor =
    camera.status === "online"
      ? "bg-emerald-400"
      : camera.status === "degraded"
        ? "bg-amber-400"
        : "bg-red-400";

  return (
    <article
      className={cn(
        "overflow-hidden rounded-xl border border-border bg-panel transition hover:border-border/80 hover:bg-panel-elevated",
        className
      )}
    >
      <div className="relative aspect-video bg-[#070d18]">
        <div className="camera-grid absolute inset-0 opacity-70" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Camera className="size-5 text-slate-500" aria-hidden="true" />
        </div>
        <div className="absolute top-2 left-2 rounded bg-black/50 px-1.5 py-0.5 text-[11px] text-slate-200">
          {camera.name}
        </div>
        <div className="absolute top-2 right-2 inline-flex items-center gap-1 rounded bg-black/50 px-1.5 py-0.5 text-[11px] text-emerald-300">
          <span className={cn("size-1.5 rounded-full", statusColor)} />
          {camera.status === "online" ? "LIVE" : camera.status}
        </div>
      </div>
      <div className="space-y-1 p-3">
        <h3 className="text-sm font-medium text-foreground">{camera.location}</h3>
        <p className="text-xs text-muted-foreground">
          Heartbeat {camera.lastHeartbeat}
        </p>
      </div>
    </article>
  );
}
