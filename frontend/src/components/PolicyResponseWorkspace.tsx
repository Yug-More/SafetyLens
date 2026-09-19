"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  FileDown,
  FileWarning,
  Loader2,
  RefreshCw,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog } from "@/components/ConfirmationDialog";
import { ConnectionBanner, PanelSkeleton } from "@/components/ConnectionBanner";
import { EmptyState } from "@/components/EmptyState";
import { SeverityBadge } from "@/components/SeverityBadge";
import { ApiError, resolveMediaUrl } from "@/lib/api/client";
import {
  approveResponsePlan,
  executeResponsePlan,
  fetchAnalysis,
  fetchIncidentAudit,
  fetchIncidentReports,
  fetchPlanExecutions,
  fetchResponsePlan,
  fetchVideo,
  fetchVideoAnalyses,
  fetchVideos,
  fetchWorkflowStatus,
  generateIncidentReport,
  getReportDownloadUrl,
  prepareAnalysisResponse,
  rejectResponsePlan,
  retryExecution,
  submitAnalysisReview,
} from "@/lib/api";
import type {
  ApiActionExecution,
  ApiAuditEvent,
  ApiIncidentAnalysis,
  ApiIncidentReport,
  ApiResponsePlan,
  ApiVideoAsset,
  ApiWorkflowStatus,
} from "@/lib/api/types";
import {
  buildResponseHref,
  parseIncidentContext,
} from "@/lib/incident-context";
import { formatRelativeTime } from "@/lib/api/mappers";
import type { IncidentSeverity } from "@/types";

function formatIncidentType(value: string | null | undefined): string {
  if (!value) return "Possible incident";
  return value.replaceAll("_", " ");
}

function toBadgeSeverity(
  value: string | null | undefined
): IncidentSeverity | null {
  if (!value || value === "none") return null;
  if (value === "critical") return "high";
  if (value === "high" || value === "medium" || value === "low") return value;
  return null;
}

function confidencePercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

function topEvidence(
  items: ApiIncidentAnalysis["evidence"],
  max = 3
): ApiIncidentAnalysis["evidence"] {
  const rank = (relevance: string) =>
    ({ supporting: 0, context: 1, contradicting: 2 })[relevance] ?? 3;
  return [...items]
    .sort(
      (a, b) =>
        rank(a.relevance) - rank(b.relevance) ||
        b.timestamp_seconds - a.timestamp_seconds
    )
    .slice(0, max);
}

function uniqueProcedureCitations(plan: ApiResponsePlan | null) {
  if (!plan) return [];
  const seen = new Set<string>();
  const citations: Array<{
    id: string;
    procedure_code: string | null;
    procedure_title: string | null;
    section_heading: string | null;
    excerpt: string;
  }> = [];
  for (const action of plan.actions) {
    for (const cite of action.citations) {
      const key = cite.procedure_code ?? cite.id;
      if (seen.has(key)) continue;
      seen.add(key);
      citations.push(cite);
    }
  }
  return citations.slice(0, 3);
}

