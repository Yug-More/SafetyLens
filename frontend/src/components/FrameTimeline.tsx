"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "cn";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { VideoFrameItem } from "@/types/video";

interface FrameTimelineProps {
  frames: VideoFrameItem[];
  selectedFrameCode?: string | null;
  onSelect: (frame: VideoFrameItem) => void;
}

export function FrameTimeline({
  frames,
  selectedFrameCode,
  onSelect,
}: FrameTimelineProps) {
  const [preview, setPreview] = useState<VideoFrameItem | null>(null);

  if (frames.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-panel/60 px-4 py-8 text-center text-sm text-muted-foreground">
        No evidence-candidate frames yet.
      </div>
    );
  }

  return (
    <>
      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="mb-3">
          <h3 className="text-sm font-semibold text-foreground">Frame Timeline</h3>
          <p className="text-xs text-muted-foreground">
            Evidence candidates prepared for AI verification.
          </p>
        </div>
        <div className="flex gap-3 overflow-x-auto pb-1">
          {frames.map((frame) => {
            const selected = frame.frameCode === selectedFrameCode;
            return (
              <button
                key={frame.id}
                type="button"
                className={cn(
                  "w-36 shrink-0 rounded-lg border bg-secondary/30 p-2 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  selected
                    ? "border-primary ring-1 ring-primary/40"
                    : "border-border hover:border-border/80 hover:bg-secondary/50"
                )}
                onClick={() => onSelect(frame)}
                onDoubleClick={() => setPreview(frame)}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={frame.contentUrl}
                  alt={`Frame ${frame.frameNumber} at ${frame.timestampSeconds.toFixed(1)} seconds`}
                  className="aspect-video w-full rounded-md object-cover"
                />
                <p className="mt-2 text-xs font-medium text-foreground">
                  Frame {frame.frameNumber}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {frame.timestampSeconds.toFixed(2)}s
                </p>
              </button>
            );
          })}
        </div>
      </section>

      <Dialog open={preview !== null} onOpenChange={(open) => !open && setPreview(null)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Frame {preview?.frameNumber} · {preview?.timestampSeconds.toFixed(2)}s
            </DialogTitle>
            <DialogDescription>
              Evidence candidate preview. Not labeled as a confirmed incident.
            </DialogDescription>
          </DialogHeader>
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={preview.contentUrl}
              alt={`Enlarged frame ${preview.frameNumber}`}
              className="w-full rounded-lg border border-border"
            />
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
}

interface VideoPlayerPanelProps {
  contentUrl: string;
  cameraName: string;
  location: string;
  seekSeconds?: number | null;
}

export function VideoPlayerPanel({
  contentUrl,
  cameraName,
  location,
  seekSeconds,
}: VideoPlayerPanelProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (seekSeconds == null || !videoRef.current) return;
    videoRef.current.currentTime = seekSeconds;
    void videoRef.current.play().catch(() => undefined);
  }, [seekSeconds]);

  return (
    <section className="overflow-hidden rounded-xl border border-border bg-panel shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Recorded Demo Feed — {cameraName}
          </h2>
          <p className="text-sm text-muted-foreground">{location}</p>
        </div>
        <span className="rounded-md border border-border bg-secondary px-2 py-1 text-xs text-muted-foreground">
          Recorded Demo Feed
        </span>
      </div>
      <div className="bg-black">
        <video
          ref={videoRef}
          src={contentUrl}
          controls
          className="aspect-video w-full"
          preload="metadata"
        >
          Your browser does not support video playback.
        </video>
      </div>
    </section>
  );
}
