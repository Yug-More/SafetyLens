"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, RefreshCw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FrameTimeline, VideoPlayerPanel } from "@/components/FrameTimeline";
import {
  fetchAnalysis,
  fetchAIProvider,
  fetchProcessingJob,
  fetchVideo,
  fetchVideoFrames,
  startVideoAnalysis,
  submitAnalysisReview,
} from "@/lib/api";
import { ApiError } from "@/lib/api/client";
import {
  mapIncidentAnalysis,
  mapProcessingJob,
  mapVideoAsset,
  mapVideoFrame,
} from "@/lib/api/mappers";
import type {
  IncidentAnalysisView,
  ProcessingJobView,
  ReviewDecision,
  VideoAsset,
  VideoFrameItem,
} from "@/types/video";
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
  const [providerLabel, setProviderLabel] = useState("Demo AI (simulated)");
  const [analysis, setAnalysis] = useState<IncidentAnalysisView | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewSaving, setReviewSaving] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const onReadyRef = useRef(onReady);

  useEffect(() => {
    onReadyRef.current = onReady;
  }, [onReady]);

  useEffect(() => {
    let cancelled = false;
    void fetchAIProvider()
      .then((info) => {
        if (!cancelled) setProviderLabel(info.label);
      })
      .catch(() => {
        if (!cancelled) setProviderLabel("Demo AI (simulated)");
      });
    return () => {
      cancelled = true;
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

  const pollAnalysis = useCallback(async (analysisCode: string) => {
    const deadline = Date.now() + 60000;
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
    throw new Error("Analysis timed out. Refresh and try again.");
  }, []);

  const handleAnalyze = useCallback(async () => {
    setAnalyzing(true);
    setAnalysisError(null);
    setReviewError(null);
    try {
      const started = await startVideoAnalysis(assetCode);
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
        errorCode: null,
        errorMessage: null,
        evidence: [],
        review: null,
        humanApprovalRequired: true,
      });
      await pollAnalysis(started.analysis_code);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Analysis failed.";
      setAnalysisError(message);
    } finally {
      setAnalyzing(false);
    }
  }, [assetCode, pollAnalysis]);

  const handleReview = useCallback(
    async (decision: Exclude<ReviewDecision, "pending">) => {
      if (!analysis) return;
      setReviewSaving(true);
      setReviewError(null);
      try {
        const updated = mapIncidentAnalysis(
          await submitAnalysisReview(analysis.analysisCode, {
            decision,
            reviewerName: "demo-reviewer",
            notes: reviewNotes.trim() || undefined,
          })
        );
        setAnalysis(updated);
      } catch (err) {
        setReviewError(
          err instanceof Error ? err.message : "Could not save human review."
        );
      } finally {
        setReviewSaving(false);
      }
    },
    [analysis, reviewNotes]
  );

  const progress = job?.progress ?? 0;
  const failed = job?.status === "failed" || video?.status === "failed";
  const ready = job?.status === "completed" && video?.status === "ready";
  const analysisDone =
    analysis?.status === "completed" || analysis?.status === "needs_review";

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

      {ready ? (
        <section className="rounded-xl border border-border bg-panel p-4 shadow-sm">
          <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-foreground">
                Multimodal Analysis
              </h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Analyzes selected extracted frames. Provider:{" "}
                <span className="text-foreground">{providerLabel}</span>. Critical
                actions stay human-approved.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => void handleAnalyze()}
              disabled={analyzing}
            >
              <Sparkles data-icon="inline-start" />
              {analyzing ? "Analyzing…" : analysis ? "Re-analyze" : "Analyze frames"}
            </Button>
          </div>

          {analysisError ? (
            <div
              className="mb-3 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-red-200"
              role="alert"
            >
              <p className="font-medium">Analysis could not complete</p>
              <p className="mt-1 text-xs opacity-90">{analysisError}</p>
              <Button
                className="mt-3"
                size="sm"
                variant="outline"
                onClick={() => void handleAnalyze()}
                disabled={analyzing}
              >
                Try again
              </Button>
            </div>
          ) : null}

          {analyzing && !analysisDone ? (
            <p className="text-xs text-muted-foreground" aria-live="polite">
              Running {providerLabel} on selected frames…
            </p>
          ) : null}

          {!analysis && !analyzing && !analysisError ? (
            <p className="text-xs text-muted-foreground">
              No analysis yet. Start analysis after frames are ready.
            </p>
          ) : null}

          {analysis ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="rounded-md border border-border px-2 py-1">
                  {analysis.analysisCode || "…"}
                </span>
                <span className="rounded-md border border-border px-2 py-1">
                  {analysis.providerLabel}
                </span>
                <span className="rounded-md border border-border px-2 py-1 capitalize">
                  status: {analysis.status.replaceAll("_", " ")}
                </span>
                {analysis.isDemo || analysis.isSimulated ? (
                  <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-amber-100">
                    Simulated / demo result
                  </span>
                ) : (
                  <span className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 text-emerald-100">
                    Real provider
                  </span>
                )}
              </div>

              {analysis.status === "failed" ? (
                <div className="rounded-lg border border-destructive/40 p-3 text-sm" role="alert">
                  <p className="font-medium text-red-200">
                    {analysis.errorMessage ?? "Analysis failed."}
                  </p>
                  <Button
                    className="mt-3"
                    size="sm"
                    variant="outline"
                    onClick={() => void handleAnalyze()}
                    disabled={analyzing}
                  >
                    Retry analysis
                  </Button>
                </div>
              ) : null}

              {analysisDone ? (
                <>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <Metric
                      label="Incident detected"
                      value={
                        analysis.inconclusive
                          ? "Inconclusive"
                          : analysis.incidentDetected
                            ? "Yes"
                            : "No"
                      }
                    />
                    <Metric
                      label="Severity"
                      value={analysis.severity ?? "none"}
                    />
                    <Metric
                      label="Confidence"
                      value={
                        analysis.confidence == null
                          ? "—"
                          : `${Math.round(analysis.confidence * 100)}%`
                      }
                    />
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Summary
                    </h4>
                    <p className="mt-1 text-sm text-foreground">
                      {analysis.summary ?? "No summary returned."}
                    </p>
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Detailed analysis
                    </h4>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {analysis.detailedAnalysis ?? "No details returned."}
                    </p>
                  </div>

                  <div>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Evidence timestamps
                    </h4>
                    {analysis.evidence.length === 0 ? (
                      <p className="text-xs text-muted-foreground">
                        No evidence frames were linked.
                      </p>
                    ) : (
                      <ul className="space-y-2">
                        {analysis.evidence.map((item) => (
                          <li key={item.id}>
                            <button
                              type="button"
                              className="w-full rounded-lg border border-border bg-background/40 p-3 text-left transition hover:border-primary/50"
                              onClick={() => {
                                setSelectedFrameCode(item.frameCode);
                                setSeekSeconds(item.timestampSeconds);
                              }}
                            >
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <span className="text-xs font-medium text-foreground">
                                  {item.frameCode} · {item.timestampSeconds.toFixed(1)}s
                                </span>
                                <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
                                  {item.relevance}
                                </span>
                              </div>
                              <p className="mt-1 text-xs text-muted-foreground">
                                {item.observation}
                              </p>
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {analysis.recommendedActions.length > 0 ? (
                    <div>
                      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Recommended actions (require approval)
                      </h4>
                      <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                        {analysis.recommendedActions.map((action) => (
                          <li key={action}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  {analysis.limitations.length > 0 ? (
                    <div className="rounded-lg border border-border/80 bg-background/30 p-3">
                      <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-muted-foreground">
                        <AlertTriangle className="size-3.5" />
                        Limitations
                      </div>
                      <ul className="list-disc space-y-1 pl-5 text-xs text-muted-foreground">
                        {analysis.limitations.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  <div className="rounded-lg border border-border p-3">
                    <h4 className="text-sm font-semibold text-foreground">
                      Human review
                    </h4>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Critical response actions remain pending until a reviewer
                      confirms or rejects this analysis.
                    </p>
                    {analysis.review && analysis.review.decision !== "pending" ? (
                      <div className="mt-3 flex items-start gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-100">
                        <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
                        <div>
                          <p className="font-medium capitalize">
                            {analysis.review.decision.replaceAll("_", " ")} by{" "}
                            {analysis.review.reviewerName}
                          </p>
                          {analysis.review.notes ? (
                            <p className="mt-1 text-xs opacity-90">
                              {analysis.review.notes}
                            </p>
                          ) : null}
                        </div>
                      </div>
                    ) : (
                      <div className="mt-3 space-y-3">
                        <label className="block text-xs text-muted-foreground">
                          Reviewer notes
                          <textarea
                            className="mt-1 min-h-20 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                            value={reviewNotes}
                            onChange={(event) => setReviewNotes(event.target.value)}
                            placeholder="Optional notes for the audit trail"
                          />
                        </label>
                        <div className="flex flex-wrap gap-2">
                          <Button
                            size="sm"
                            disabled={reviewSaving}
                            onClick={() => void handleReview("confirmed")}
                          >
                            Confirm
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={reviewSaving}
                            onClick={() => void handleReview("rejected")}
                          >
                            Reject
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            disabled={reviewSaving}
                            onClick={() => void handleReview("needs_more_info")}
                          >
                            Needs more info
                          </Button>
                        </div>
                      </div>
                    )}
                    {reviewError ? (
                      <p className="mt-2 text-xs text-red-300" role="alert">
                        {reviewError}
                      </p>
                    ) : null}
                  </div>
                </>
              ) : null}
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-background/40 p-3">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-sm font-medium capitalize text-foreground">{value}</p>
    </div>
  );
}
