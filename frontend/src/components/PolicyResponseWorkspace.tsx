"use client";

import { useCallback, useState } from "react";
import {
  BookOpenCheck,
  FileDown,
  FileWarning,
  Loader2,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog } from "@/components/ConfirmationDialog";
import { ConnectionBanner, PanelSkeleton } from "@/components/ConnectionBanner";
import { EmptyState } from "@/components/EmptyState";
import { SeverityBadge } from "@/components/SeverityBadge";
import { useApiResource } from "@/hooks/useApiResource";
import { ApiError } from "@/lib/api/client";
import {
  approveResponsePlan,
  executeResponsePlan,
  fetchIncidentAudit,
  fetchPlanExecutions,
  fetchResponsePlan,
  fetchVideoAnalyses,
  fetchVideos,
  generateIncidentReport,
  generateResponsePlan,
  getReportDownloadUrl,
  rejectResponsePlan,
  retryExecution,
  retrieveProceduresForAnalysis,
} from "@/lib/api";
import type {
  ApiActionExecution,
  ApiAuditEvent,
  ApiIncidentAnalysis,
  ApiIncidentReport,
  ApiProcedureRetrieval,
  ApiResponsePlan,
  ApiVideoAsset,
} from "@/lib/api/types";
import { getFallbackIncidentDetail } from "@/data/fallback";
import type { IncidentSeverity } from "@/types";

