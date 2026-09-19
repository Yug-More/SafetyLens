"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FrameTimeline, VideoPlayerPanel } from "@/components/FrameTimeline";
import {
  fetchProcessingJob,
  fetchVideo,
  fetchVideoFrames,
} from "@/lib/api";
import {
  mapProcessingJob,
  mapVideoAsset,
  mapVideoFrame,
} from "@/lib/api/mappers";
import type { ProcessingJobView, VideoAsset, VideoFrameItem } from "@/types/video";
import { cn } from "cn";

interface VideoAnalysisWorkspaceProps {
  assetCode: string;
  jobCode: string;
  onReady?: (video: VideoAsset) => void;
}

export function VideoAnalysisWorkspace({
  assetCode,
  jobCode,
  onReady,
}: VideoAnalysisWorkspaceProps) {
  const [video, setVideo] = useState<VideoAsset | null>(null);
  const [job, setJob] = useState<ProcessingJobView | null>(null);
  const [frames, setFrames] = useState<VideoFrameItem[]>([]);
  const [selectedFrameCode, setSelectedFrameCode] = useState<string | null>(null);
  const [seekSeconds, setSeekSeconds] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const onReadyRef = useRef(onReady);

  useEffect(() => {
    onReadyRef.current = onReady;
  }, [onReady]);

  const loadFrames = useCallback(async (code: string) => {
    const response = await fetchVideoFrames(code);
    setFrames(response.data.map(mapVideoFrame));
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [videoData, jobData] = await Promise.all([
        fetchVideo(assetCode),
        fetchProcessingJob(jobCode),
      ]);
      const mappedVideo = mapVideoAsset(videoData);
      const mappedJob = mapProcessingJob(jobData);
      setVideo(mappedVideo);
      setJob(mappedJob);
      setError(null);
      if (mappedJob.status === "completed" || mappedVideo.status === "ready") {
        await loadFrames(assetCode);
        onReadyRef.current?.(mappedVideo);
      }
      return mappedJob;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh processing status.");
      return null;
    }
  }, [assetCode, jobCode, loadFrames]);

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;

    async function poll() {
      const mappedJob = await refresh();
      if (cancelled || !mappedJob) return;
      if (mappedJob.status === "completed" || mappedJob.status === "failed") {
        return;
      }
      timer = window.setTimeout(() => {
        void poll();
      }, 1000);
    }

    void poll();

    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [refresh]);

  const progress = job?.progress ?? 0;
  const failed = job?.status === "failed" || video?.status === "failed";
  const ready = job?.status === "completed" && video?.status === "ready";

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Processing Status</h3>
            <p className="text-xs text-muted-foreground" aria-live="polite">
              {job?.currentStep ?? "Waiting for job updates…"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground">
              {job?.jobCode ?? jobCode}
            </span>
            {failed ? (
              <Button size="sm" variant="outline" onClick={() => void refresh()}>
                <RefreshCw data-icon="inline-start" />
                Retry
              </Button>
            ) : null}
          </div>
        </div>

        <div
          className="h-2 overflow-hidden rounded-full bg-muted"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Processing progress"
        >
          <div
            className={cn(
              "h-full rounded-full transition-all",
              failed ? "bg-destructive" : "bg-primary"
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          {failed
            ? job?.errorMessage ?? "Processing failed."
            : ready
              ? "Ready for AI analysis"
              : `Progress ${progress}%`}
        </p>
        {error ? (
          <p className="mt-2 text-xs text-red-300" role="alert">
            {error}
          </p>
        ) : null}
      </section>

      {video?.contentUrl ? (
        <VideoPlayerPanel
          contentUrl={video.contentUrl}
          cameraName={video.cameraName ?? "Camera 04"}
          location={video.location}
          seekSeconds={seekSeconds}
        />
      ) : null}

      {ready ? (
        <FrameTimeline
          frames={frames}
          selectedFrameCode={selectedFrameCode}
          onSelect={(frame) => {
            setSelectedFrameCode(frame.frameCode);
            setSeekSeconds(frame.timestampSeconds);
          }}
        />
      ) : null}
    </div>
  );
}