export function PolicyResponseWorkspace() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const context = useMemo(
    () => parseIncidentContext(searchParams),
    [searchParams]
  );

  const [analysis, setAnalysis] = useState<ApiIncidentAnalysis | null>(null);
  const [video, setVideo] = useState<ApiVideoAsset | null>(null);
  const [workflow, setWorkflow] = useState<ApiWorkflowStatus | null>(null);
  const [plan, setPlan] = useState<ApiResponsePlan | null>(null);
  const [selectedActionIds, setSelectedActionIds] = useState<string[]>([]);
  const [approvalNotes, setApprovalNotes] = useState("");
  const [executions, setExecutions] = useState<ApiActionExecution[]>([]);
  const [audit, setAudit] = useState<ApiAuditEvent[]>([]);
  const [report, setReport] = useState<ApiIncidentReport | null>(null);
  const [activeCitation, setActiveCitation] = useState<string | null>(null);

  const [videos, setVideos] = useState<ApiVideoAsset[]>([]);
  const [analyses, setAnalyses] = useState<ApiIncidentAnalysis[]>([]);
  const [switcherOpen, setSwitcherOpen] = useState(false);

  const [loading, setLoading] = useState(true);
  const [preparing, setPreparing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [approveOpen, setApproveOpen] = useState(false);
  const [executeOpen, setExecuteOpen] = useState(false);

  const analysisId = context.analysis_id ?? null;
  const videoId = context.video_id ?? null;

  const reviewDecision =
    workflow?.review_decision ?? analysis?.review?.decision ?? null;
  const isConfirmed = reviewDecision === "confirmed";
  const isRejected = reviewDecision === "rejected";
  const isNeedsMoreInfo = reviewDecision === "needs_more_info";
  const canReview = !reviewDecision || reviewDecision === "pending";
  const incidentCode = workflow?.incident_code ?? null;

  const badgeSeverity = toBadgeSeverity(
    analysis?.severity ?? workflow?.severity
  );

  const refreshAudit = useCallback(async (code: string | null) => {
    if (!code) return;
    try {
      const response = await fetchIncidentAudit(code);
      setAudit(response.data);
    } catch {
      // Audit may be empty before incident is linked.
    }
  }, []);

  const loadPlanAndExecutions = useCallback(
    async (planCode: string | null | undefined) => {
      if (!planCode) {
        setPlan(null);
        setExecutions([]);
        return;
      }
      const loadedPlan = await fetchResponsePlan(planCode);
      setPlan(loadedPlan);
      setSelectedActionIds(loadedPlan.actions.map((action) => action.id));
      if (
        loadedPlan.execution_status &&
        loadedPlan.execution_status !== "none"
      ) {
        const execRes = await fetchPlanExecutions(planCode);
        setExecutions(execRes.data);
      } else {
        setExecutions([]);
      }
    },
    []
  );

  const loadIncident = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    setActionError(null);

    try {
      if (!analysisId && !videoId) {
        const videoRes = await fetchVideos({ status: "ready", limit: 20 });
        setVideos(videoRes.data);
        setAnalysis(null);
        setVideo(null);
        setWorkflow(null);
        setPlan(null);
        setExecutions([]);
        setReport(null);
        setAudit([]);
        setAnalyses([]);
        setLoading(false);
        return;
      }

      let loadedAnalysis: ApiIncidentAnalysis | null = null;
      let loadedVideo: ApiVideoAsset | null = null;
      let loadedWorkflow: ApiWorkflowStatus | null = null;

      if (analysisId) {
        loadedAnalysis = await fetchAnalysis(analysisId);

        const resolvedVideoId =
          videoId ?? loadedAnalysis.video_asset_code ?? null;
        if (resolvedVideoId) {
          loadedVideo = await fetchVideo(resolvedVideoId);
        }

        setPreparing(true);
        try {
          loadedWorkflow = await prepareAnalysisResponse(analysisId);
        } catch {
          loadedWorkflow = await fetchWorkflowStatus(analysisId);
        } finally {
          setPreparing(false);
        }

        if (!loadedWorkflow) {
          loadedWorkflow = await fetchWorkflowStatus(analysisId);
        }

        await loadPlanAndExecutions(loadedWorkflow.plan_code);

        if (loadedWorkflow.incident_code) {
          await refreshAudit(loadedWorkflow.incident_code);
          try {
            const reports = await fetchIncidentReports(
              loadedWorkflow.incident_code
            );
            const sorted = [...reports.data].sort(
              (a, b) =>
                new Date(b.generated_at).getTime() -
                new Date(a.generated_at).getTime()
            );
            if (sorted[0]) setReport(sorted[0]);
          } catch {
            // Reports may not exist yet.
          }
        }
      } else if (videoId) {
        loadedVideo = await fetchVideo(videoId);
        const analysesRes = await fetchVideoAnalyses(videoId);
        setAnalyses(
          analysesRes.data.filter((item) =>
            ["completed", "needs_review"].includes(item.status)
          )
        );
      }

      setAnalysis(loadedAnalysis);
      setVideo(loadedVideo);
      setWorkflow(loadedWorkflow);

      const videoRes = await fetchVideos({ status: "ready", limit: 20 });
      setVideos(videoRes.data);
      if (loadedVideo) {
        const analysesRes = await fetchVideoAnalyses(loadedVideo.asset_code);
        setAnalyses(
          analysesRes.data.filter((item) =>
            ["completed", "needs_review"].includes(item.status)
          )
        );
      }
    } catch (err) {
      setLoadError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Unable to load incident context."
      );
      setAnalysis(null);
      setVideo(null);
      setWorkflow(null);
    } finally {
      setLoading(false);
    }
  }, [analysisId, videoId, loadPlanAndExecutions, refreshAudit]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadIncident();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadIncident]);

  async function handleReview(
    decision: "confirmed" | "rejected" | "needs_more_info"
  ) {
    if (!analysis) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await submitAnalysisReview(analysis.analysis_code, {
        decision,
        reviewerName: "demo-reviewer",
      });
      setAnalysis(updated);
      const wf = await fetchWorkflowStatus(analysis.analysis_code);
      setWorkflow(wf);
      await loadPlanAndExecutions(wf.plan_code);
      if (wf.incident_code) await refreshAudit(wf.incident_code);
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Review submission failed."
      );
    } finally {
      setBusy(false);
    }
  }

  async function confirmApprove() {
    if (!plan || !incidentCode) return;
    setBusy(true);
    setActionError(null);
    try {
      await approveResponsePlan(plan.plan_code, {
        selectedActionIds,
        reviewerName: "demo-reviewer",
        notes: approvalNotes || undefined,
        incidentIdentifier: incidentCode,
        confirmed: true,
      });
      await loadPlanAndExecutions(plan.plan_code);
      await refreshAudit(incidentCode);
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Approval failed."
      );
    } finally {
      setBusy(false);
      setApproveOpen(false);
    }
  }

  async function handleRejectPlan() {
    if (!plan || !incidentCode) return;
    setBusy(true);
    setActionError(null);
    try {
      await rejectResponsePlan(plan.plan_code, {
        reviewerName: "demo-reviewer",
        reason: approvalNotes || "Rejected in demo review",
      });
      await loadPlanAndExecutions(plan.plan_code);
      await refreshAudit(incidentCode);
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Rejection failed."
      );
    } finally {
      setBusy(false);
    }
  }

  async function confirmExecute() {
    if (!plan || !incidentCode) return;
    setBusy(true);
    setActionError(null);
    try {
      const result = await executeResponsePlan(plan.plan_code);
      setExecutions(result.executions);
      await loadPlanAndExecutions(plan.plan_code);
      await refreshAudit(incidentCode);
      try {
        const reports = await fetchIncidentReports(incidentCode);
        const sorted = [...reports.data].sort(
          (a, b) =>
            new Date(b.generated_at).getTime() -
            new Date(a.generated_at).getTime()
        );
        if (sorted[0]) setReport(sorted[0]);
      } catch {
        // Report generation may lag; manual generate remains available.
      }
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Execution failed."
      );
    } finally {
      setBusy(false);
      setExecuteOpen(false);
    }
  }

  async function handleRetry(executionCode: string) {
    if (!plan || !incidentCode) return;
    setBusy(true);
    setActionError(null);
    try {
      await retryExecution(executionCode);
      const response = await fetchPlanExecutions(plan.plan_code);
      setExecutions(response.data);
      await loadPlanAndExecutions(plan.plan_code);
      await refreshAudit(incidentCode);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Retry failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleReport() {
    if (!incidentCode) return;
    setBusy(true);
    setActionError(null);
    try {
      const result = await generateIncidentReport(
        incidentCode,
        plan?.plan_code,
        true
      );
      setReport(result);
      await refreshAudit(incidentCode);
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Report generation failed."
      );
    } finally {
      setBusy(false);
    }
  }

  function navigateToContext(next: {
    video_id?: string;
    analysis_id?: string;
  }) {
    router.push(buildResponseHref(next));
  }

  const canApprove =
    isConfirmed &&
    !isRejected &&
    !isNeedsMoreInfo &&
    plan?.status === "completed" &&
    (plan.approval_status === "pending" || !plan.approval_status) &&
    (plan.execution_status === "none" || !plan.execution_status);

  const canExecute =
    isConfirmed &&
    !isRejected &&
    !isNeedsMoreInfo &&
    (plan?.approval_status === "approved" ||
      plan?.approval_status === "partially_approved");

  const procedureCitations = uniqueProcedureCitations(plan);
  const evidenceItems = topEvidence(analysis?.evidence ?? []);
  const videoUrl = video?.content_url
    ? resolveMediaUrl(video.content_url)
    : null;
  const detectionTime =
    analysis?.completed_at ?? analysis?.created_at ?? null;
  const locationLabel =
    video?.location ?? workflow?.location ?? "—";
  const cameraLabel =
    video?.camera_name ??
    video?.camera_id ??
    workflow?.camera_name ??
    workflow?.camera_id ??
    "—";
  const statusMessage =
    workflow?.message ??
    (preparing
      ? "Preparing draft response…"
      : "Draft response prepared — awaiting incident confirmation");

  if (loading) {
    return <PanelSkeleton className="min-h-96" />;
  }

  if (loadError) {
    return (
      <div className="space-y-4">
        <ConnectionBanner
          mode="error"
          message={loadError}
          onRetry={() => void loadIncident()}
        />
        <EmptyState
          title="Incident not found"
          description={loadError}
          actionLabel="Retry"
          onAction={() => void loadIncident()}
        />
        <div className="flex justify-center">
          <Button variant="outline" nativeButton={false} render={<Link href="/monitor" />}>
            Go to Live Monitor
          </Button>
        </div>
      </div>
    );
  }

  if (!analysisId && !videoId) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="No incident selected"
          description="Open an analysis from Live Monitor or use a notification link to review a flagged incident."
          actionLabel="Go to Live Monitor"
          onAction={() => router.push("/monitor")}
        />
        <SwitcherSection
          open={switcherOpen}
          onOpenChange={setSwitcherOpen}
          videos={videos}
          analyses={analyses}
          selectedVideoId={null}
          selectedAnalysisId={null}
          onSelectVideo={(assetCode) => {
            void navigateToContext({ video_id: assetCode });
          }}
          onSelectAnalysis={(assetCode, code) => {
            void navigateToContext({ video_id: assetCode, analysis_id: code });
          }}
        />
      </div>
    );
  }

  if (videoId && !analysisId) {
    return (
      <div className="space-y-4">
        {video ? (
          <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Video selected
            </p>
            <h2 className="mt-1 text-lg font-semibold text-foreground">
              {video.asset_code}
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">{video.location}</p>
          </article>
        ) : null}
        <EmptyState
          title="Select an analysis"
          description="This video has no analysis in the URL. Choose a completed analysis below to open the Incident Command Center."
        />
        <SwitcherSection
          open
          onOpenChange={setSwitcherOpen}
          videos={videos}
          analyses={analyses}
          selectedVideoId={videoId}
          selectedAnalysisId={null}
          onSelectVideo={(assetCode) => {
            void navigateToContext({ video_id: assetCode });
          }}
          onSelectAnalysis={(assetCode, code) => {
            void navigateToContext({ video_id: assetCode, analysis_id: code });
          }}
        />
        <div className="flex justify-center">
          <Button variant="outline" nativeButton={false} render={<Link href="/monitor" />}>
            Go to Live Monitor
          </Button>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="space-y-4">
        <ConnectionBanner
          mode="error"
          message="Analysis record could not be loaded."
          onRetry={() => void loadIncident()}
        />
        <EmptyState
          title="Analysis unavailable"
          description="The requested analysis was not found or is not ready for review."
          actionLabel="Retry"
          onAction={() => void loadIncident()}
        />
        <div className="flex justify-center">
          <Button variant="outline" nativeButton={false} render={<Link href="/monitor" />}>
            Go to Live Monitor
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Primary command center — above the fold */}
      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium tracking-wide text-red-300/90 uppercase">
              {formatIncidentType(
                analysis.incident_type ?? workflow?.incident_type
              )}
            </p>
            <h2 className="mt-1 text-xl font-semibold text-foreground">
              Incident Command Center
            </h2>
            <p className="mt-1 text-xs text-amber-100">
              Demo AI analysis · Human review required
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {badgeSeverity ? <SeverityBadge severity={badgeSeverity} /> : null}
            {incidentCode ? (
              <span className="rounded-md border border-border px-2 py-1 font-mono text-[11px] text-muted-foreground">
                {incidentCode}
              </span>
            ) : null}
            <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-100">
              SIMULATED execution
            </span>
          </div>
        </div>

        <div className="mt-4 rounded-lg border border-border/60 bg-secondary/20 px-3 py-2">
          <p className="text-xs font-medium text-muted-foreground uppercase">
            Workflow status
          </p>
          <p className="mt-0.5 text-sm font-medium text-foreground">
            {statusMessage}
          </p>
          {workflow?.pipeline_status ? (
            <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
              {workflow.pipeline_status.replaceAll("_", " ")}
            </p>
          ) : null}
          {preparing ? (
            <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="size-3 animate-spin" />
              Preparing response…
            </p>
          ) : null}
        </div>

        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-muted-foreground">Camera</dt>
            <dd className="font-medium text-foreground">{cameraLabel}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Location</dt>
            <dd className="font-medium text-foreground">{locationLabel}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Detection time</dt>
            <dd className="font-medium text-foreground">
              {detectionTime
                ? `${new Date(detectionTime).toLocaleString()} (${formatRelativeTime(detectionTime)})`
                : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Severity</dt>
            <dd className="font-medium capitalize text-foreground">
              {analysis.severity ?? workflow?.severity ?? "—"}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Confidence</dt>
            <dd className="font-medium text-foreground">
              {confidencePercent(analysis.confidence ?? workflow?.confidence)}
            </dd>
          </div>
        </dl>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <section className="space-y-4">
          {videoUrl ? (
            <article className="overflow-hidden rounded-xl border border-border bg-panel shadow-sm">
              <video
                className="aspect-video w-full bg-black object-contain"
                src={videoUrl}
                controls
                preload="metadata"
              />
            </article>
          ) : null}

          <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <FileWarning className="size-4 text-warning" aria-hidden="true" />
              <h3 className="text-base font-semibold text-foreground">
                Strongest evidence
              </h3>
            </div>
            <ul className="space-y-2 text-sm leading-relaxed text-slate-200">
              {evidenceItems.map((item) => (
                <li
                  key={item.id}
                  className="rounded-lg border border-border/60 bg-secondary/25 px-3 py-2"
                >
                  <span className="font-mono text-[11px] text-muted-foreground">
                    t={item.timestamp_seconds.toFixed(1)}s · {item.frame_code}
                  </span>
                  <span className="mt-1 block">{item.observation}</span>
                </li>
              ))}
              {evidenceItems.length === 0 ? (
                <li className="text-muted-foreground">
                  No evidence items recorded for this analysis.
                </li>
              ) : null}
            </ul>
          </article>

          {analysis.summary ? (
            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <h3 className="text-base font-semibold text-foreground">
                Why SafetyLens flagged this
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-200">
                {analysis.summary}
              </p>
            </article>
          ) : null}
        </section>

        <section className="space-y-4">
          {canReview ? (
            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <h3 className="text-base font-semibold text-foreground">
                Incident confirmation
              </h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Confirm whether this AI detection represents a real incident
                requiring response.
              </p>
              {!isConfirmed ? (
                <p className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-100">
                  {statusMessage}
                </p>
              ) : null}
              <div className="mt-4 flex flex-wrap gap-2">
                <Button
                  size="sm"
                  disabled={busy || preparing}
                  onClick={() => void handleReview("confirmed")}
                >
                  <CheckCircle2 data-icon="inline-start" />
                  Confirm Incident
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy || preparing}
                  onClick={() => void handleReview("rejected")}
                >
                  <XCircle data-icon="inline-start" />
                  Reject Incident
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={busy || preparing}
                  onClick={() => void handleReview("needs_more_info")}
                >
                  <AlertTriangle data-icon="inline-start" />
                  Needs More Information
                </Button>
              </div>
            </article>
          ) : null}

          {isRejected ? (
            <article className="rounded-xl border border-destructive/40 bg-destructive/10 p-4 shadow-sm">
              <p className="text-sm font-medium text-red-200">
                Incident rejected — response actions are blocked.
              </p>
            </article>
          ) : null}

          {isNeedsMoreInfo ? (
            <article className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 shadow-sm">
              <p className="text-sm font-medium text-amber-100">
                Needs more information — response actions are blocked until
                confirmed.
              </p>
            </article>
          ) : null}

          {isConfirmed && plan ? (
            <>
              <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
                <div className="mb-3 flex items-center gap-2">
                  <ShieldAlert
                    className="size-4 text-emerald-300"
                    aria-hidden="true"
                  />
                  <h3 className="text-base font-semibold text-foreground">
                    Matched procedures
                  </h3>
                </div>
                {procedureCitations.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No policy citations linked to the response plan yet.
                  </p>
                ) : (
                  <div className="space-y-2 text-sm">
                    {procedureCitations.map((match) => (
                      <div
                        key={match.id}
                        className="rounded-lg border border-border/60 bg-secondary/25 px-3 py-2.5"
                      >
                        <p className="font-medium text-foreground">
                          {match.procedure_code}
                          {match.procedure_title
                            ? ` — ${match.procedure_title}`
                            : ""}
                        </p>
                        {match.section_heading ? (
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {match.section_heading}
                          </p>
                        ) : null}
                        <p className="mt-2 whitespace-pre-wrap text-slate-200">
                          {match.excerpt}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </article>

              <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
                <h3 className="text-base font-semibold text-foreground">
                  Response plan actions
                </h3>
                {plan.summary ? (
                  <p className="mt-2 text-sm text-muted-foreground">
                    {plan.summary}
                  </p>
                ) : null}

                <label className="mt-4 block space-y-1 text-xs text-muted-foreground">
                  Approval notes
                  <textarea
                    className="min-h-16 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                    value={approvalNotes}
                    onChange={(event) => setApprovalNotes(event.target.value)}
                    disabled={!canApprove}
                  />
                </label>

                <ul className="mt-3 space-y-2">
                  {plan.actions.map((action) => {
                    const checked = selectedActionIds.includes(action.id);
                    return (
                      <li
                        key={action.id}
                        className="rounded-lg border border-border p-3 text-sm"
                      >
                        <label className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            className="mt-1"
                            checked={checked}
                            disabled={!canApprove}
                            onChange={(event) => {
                              setSelectedActionIds((current) =>
                                event.target.checked
                                  ? [...current, action.id]
                                  : current.filter((id) => id !== action.id)
                              );
                            }}
                          />
                          <span>
                            <span className="font-medium text-foreground">
                              {action.action_order}. {action.title}
                            </span>
                            <span className="mt-1 block text-xs text-muted-foreground">
                              {action.responsible_role} · {action.priority}
                            </span>
                            <span className="mt-1 block text-slate-200">
                              {action.description}
                            </span>
                            {action.citations.map((cite) => (
                              <button
                                key={cite.id}
                                type="button"
                                className="mt-2 block text-left text-xs text-primary"
                                onClick={() =>
                                  setActiveCitation(
                                    activeCitation === cite.id ? null : cite.id
                                  )
                                }
                              >
                                Citation {cite.procedure_code}
                                {activeCitation === cite.id ? (
                                  <span className="mt-1 block whitespace-pre-wrap text-slate-300">
                                    {cite.excerpt}
                                  </span>
                                ) : null}
                              </button>
                            ))}
                          </span>
                        </label>
                      </li>
                    );
                  })}
                </ul>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    disabled={
                      !canApprove || busy || selectedActionIds.length === 0
                    }
                    onClick={() => setApproveOpen(true)}
                  >
                    Approve selected actions
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canApprove || busy}
                    onClick={() => void handleRejectPlan()}
                  >
                    Reject plan
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={!canExecute || busy}
                    onClick={() => setExecuteOpen(true)}
                  >
                    Run approved actions
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={!incidentCode || busy}
                    onClick={() => void handleReport()}
                  >
                    <FileDown data-icon="inline-start" />
                    Generate report
                  </Button>
                </div>
              </article>
            </>
          ) : isConfirmed && !plan ? (
            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <p className="text-sm text-muted-foreground">
                Response plan is still being prepared…
              </p>
            </article>
          ) : null}

          {executions.length > 0 ? (
            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <h3 className="text-sm font-semibold text-foreground">
                Simulated execution status
              </h3>
              <ul className="mt-2 space-y-2 text-sm">
                {executions.map((item) => {
                  const statusLabel =
                    item.status === "completed"
                      ? "Simulated completed"
                      : item.status === "failed"
                        ? "Simulated failed"
                        : item.status === "running"
                          ? "Simulated execution in progress"
                          : item.status;
                  return (
                    <li
                      key={item.id}
                      className="rounded-md border border-border/70 p-2"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span>
                          {item.action_title} · {statusLabel}
                        </span>
                        <span className="text-[11px] text-amber-100">
                          SIMULATED
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {item.message}
                      </p>
                      {item.status === "failed" ? (
                        <Button
                          className="mt-2"
                          size="sm"
                          variant="outline"
                          disabled={busy}
                          onClick={() => void handleRetry(item.execution_code)}
                        >
                          Retry simulated action
                        </Button>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </article>
          ) : null}

          {report ? (
            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <p className="font-medium text-foreground">{report.title}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {report.report_code} · {report.status} · SIMULATED
              </p>
              {report.download_url ? (
                <a
                  className="mt-2 inline-flex text-sm text-primary underline"
                  href={getReportDownloadUrl(report.report_code)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download PDF
                </a>
              ) : null}
            </article>
          ) : null}
        </section>
      </div>

      {actionError ? (
        <div
          className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-red-200"
          role="alert"
        >
          {actionError}
        </div>
      ) : null}

      <details className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <summary className="cursor-pointer text-sm font-medium text-muted-foreground">
          Technical details
        </summary>
        <dl className="mt-3 grid gap-2 font-mono text-xs text-muted-foreground sm:grid-cols-2">
          <div>
            <dt>Analysis</dt>
            <dd className="text-foreground">{analysis.analysis_code}</dd>
          </div>
          <div>
            <dt>Video</dt>
            <dd className="text-foreground">
              {video?.asset_code ?? analysis.video_asset_code ?? "—"}
            </dd>
          </div>
          <div>
            <dt>Provider</dt>
            <dd className="text-foreground">
              {analysis.provider_label ?? analysis.provider_name}
              {analysis.is_simulated ? " · SIMULATED" : ""}
            </dd>
          </div>
          <div>
            <dt>Plan</dt>
            <dd className="text-foreground">{plan?.plan_code ?? "—"}</dd>
          </div>
          <div>
            <dt>Retrieval</dt>
            <dd className="text-foreground">
              {workflow?.retrieval_code ?? "—"}
            </dd>
          </div>
          <div>
            <dt>Review decision</dt>
            <dd className="text-foreground capitalize">
              {reviewDecision ?? "pending"}
            </dd>
          </div>
        </dl>
        {analysis.evidence.length > 3 ? (
          <div className="mt-4">
            <p className="text-xs font-medium text-muted-foreground uppercase">
              Full evidence ({analysis.evidence.length} items)
            </p>
            <ul className="mt-2 space-y-1 text-xs text-slate-300">
              {analysis.evidence.map((item) => (
                <li key={item.id}>
                  t={item.timestamp_seconds.toFixed(1)}s · {item.observation}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {audit.length > 0 ? (
          <div className="mt-4">
            <p className="text-xs font-medium text-muted-foreground uppercase">
              Audit timeline
            </p>
            <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
              {audit.slice(-12).map((event) => (
                <li key={event.id}>
                  {new Date(event.occurred_at).toLocaleString()} ·{" "}
                  {event.event_type} · {event.actor_name}
                  {event.simulation ? " · SIMULATED" : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <div className="mt-3">
          <Button
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() => void loadIncident()}
          >
            <RefreshCw data-icon="inline-start" />
            Retry load
          </Button>
        </div>
      </details>

      <SwitcherSection
        open={switcherOpen}
        onOpenChange={setSwitcherOpen}
        videos={videos}
        analyses={analyses}
        selectedVideoId={video?.asset_code ?? videoId}
        selectedAnalysisId={analysis.analysis_code}
        onSelectVideo={(assetCode) => {
          void navigateToContext({ video_id: assetCode });
        }}
        onSelectAnalysis={(assetCode, code) => {
          void navigateToContext({ video_id: assetCode, analysis_id: code });
        }}
      />

      <ConfirmationDialog
        open={approveOpen}
        onOpenChange={setApproveOpen}
        title="Approve selected actions?"
        description={`You are approving ${selectedActionIds.length} recommended action(s) for simulation only. No real notifications, medical dispatch, or tickets will be sent.`}
        confirmLabel="Confirm approval"
        onConfirm={() => void confirmApprove()}
      />
      <ConfirmationDialog
        open={executeOpen}
        onOpenChange={setExecuteOpen}
        title="Run simulated execution?"
        description="SafetyLens will create simulated supervisor alerts, medical-assistance requests, tickets, and evidence records. Emergency services will not be contacted."
        confirmLabel="Execute simulated actions"
        onConfirm={() => void confirmExecute()}
      />
    </div>
  );
}

interface SwitcherSectionProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  videos: ApiVideoAsset[];
  analyses: ApiIncidentAnalysis[];
  selectedVideoId: string | null;
  selectedAnalysisId: string | null;
  onSelectVideo: (assetCode: string) => void;
  onSelectAnalysis: (assetCode: string, analysisCode: string) => void;
}

function SwitcherSection({
  open,
  onOpenChange,
  videos,
  analyses,
  selectedVideoId,
  selectedAnalysisId,
  onSelectVideo,
  onSelectAnalysis,
}: SwitcherSectionProps) {
  return (
    <details
      className="rounded-xl border border-border bg-panel p-4 shadow-sm"
      open={open}
      onToggle={(event) =>
        onOpenChange((event.currentTarget as HTMLDetailsElement).open)
      }
    >
      <summary className="flex cursor-pointer items-center gap-2 text-sm font-medium text-muted-foreground">
        <ChevronRight className="size-4" />
        Switch incident (optional)
      </summary>
      <p className="mt-2 text-xs text-muted-foreground">
        Secondary navigation only — use notifications or Live Monitor for the
        primary workflow.
      </p>
      {videos.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">
          No ready videos available.
        </p>
      ) : (
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <label className="space-y-1 text-xs text-muted-foreground">
            Video asset
            <select
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
              value={selectedVideoId ?? ""}
              onChange={(event) => {
                if (event.target.value) onSelectVideo(event.target.value);
              }}
            >
              <option value="">Select a ready video…</option>
              {videos.map((item) => (
                <option key={item.id} value={item.asset_code}>
                  {item.asset_code} · {item.location}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1 text-xs text-muted-foreground">
            Completed analysis
            <select
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
              value={selectedAnalysisId ?? ""}
              onChange={(event) => {
                const code = event.target.value;
                if (code && selectedVideoId) {
                  onSelectAnalysis(selectedVideoId, code);
                }
              }}
              disabled={!selectedVideoId || analyses.length === 0}
            >
              {analyses.length === 0 ? (
                <option value="">No completed analyses</option>
              ) : (
                <>
                  <option value="">Select analysis…</option>
                  {analyses.map((item) => (
                    <option key={item.id} value={item.analysis_code}>
                      {item.analysis_code} · {item.incident_type}
                    </option>
                  ))}
                </>
              )}
            </select>
          </label>
        </div>
      )}
    </details>
  );
}