function formatIncidentType(value: string | null | undefined): string {
  if (!value) return "Unknown";
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

export function PolicyResponseWorkspace() {
  const [selectedAsset, setSelectedAsset] = useState("");
  const [analyses, setAnalyses] = useState<ApiIncidentAnalysis[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState("");
  const [retrieval, setRetrieval] = useState<ApiProcedureRetrieval | null>(null);
  const [plan, setPlan] = useState<ApiResponsePlan | null>(null);
  const [selectedActionIds, setSelectedActionIds] = useState<string[]>([]);
  const [approvalNotes, setApprovalNotes] = useState("");
  const [executions, setExecutions] = useState<ApiActionExecution[]>([]);
  const [audit, setAudit] = useState<ApiAuditEvent[]>([]);
  const [report, setReport] = useState<ApiIncidentReport | null>(null);
  const [activeCitation, setActiveCitation] = useState<string | null>(null);
  const [approveOpen, setApproveOpen] = useState(false);
  const [executeOpen, setExecuteOpen] = useState(false);
  const [loadingAnalyses, setLoadingAnalyses] = useState(false);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const videoLoader = useCallback(async () => {
    const response = await fetchVideos({ status: "ready", limit: 20 });
    return response.data;
  }, []);

  const {
    data: videos,
    error: videoError,
    source,
    isLoading: loadingVideos,
    reload: reloadVideos,
  } = useApiResource({
    loader: videoLoader,
    fallback: () => [] as ApiVideoAsset[],
    allowFallback: true,
  });

  const videoList = videos ?? [];

  const loadAnalysesForAsset = useCallback(async (assetCode: string) => {
    if (!assetCode) {
      setAnalyses([]);
      setSelectedAnalysis("");
      setRetrieval(null);
      setPlan(null);
      setExecutions([]);
      setReport(null);
      setAudit([]);
      return;
    }
    setLoadingAnalyses(true);
    setActionError(null);
    try {
      const response = await fetchVideoAnalyses(assetCode);
      const completed = response.data.filter((item) =>
        ["completed", "needs_review"].includes(item.status)
      );
      setAnalyses(completed);
      setSelectedAnalysis(completed[0]?.analysis_code ?? "");
      setRetrieval(null);
      setPlan(null);
      setExecutions([]);
      setReport(null);
      setAudit([]);
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Unable to load analyses."
      );
      setAnalyses([]);
      setSelectedAnalysis("");
    } finally {
      setLoadingAnalyses(false);
    }
  }, []);

  async function selectVideo(assetCode: string) {
    setSelectedAsset(assetCode);
    await loadAnalysesForAsset(assetCode);
  }

  const selectedVideo =
    videoList.find((item) => item.asset_code === selectedAsset) ?? null;
  const activeAnalysis =
    analyses.find((item) => item.analysis_code === selectedAnalysis) ?? null;
  const badgeSeverity = toBadgeSeverity(activeAnalysis?.severity);

  async function refreshAudit() {
    try {
      const response = await fetchIncidentAudit("INC-2026-0042");
      setAudit(response.data);
    } catch {
      // Audit may be empty before approval links the demo incident record.
    }
  }

  async function handleRetrieve() {
    if (!selectedAnalysis) return;
    setBusy(true);
    setActionError(null);
    setPlan(null);
    try {
      setRetrieval(await retrieveProceduresForAnalysis(selectedAnalysis));
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Retrieval failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handlePlan() {
    if (!selectedAnalysis) return;
    setBusy(true);
    setActionError(null);
    try {
      const result = await generateResponsePlan(selectedAnalysis, retrieval?.id);
      setPlan(result);
      setSelectedActionIds(result.actions.map((action) => action.id));
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Plan generation failed."
      );
    } finally {
      setBusy(false);
    }
  }

  async function confirmApprove() {
    if (!plan) return;
    setBusy(true);
    setActionError(null);
    try {
      await approveResponsePlan(plan.plan_code, {
        selectedActionIds,
        reviewerName: "demo-reviewer",
        notes: approvalNotes || undefined,
        incidentIdentifier: "INC-2026-0042",
        confirmed: true,
      });
      setPlan(await fetchResponsePlan(plan.plan_code));
      await refreshAudit();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Approval failed.");
    } finally {
      setBusy(false);
      setApproveOpen(false);
    }
  }

  async function handleReject() {
    if (!plan) return;
    setBusy(true);
    setActionError(null);
    try {
      await rejectResponsePlan(plan.plan_code, {
        reviewerName: "demo-reviewer",
        reason: approvalNotes || "Rejected in demo review",
      });
      setPlan(await fetchResponsePlan(plan.plan_code));
      await refreshAudit();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Rejection failed.");
    } finally {
      setBusy(false);
    }
  }

  async function confirmExecute() {
    if (!plan) return;
    setBusy(true);
    setActionError(null);
    try {
      const result = await executeResponsePlan(plan.plan_code);
      setExecutions(result.executions);
      setPlan(await fetchResponsePlan(plan.plan_code));
      await refreshAudit();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Execution failed.");
    } finally {
      setBusy(false);
      setExecuteOpen(false);
    }
  }

  async function handleRetry(executionCode: string) {
    setBusy(true);
    setActionError(null);
    try {
      await retryExecution(executionCode);
      if (plan) {
        const response = await fetchPlanExecutions(plan.plan_code);
        setExecutions(response.data);
        setPlan(await fetchResponsePlan(plan.plan_code));
      }
      await refreshAudit();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Retry failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleReport() {
    if (!plan) return;
    setBusy(true);
    setActionError(null);
    try {
      const result = await generateIncidentReport(
        "INC-2026-0042",
        plan.plan_code,
        true
      );
      setReport(result);
      await refreshAudit();
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Report generation failed."
      );
    } finally {
      setBusy(false);
    }
  }

  const canApprove =
    plan?.status === "completed" &&
    (plan.approval_status === "pending" || !plan.approval_status) &&
    (plan.execution_status === "none" || !plan.execution_status);

  const canExecute =
    plan?.approval_status === "approved" ||
    plan?.approval_status === "partially_approved";

  if (loadingVideos) {
    return <PanelSkeleton className="min-h-96" />;
  }

  if (source === "fallback") {
    const offline = getFallbackIncidentDetail();
    return (
      <div className="space-y-4">
        <ConnectionBanner
          mode="fallback"
          message={videoError}
          onRetry={reloadVideos}
        />
        <div className="rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
          Offline Demo Data — seeded INC-2026-0042 is shown because the API is
          unavailable. Uploaded-video analysis summaries are not mixed into this
          view.
        </div>
        <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
          <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Offline demo incident
          </p>
          <h2 className="mt-1 text-xl font-semibold text-foreground">
            {offline.incident.title}
          </h2>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            {offline.incident.id}
          </p>
          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">Location</dt>
              <dd className="font-medium text-foreground">
                {offline.incident.location}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Camera</dt>
              <dd className="font-medium text-foreground">
                {offline.incident.cameraName}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Confidence</dt>
              <dd className="font-medium text-foreground">
                {offline.incident.confidence}%
              </dd>
            </div>
          </dl>
        </article>
      </div>
    );
  }

  if (source === "error") {
    return (
      <div className="space-y-4">
        <ConnectionBanner mode="error" message={videoError} onRetry={reloadVideos} />
        <EmptyState
          title="Response Center unavailable"
          description="Connect to the SafetyLens API to load uploaded videos and analyses."
          actionLabel="Retry"
          onAction={reloadVideos}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="space-y-4 rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Select analysis for response
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Summary, evidence, and procedures below come from the selected
              uploaded video analysis — not from seeded dashboard incidents.
            </p>
          </div>
          <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-100">
            SIMULATED execution
          </span>
        </div>

        {videoList.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Upload and analyze a video on Live Monitor first.
          </p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1 text-xs text-muted-foreground">
              Video asset
              <select
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                value={selectedAsset}
                onChange={(event) => {
                  void selectVideo(event.target.value);
                }}
              >
                <option value="">Select a ready video…</option>
                {videoList.map((video) => (
                  <option key={video.id} value={video.asset_code}>
                    {video.asset_code} · {video.location}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Completed analysis
              <select
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                value={selectedAnalysis}
                onChange={(event) => {
                  setSelectedAnalysis(event.target.value);
                  setRetrieval(null);
                  setPlan(null);
                  setExecutions([]);
                  setReport(null);
                  setAudit([]);
                }}
                disabled={loadingAnalyses || !selectedAsset || analyses.length === 0}
              >
                {analyses.length === 0 ? (
                  <option value="">
                    {loadingAnalyses
                      ? "Loading analyses…"
                      : selectedAsset
                        ? "No completed analyses for this video"
                        : "Select a video first"}
                  </option>
                ) : (
                  analyses.map((analysis) => (
                    <option key={analysis.id} value={analysis.analysis_code}>
                      {analysis.analysis_code} · {analysis.incident_type}
                    </option>
                  ))
                )}
              </select>
            </label>
          </div>
        )}
      </section>

      {activeAnalysis && selectedVideo ? (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
          <section className="space-y-4">
            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    Selected analysis summary
                  </p>
                  <h2 className="mt-1 text-xl font-semibold capitalize text-foreground">
                    {formatIncidentType(activeAnalysis.incident_type)}
                  </h2>
                  <p className="mt-1 font-mono text-xs text-muted-foreground">
                    {activeAnalysis.analysis_code} · {selectedVideo.asset_code}
                  </p>
                </div>
                {badgeSeverity ? <SeverityBadge severity={badgeSeverity} /> : null}
              </div>
              <dl className="grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-muted-foreground">Location</dt>
                  <dd className="font-medium text-foreground">
                    {selectedVideo.location}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Camera</dt>
                  <dd className="font-medium text-foreground">
                    {selectedVideo.camera_name ?? selectedVideo.camera_id ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Severity</dt>
                  <dd className="font-medium capitalize text-foreground">
                    {activeAnalysis.severity ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Confidence</dt>
                  <dd className="font-medium text-foreground">
                    {confidencePercent(activeAnalysis.confidence)}
                  </dd>
                </div>
              </dl>
              {activeAnalysis.summary ? (
                <p className="mt-4 text-sm text-slate-200">{activeAnalysis.summary}</p>
              ) : null}
              {activeAnalysis.provider_label ? (
                <p className="mt-2 text-xs text-muted-foreground">
                  {activeAnalysis.provider_label}
                  {activeAnalysis.is_simulated ? " · SIMULATED" : ""}
                </p>
              ) : null}
            </article>

            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <FileWarning className="size-4 text-warning" aria-hidden="true" />
                <h2 className="text-base font-semibold text-foreground">
                  Evidence from selected analysis
                </h2>
              </div>
              <ul className="space-y-2 text-sm leading-relaxed text-slate-200">
                {activeAnalysis.evidence.map((item) => (
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
                {activeAnalysis.evidence.length === 0 ? (
                  <li className="text-muted-foreground">
                    No evidence items recorded for this analysis.
                  </li>
                ) : null}
              </ul>
            </article>
          </section>

          <section className="space-y-4">
            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <ShieldAlert className="size-4 text-emerald-300" aria-hidden="true" />
                <h2 className="text-base font-semibold text-foreground">
                  Retrieved procedure
                </h2>
              </div>
              {!retrieval ? (
                <div className="rounded-lg border border-dashed border-border bg-secondary/20 px-4 py-6 text-center">
                  <p className="text-sm font-medium text-foreground">
                    No procedure retrieved yet
                  </p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Click{" "}
                    <span className="font-medium text-foreground">
                      Retrieve procedure
                    </span>{" "}
                    to load the SOP and verified citations for this analysis.
                  </p>
                </div>
              ) : (
                <div className="space-y-3 text-sm">
                  <p className="text-xs text-muted-foreground">
                    {retrieval.retrieval_code} · {retrieval.method} ·{" "}
                    {retrieval.status}
                  </p>
                  {retrieval.matches.length === 0 ? (
                    <p className="text-amber-100">
                      Retrieval completed with insufficient policy matches.
                    </p>
                  ) : (
                    retrieval.matches.map((match) => (
                      <div
                        key={`${match.chunk_id}-${match.rank}`}
                        className="rounded-lg border border-border/60 bg-secondary/25 px-3 py-2.5"
                      >
                        <p className="font-medium text-foreground">
                          #{match.rank} {match.procedure_code}
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
                    ))
                  )}
                </div>
              )}
            </article>
          </section>
        </div>
      ) : !selectedAsset ? (
        <EmptyState
          title="Select a video and analysis"
          description="Choose a ready uploaded video above. The incident summary and evidence will come only from that analysis."
        />
      ) : loadingAnalyses ? (
        <p className="text-sm text-muted-foreground">Loading analyses…</p>
      ) : analyses.length === 0 ? (
        <EmptyState
          title="No completed analyses"
          description="Analyze this video on Live Monitor first, then return here to retrieve procedures."
        />
      ) : null}

      <section className="space-y-4 rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            disabled={!selectedAnalysis || busy}
            onClick={() => void handleRetrieve()}
          >
            {busy ? (
              <Loader2 className="size-4 animate-spin" data-icon="inline-start" />
            ) : (
              <BookOpenCheck data-icon="inline-start" />
            )}
            Retrieve procedure
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={!selectedAnalysis || busy}
            onClick={() => void handlePlan()}
          >
            <Sparkles data-icon="inline-start" />
            Generate response plan
          </Button>
        </div>

        {actionError ? (
          <div
            className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-red-200"
            role="alert"
          >
            {actionError}
          </div>
        ) : null}

        {plan ? (
          <div className="space-y-4 rounded-lg border border-border bg-background/40 p-3">
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="rounded-md border border-border px-2 py-1">
                {plan.plan_code}
              </span>
              <span className="rounded-md border border-border px-2 py-1 capitalize">
                approval: {(plan.approval_status ?? "pending").replaceAll("_", " ")}
              </span>
              <span className="rounded-md border border-border px-2 py-1 capitalize">
                execution: {(plan.execution_status ?? "none").replaceAll("_", " ")}
              </span>
              <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-amber-100">
                Recommended ≠ executed
              </span>
            </div>
            <p className="text-sm text-muted-foreground">{plan.summary}</p>

            {plan.status === "completed" ? (
              <>
                <label className="block space-y-1 text-xs text-muted-foreground">
                  Approval notes
                  <textarea
                    className="min-h-16 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                    value={approvalNotes}
                    onChange={(event) => setApprovalNotes(event.target.value)}
                    disabled={!canApprove}
                  />
                </label>
                <ul className="space-y-2">
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
                              {action.responsible_role} · {action.priority} ·{" "}
                              {action.selection_status === "approved"
                                ? "Approved"
                                : action.selection_status === "rejected"
                                  ? "Rejected"
                                  : action.selection_status === "unselected"
                                    ? "Unselected"
                                    : canApprove
                                      ? "Awaiting approval"
                                      : "Recommended"}
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
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    disabled={
                      !canApprove || busy || selectedActionIds.length === 0
                    }
                    onClick={() => setApproveOpen(true)}
                  >
                    Approve Actions
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canApprove || busy}
                    onClick={() => void handleReject()}
                  >
                    Reject Plan
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={!canExecute || busy}
                    onClick={() => setExecuteOpen(true)}
                  >
                    Run simulated execution
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={!canExecute || busy}
                    onClick={() => void handleReport()}
                  >
                    <FileDown data-icon="inline-start" />
                    Generate report
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-sm text-amber-100">
                This plan cannot be approved or executed (
                {plan.status.replaceAll("_", " ")}).
              </p>
            )}
          </div>
        ) : null}

        {executions.length > 0 ? (
          <div className="space-y-2 rounded-lg border border-border p-3">
            <h3 className="text-sm font-semibold text-foreground">
              Simulated execution status
            </h3>
            <ul className="space-y-2 text-sm">
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
                      <span className="text-[11px] text-amber-100">SIMULATED</span>
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
          </div>
        ) : null}

        {audit.length > 0 ? (
          <div className="space-y-2 rounded-lg border border-border p-3">
            <h3 className="text-sm font-semibold text-foreground">Audit timeline</h3>
            <ul className="space-y-1 text-xs text-muted-foreground">
              {audit.slice(-12).map((event) => (
                <li key={event.id}>
                  {new Date(event.occurred_at).toLocaleString()} · {event.event_type}{" "}
                  · {event.actor_name}
                  {event.simulation ? " · SIMULATED" : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {report ? (
          <div className="rounded-lg border border-border p-3 text-sm">
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
          </div>
        ) : null}
      </section>

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
