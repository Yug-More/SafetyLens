"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle2,
  Circle,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { buildResponseHref } from "@/lib/incident-context";
import { FrameTimeline, VideoPlayerPanel } from "@/components/FrameTimeline";
import {
  fetchAnalysis,
  fetchAIProvider,
  fetchProcessingJob,
  fetchVideo,
  fetchVideoAnalyses,
  fetchVideoFrames,
  fetchWorkflowStatus,
  startVideoAnalysis,
} from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import {
  mapIncidentAnalysis,
  mapProcessingJob,
  mapVideoAsset,
  mapVideoFrame,
} from "@/lib/api/mappers";
import type { ApiWorkflowStatus } from "@/lib/api/types";
import type {
  IncidentAnalysisView,
  ProcessingJobView,
  VideoAsset,
  VideoFrameItem,
} from "@/types/video";
import { cn } from "cn";

export type PipelineStage =
  | "evidence_received"
  | "preparing_video"
  | "extracting_frames"
  | "analyzing"
  | "matching_procedure"
  | "preparing_response"
  | "human_review_required"
  | "failed"
  | "no_incident";

export interface VideoWorkspaceState {
  processing: boolean;
  ready: boolean;
  analyzing: boolean;
  failed: boolean;
  incidentDetected: boolean;
  analysisId: string | null;
  analysisCode: string | null;
  videoAssetCode: string | null;
  cameraId: string | null;
  pipelineStage: PipelineStage;
}

interface VideoAnalysisWorkspaceProps {
  assetCode: string;
  jobCode: string;
  onReady?: (video: VideoAsset) => void;
  onStateChange?: (state: VideoWorkspaceState) => void;
}

const STAGE_LABELS: { id: PipelineStage; label: string }[] = [
  { id: "evidence_received", label: "Evidence received" },
  { id: "preparing_video", label: "Preparing video" },
  { id: "extracting_frames", label: "Extracting key moments" },
  { id: "analyzing", label: "Analyzing possible incident" },
  { id: "matching_procedure", label: "Matching company procedure" },
  { id: "preparing_response", label: "Preparing response" },
  { id: "human_review_required", label: "Human review required" },
];

function confidencePercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

function formatIncidentType(value: string | null | undefined): string {
  if (!value) return "Possible safety incident";
  return value.replaceAll("_", " ");
}

function stageIndex(stage: PipelineStage): number {
  const idx = STAGE_LABELS.findIndex((item) => item.id === stage);
  return idx >= 0 ? idx : 0;
}

