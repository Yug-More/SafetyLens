"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BookOpenCheck,
  FileDown,
  Loader2,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog } from "@/components/ConfirmationDialog";
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

export function PolicyResponseWorkspace() {
  const [videos, setVideos] = useState<ApiVideoAsset[]>([]);
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
  const [loadingVideos, setLoadingVideos] = useState(true);
  const [loadingAnalyses, setLoadingAnalyses] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnalysesForAsset = useCallback(async (assetCode: string) => {
    if (!assetCode) {
      setAnalyses([]);
      setSelectedAnalysis("");
      return;
    }
    setLoadingAnalyses(true);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load analyses.");
    } finally {
      setLoadingAnalyses(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const response = await fetchVideos({ status: "ready", limit: 20 });
        if (cancelled) return;
        setVideos(response.data);
        const first = response.data[0]?.asset_code ?? "";
        setSelectedAsset(first);
        if (first) await loadAnalysesForAsset(first);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unable to load videos.");
        }
      } finally {
        if (!cancelled) setLoadingVideos(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadAnalysesForAsset]);

  async function refreshAudit() {
    try {
      const response = await fetchIncidentAudit("INC-2026-0042");
      setAudit(response.data);
    } catch {
      // Audit may be empty before approval links the incident.
    }
  }

  async function handleRetrieve() {
    if (!selectedAnalysis) return;
    setBusy(true);
    setError(null);
    setPlan(null);
    try {
      setRetrieval(await retrieveProceduresForAnalysis(selectedAnalysis));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Retrieval failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handlePlan() {
    if (!selectedAnalysis) return;
    setBusy(true);
    setError(null);
    try {
      const result = await generateResponsePlan(selectedAnalysis, retrieval?.id);
      setPlan(result);
      setSelectedActionIds(result.actions.map((action) => action.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Plan generation failed.");
    } finally {
      setBusy(false);
    }
  }

  async function confirmApprove() {
    if (!plan) return;
    setBusy(true);
    setError(null);
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
      setError(err instanceof ApiError ? err.message : "Approval failed.");
    } finally {
      setBusy(false);
      setApproveOpen(false);
    }
  }

  async function handleReject() {
    if (!plan) return;
    setBusy(true);
    setError(null);
    try {
      await rejectResponsePlan(plan.plan_code, {
        reviewerName: "demo-reviewer",
        reason: approvalNotes || "Rejected in demo review",
      });
      setPlan(await fetchResponsePlan(plan.plan_code));
      await refreshAudit();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Rejection failed.");
    } finally {
      setBusy(false);
    }
  }

  async function confirmExecute() {
    if (!plan) return;
    setBusy(true);
    setError(null);
    try {
      const result = await executeResponsePlan(plan.plan_code);
      setExecutions(result.executions);
      setPlan(await fetchResponsePlan(plan.plan_code));
      await refreshAudit();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Execution failed.");
    } finally {
      setBusy(false);
      setExecuteOpen(false);
    }
  }

  async function handleRetry(executionCode: string) {
    setBusy(true);
    setError(null);
    try {
      await retryExecution(executionCode);
      if (plan) {
        const response = await fetchPlanExecutions(plan.plan_code);
        setExecutions(response.data);
        setPlan(await fetchResponsePlan(plan.plan_code));
      }
      await refreshAudit();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Retry failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleReport() {
    if (!plan) return;
    setBusy(true);
    setError(null);
    try {
      const result = await generateIncidentReport(
        "INC-2026-0042",
        plan.plan_code,
        true
      );
      setReport(result);
      await refreshAudit();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Report generation failed.");
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

  return (
    <section className="space-y-4 rounded-xl border border-border bg-panel p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Policy retrieval, approval & simulated execution
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Stage 6 requires explicit human approval. Executed outcomes are
            simulated only.
          </p>
        </div>
        <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-100">
          SIMULATED execution
        </span>
      </div>

      {loadingVideos ? (
        <p className="text-sm text-muted-foreground">Loading ready videos…</p>
      ) : videos.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Upload and analyze a video on Monitor first.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="space-y-1 text-xs text-muted-foreground">
            Video asset
            <select
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
              value={selectedAsset}
              onChange={(event) => {
                setSelectedAsset(event.target.value);
                void loadAnalysesForAsset(event.target.value);
              }}
            >
              {videos.map((video) => (
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
              onChange={(event) => setSelectedAnalysis(event.target.value)}
              disabled={loadingAnalyses || analyses.length === 0}
            >
              {analyses.length === 0 ? (
                <option value="">No completed analyses</option>
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

      <div className="flex flex-wrap gap-2">
        <Button size="sm" disabled={!selectedAnalysis || busy} onClick={() => void handleRetrieve()}>
          {busy ? <Loader2 className="size-4 animate-spin" data-icon="inline-start" /> : <BookOpenCheck data-icon="inline-start" />}
          Retrieve procedure
        </Button>
        <Button size="sm" variant="outline" disabled={!selectedAnalysis || busy} onClick={() => void handlePlan()}>
          <Sparkles data-icon="inline-start" />
          Generate response plan
        </Button>
      </div>

      {error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-red-200" role="alert">
          {error}
        </div>
      ) : null}

      {retrieval ? (
        <div className="space-y-2 rounded-lg border border-border bg-background/40 p-3 text-sm">
          <p className="text-xs text-muted-foreground">
            {retrieval.retrieval_code} · method {retrieval.method} · {retrieval.status}
          </p>
          {retrieval.matches.slice(0, 3).map((match) => (
            <p key={`${match.chunk_id}-${match.rank}`} className="text-slate-200">
              #{match.rank} {match.procedure_code}: {match.excerpt.slice(0, 160)}…
            </p>
          ))}
        </div>
      ) : null}

      {plan ? (
        <div className="space-y-4 rounded-lg border border-border bg-background/40 p-3">
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-md border border-border px-2 py-1">{plan.plan_code}</span>
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
                    <li key={action.id} className="rounded-lg border border-border p-3 text-sm">
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
                          <span className="mt-1 block text-slate-200">{action.description}</span>
                          {action.citations.map((cite) => (
                            <button
                              key={cite.id}
                              type="button"
                              className="mt-2 block text-left text-xs text-primary"
                              onClick={() =>
                                setActiveCitation(activeCitation === cite.id ? null : cite.id)
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
                <Button size="sm" disabled={!canApprove || busy || selectedActionIds.length === 0} onClick={() => setApproveOpen(true)}>
                  Approve Actions
                </Button>
                <Button size="sm" variant="outline" disabled={!canApprove || busy} onClick={() => void handleReject()}>
                  Reject Plan
                </Button>
                <Button size="sm" variant="secondary" disabled={!canExecute || busy} onClick={() => setExecuteOpen(true)}>
                  Run simulated execution
                </Button>
                <Button size="sm" variant="ghost" disabled={!canExecute || busy} onClick={() => void handleReport()}>
                  <FileDown data-icon="inline-start" />
                  Generate report
                </Button>
              </div>
            </>
          ) : (
            <p className="text-sm text-amber-100">
              This plan cannot be approved or executed ({plan.status.replaceAll("_", " ")}).
            </p>
          )}
        </div>
      ) : null}

      {executions.length > 0 ? (
        <div className="space-y-2 rounded-lg border border-border p-3">
          <h3 className="text-sm font-semibold text-foreground">Simulated execution status</h3>
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
              <li key={item.id} className="rounded-md border border-border/70 p-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span>
                    {item.action_title} · {statusLabel}
                  </span>
                  <span className="text-[11px] text-amber-100">SIMULATED</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{item.message}</p>
                {item.status === "failed" ? (
                  <Button className="mt-2" size="sm" variant="outline" disabled={busy} onClick={() => void handleRetry(item.execution_code)}>
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
                {new Date(event.occurred_at).toLocaleString()} · {event.event_type} ·{" "}
                {event.actor_name}
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
    </section>
  );
}