export function VideoAnalysisWorkspace({
  assetCode,
  jobCode,
  onReady,
  onStateChange,
}: VideoAnalysisWorkspaceProps) {
  const [video, setVideo] = useState<VideoAsset | null>(null);
  const [job, setJob] = useState<ProcessingJobView | null>(null);
  const [frames, setFrames] = useState<VideoFrameItem[]>([]);
  const [selectedFrameCode, setSelectedFrameCode] = useState<string | null>(null);
  const [seekSeconds, setSeekSeconds] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [providerLabel, setProviderLabel] = useState("Demo AI (simulated)");
  const [analysis, setAnalysis] = useState<IncidentAnalysisView | null>(null);
  const [workflow, setWorkflow] = useState<ApiWorkflowStatus | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [failedStage, setFailedStage] = useState<PipelineStage | null>(null);
  const onReadyRef = useRef(onReady);
  const onStateChangeRef = useRef(onStateChange);
  const autoPipelineStartedRef = useRef(false);

  useEffect(() => {
    onReadyRef.current = onReady;
  }, [onReady]);

  useEffect(() => {
    onStateChangeRef.current = onStateChange;
  }, [onStateChange]);

  useEffect(() => {
    autoPipelineStartedRef.current = false;
    const timer = window.setTimeout(() => {
      setAnalysis(null);
      setWorkflow(null);
      setPipelineError(null);
      setFailedStage(null);
      setAnalyzing(false);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [assetCode, jobCode]);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void fetchAIProvider()
        .then((info) => {
          if (!cancelled) setProviderLabel(info.label);
        })
        .catch(() => {
          if (!cancelled) setProviderLabel("Demo AI (simulated)");
        });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, []);

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
      return { mappedJob, mappedVideo };
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh processing status.");
      return null;
    }
  }, [assetCode, jobCode, loadFrames]);

  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;

    async function poll() {
      const result = await refresh();
      if (cancelled || !result) return;
      if (
        result.mappedJob.status === "completed" ||
        result.mappedJob.status === "failed"
      ) {
        return;
      }
      timer = window.setTimeout(() => {
        void poll();
      }, 1000);
    }

    const start = window.setTimeout(() => {
      void poll();
    }, 0);

    return () => {
      cancelled = true;
      window.clearTimeout(start);
      if (timer) window.clearTimeout(timer);
    };
  }, [refresh]);

  const pollAnalysis = useCallback(async (analysisCode: string) => {
    const deadline = Date.now() + 90000;
    while (Date.now() < deadline) {
      const mapped = mapIncidentAnalysis(await fetchAnalysis(analysisCode));
      setAnalysis(mapped);
      if (
        mapped.status === "completed" ||
        mapped.status === "needs_review" ||
        mapped.status === "failed"
      ) {
        return mapped;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 800));
    }
    throw new Error("Analysis timed out. Use Retry to continue.");
  }, []);

  const refreshWorkflow = useCallback(async (analysisCode: string) => {
    try {
      const status = await fetchWorkflowStatus(analysisCode);
      setWorkflow(status);
      return status;
    } catch {
      return null;
    }
  }, []);

  const runPipeline = useCallback(
    async (forceNew = false) => {
      setAnalyzing(true);
      setPipelineError(null);
      setFailedStage(null);
      try {
        const started = await startVideoAnalysis(assetCode, forceNew);
        setAnalysis({
          id: "",
          analysisCode: started.analysis_code,
          videoAssetCode: assetCode,
          status: started.status,
          providerName: started.provider_name,
          isDemo: started.is_demo,
          isSimulated: started.is_simulated,
          providerLabel: started.is_demo
            ? "Demo AI (simulated)"
            : `${started.provider_name} (real provider)`,
          incidentDetected: null,
          incidentType: null,
          summary: null,
          detailedAnalysis: null,
          severity: null,
          confidence: null,
          recommendedActions: [],
          limitations: [],
          inconclusive: false,
          requiredPpe: [],
          observedPpe: [],
          possiblyMissingPpe: [],
          analysisMode: null,
          humanReviewRequired: true,
          errorCode: null,
          errorMessage: null,
          evidence: [],
          review: null,
          humanApprovalRequired: true,
        });
        const completed = await pollAnalysis(started.analysis_code);
        if (completed.status === "failed") {
          setFailedStage("analyzing");
          setPipelineError(
            completed.errorMessage ?? "Analysis failed. Retry to continue."
          );
          return;
        }
        if (completed.incidentDetected) {
          const status = await refreshWorkflow(started.analysis_code);
          if (
            status &&
            !status.plan_code &&
            status.pipeline_status !== "awaiting_human_review" &&
            status.pipeline_status !== "ready_for_approval"
          ) {
            // Give prepare a moment if still catching up.
            await new Promise((resolve) => window.setTimeout(resolve, 600));
            await refreshWorkflow(started.analysis_code);
          }
        }
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : "Automatic analysis failed.";
        setFailedStage("analyzing");
        setPipelineError(message);
      } finally {
        setAnalyzing(false);
      }
    },
    [assetCode, pollAnalysis, refreshWorkflow]
  );

  const ready = Boolean(
    job?.status === "completed" && video?.status === "ready"
  );
  const processingFailed =
    job?.status === "failed" || video?.status === "failed";

  // Auto-continue when frames are ready (backend usually already started).
  useEffect(() => {
    if (!ready || processingFailed || autoPipelineStartedRef.current) return;
    autoPipelineStartedRef.current = true;

    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          const existing = await fetchVideoAnalyses(assetCode);
          const latest = existing.data.find((item) =>
            ["queued", "running", "completed", "needs_review"].includes(item.status)
          );
          if (latest) {
            setAnalyzing(
              latest.status === "queued" || latest.status === "running"
            );
            const mapped = await pollAnalysis(latest.analysis_code);
            setAnalyzing(false);
            if (mapped.status === "failed") {
              setFailedStage("analyzing");
              setPipelineError(mapped.errorMessage ?? "Analysis failed.");
              return;
            }
            if (mapped.incidentDetected) {
              await refreshWorkflow(latest.analysis_code);
            }
            return;
          }
          await runPipeline(false);
        } catch (err) {
          setAnalyzing(false);
          setFailedStage("analyzing");
          setPipelineError(
            err instanceof Error ? err.message : "Could not start analysis."
          );
        }
      })();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [
    ready,
    processingFailed,
    assetCode,
    pollAnalysis,
    refreshWorkflow,
    runPipeline,
  ]);

  const analysisDone =
    analysis?.status === "completed" || analysis?.status === "needs_review";
  const incidentDetected = Boolean(analysis?.incidentDetected);
  const processing = Boolean(job && !ready && !processingFailed);

  const pipelineStage: PipelineStage = (() => {
    if (processingFailed || failedStage === "preparing_video") return "failed";
    if (pipelineError && failedStage === "analyzing") return "failed";
    if (!job) return "evidence_received";
    if (processing) {
      const step = (job.currentStep ?? "").toLowerCase();
      if (step.includes("frame") || step.includes("extract") || job.progress >= 40) {
        return "extracting_frames";
      }
      return "preparing_video";
    }
    if (analyzing || analysis?.status === "queued" || analysis?.status === "running") {
      return "analyzing";
    }
    if (analysisDone && analysis && !incidentDetected) return "no_incident";
    if (analysisDone && incidentDetected) {
      const status = workflow?.pipeline_status;
      if (
        status === "awaiting_human_review" ||
        status === "ready_for_approval" ||
        workflow?.plan_code
      ) {
        return "human_review_required";
      }
      if (status === "preparing_response_plan" || workflow?.retrieval_code) {
        return "preparing_response";
      }
      if (status === "preparing_company_procedure") {
        return "matching_procedure";
      }
      if (workflow?.plan_code) return "human_review_required";
      if (workflow?.retrieval_code) return "preparing_response";
      return "matching_procedure";
    }
    if (ready) return "analyzing";
    return "evidence_received";
  })();

  useEffect(() => {
    onStateChangeRef.current?.({
      processing,
      ready,
      analyzing,
      failed: processingFailed || pipelineStage === "failed",
      incidentDetected,
      analysisId: analysis?.id || null,
      analysisCode: analysis?.analysisCode || null,
      videoAssetCode: video?.assetCode ?? assetCode,
      cameraId: video?.cameraId ?? null,
      pipelineStage,
    });
  }, [
    processing,
    ready,
    analyzing,
    processingFailed,
    incidentDetected,
    analysis?.id,
    analysis?.analysisCode,
    video?.assetCode,
    video?.cameraId,
    assetCode,
    pipelineStage,
  ]);

  const reviewHref =
    incidentDetected && analysis
      ? buildResponseHref({
          analysis_id: analysis.analysisCode || analysis.id,
          video_id: video?.assetCode ?? assetCode,
          camera_id: video?.cameraId,
          incident_id: workflow?.incident_code,
        })
      : null;

  const cameraLabel = video?.cameraName ?? "Camera 03";
  const activeStageIndex = stageIndex(
    pipelineStage === "failed" || pipelineStage === "no_incident"
      ? "analyzing"
      : pipelineStage
  );

  async function handleRetry() {
    setPipelineError(null);
    setFailedStage(null);
    if (processingFailed) {
      autoPipelineStartedRef.current = false;
      await refresh();
      return;
    }
    await runPipeline(true);
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="mb-1 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-foreground">
              SafetyLens is reviewing {cameraLabel}
            </h3>
            <p className="mt-1 text-xs text-muted-foreground">
              For this demonstration, uploading a clip simulates the event handoff from an
              existing facility camera.{" "}
              <span className="text-foreground">Recorded Demo Feed</span>
              {" · "}
              <span className="text-foreground">
                {analysis?.analysisMode === "configured_demo"
                  ? "Configured PPE Demo · Human verification required"
                  : analysis && !analysis.isDemo
                    ? "Multimodal analysis · Human verification required"
                    : "Demo AI analysis · Human verification required"}
              </span>
            </p>
          </div>
          {pipelineStage === "human_review_required" && reviewHref ? (
            <Button size="sm" render={<Link href={reviewHref} />}>
              Review Incident
            </Button>
          ) : null}
        </div>

        <ol className="mt-4 space-y-2">
          {STAGE_LABELS.map((stage, index) => {
            const done =
              pipelineStage === "human_review_required" ||
              pipelineStage === "no_incident"
                ? index <= stageIndex("human_review_required") ||
                  (pipelineStage === "no_incident" && index <= stageIndex("analyzing"))
                : index < activeStageIndex;
            const current =
              pipelineStage !== "failed" &&
              pipelineStage !== "no_incident" &&
              index === activeStageIndex;
            const noIncidentStop =
              pipelineStage === "no_incident" && index > stageIndex("analyzing");

            if (noIncidentStop) return null;

            return (
              <li
                key={stage.id}
                className={cn(
                  "flex items-center gap-2 text-sm",
                  done
                    ? "text-emerald-300"
                    : current
                      ? "text-sky-200"
                      : "text-muted-foreground"
                )}
              >
                {done ? (
                  <CheckCircle2 className="size-4 shrink-0" aria-hidden="true" />
                ) : current ? (
                  <Loader2 className="size-4 shrink-0 animate-spin" aria-hidden="true" />
                ) : (
                  <Circle className="size-3.5 shrink-0 opacity-50" aria-hidden="true" />
                )}
                <span>{stage.label}</span>
              </li>
            );
          })}
        </ol>

        {pipelineStage === "no_incident" && analysisDone ? (
          <p className="mt-4 text-sm text-muted-foreground">
            Analysis completed — no incident requiring operator response.
          </p>
        ) : null}

        {(processingFailed || pipelineError) && (
          <div
            className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-red-200"
            role="alert"
          >
            <p className="font-medium">
              {processingFailed ? "Video preparation failed" : "Automatic review paused"}
            </p>
            <p className="mt-1 text-xs opacity-90">
              {processingFailed
                ? job?.errorMessage ?? error ?? "Processing failed."
                : pipelineError}
            </p>
            <Button
              className="mt-3"
              size="sm"
              variant="outline"
              onClick={() => void handleRetry()}
              disabled={analyzing}
            >
              <RefreshCw data-icon="inline-start" />
              Retry
            </Button>
          </div>
        )}

        {pipelineStage === "human_review_required" && analysis && reviewHref ? (
          <div
            className="mt-4 rounded-lg border border-red-500/50 bg-red-500/10 p-3"
            role="alert"
          >
            <p className="text-sm font-semibold capitalize text-red-100">
              {formatIncidentType(analysis.incidentType)} event
            </p>
            <p className="mt-1 text-xs text-red-200/90">
              {cameraLabel} · {video?.location ?? "Warehouse Aisle"}
            </p>
            <p className="mt-1 text-xs text-red-200/80">
              {(analysis.severity ?? "high").replace(/^./, (c) => c.toUpperCase())} severity
              {" · "}
              {analysis.analysisMode === "configured_demo"
                ? "Configured scenario"
                : `${confidencePercent(analysis.confidence)} confidence`}
              {" · "}
              Review required
            </p>
            <div className="mt-3">
              <Button size="sm" render={<Link href={reviewHref} />}>
                Review Incident
              </Button>
            </div>
          </div>
        ) : null}
      </section>

      {video?.contentUrl ? (
        <VideoPlayerPanel
          contentUrl={video.contentUrl}
          cameraName={cameraLabel}
          location={video.location}
          seekSeconds={seekSeconds}
        />
      ) : null}

      <details className="rounded-xl border border-border bg-panel/80 p-4">
        <summary className="cursor-pointer text-sm font-medium text-muted-foreground">
          Developer tools
        </summary>
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            <span className="rounded-md border border-border px-2 py-1 font-mono">
              {assetCode}
            </span>
            <span className="rounded-md border border-border px-2 py-1 font-mono">
              {job?.jobCode ?? jobCode}
            </span>
            {analysis?.analysisCode ? (
              <span className="rounded-md border border-border px-2 py-1 font-mono">
                {analysis.analysisCode}
              </span>
            ) : null}
            <span className="rounded-md border border-border px-2 py-1">
              {providerLabel}
            </span>
            <span className="rounded-md border border-border px-2 py-1">
              Progress {job?.progress ?? 0}%
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={!ready || analyzing}
              onClick={() => void runPipeline(true)}
            >
              <Sparkles data-icon="inline-start" />
              Re-analyze
            </Button>
            <Button size="sm" variant="ghost" onClick={() => void refresh()}>
              <RefreshCw data-icon="inline-start" />
              Refresh status
            </Button>
          </div>

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

          {analysis?.limitations && analysis.limitations.length > 0 ? (
            <div className="rounded-lg border border-border/80 bg-background/30 p-3">
              <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                <AlertTriangle className="size-3.5" />
                Model limitations
              </div>
              <ul className="list-disc space-y-1 pl-5 text-xs text-muted-foreground">
                {analysis.limitations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {analysis?.detailedAnalysis ? (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Detailed analysis
              </h4>
              <p className="mt-1 text-sm text-muted-foreground">
                {analysis.detailedAnalysis}
              </p>
            </div>
          ) : null}
        </div>
      </details>
    </div>
  );
}
