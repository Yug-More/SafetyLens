"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import {
  CheckCircle2,
  ClipboardList,
  FileWarning,
  ShieldAlert,
} from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { ConfirmationDialog } from "@/components/ConfirmationDialog";
import { Button } from "@/components/ui/button";
import {
  ConnectionBanner,
  PanelSkeleton,
} from "@/components/ConnectionBanner";
import { EmptyState } from "@/components/EmptyState";
import { useApiResource } from "@/hooks/useApiResource";
import { fetchIncidentDetail } from "@/lib/api";
import { mapIncidentDetail } from "@/lib/api/mappers";
import { getFallbackIncidentDetail } from "@/data/fallback";

export default function ResponsePage() {
  const loader = useCallback(async () => {
    const detail = await fetchIncidentDetail("INC-2026-0042");
    return mapIncidentDetail(detail);
  }, []);

  const fallback = useCallback(() => getFallbackIncidentDetail(), []);

  const { data, error, source, isLoading, reload } = useApiResource({
    loader,
    fallback,
  });

  const [approveOpen, setApproveOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader title="Response Center" subtitle="Loading incident review…" />
        <PanelSkeleton className="min-h-96" />
      </div>
    );
  }

  if (source === "error" || !data) {
    return (
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader
          title="Response Center"
          subtitle="Review evidence, procedure guidance, and recommended actions"
        />
        <ConnectionBanner mode="error" message={error} onRetry={reload} />
        <EmptyState
          title="Incident details unavailable"
          description="Connect to the API to load INC-2026-0042."
          actionLabel="Retry"
          onAction={reload}
        />
      </div>
    );
  }

  const { incident, procedure, actions, evidenceDescriptions } = data;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <ConnectionBanner
        mode={source === "fallback" ? "fallback" : "api"}
        message={error}
        onRetry={reload}
      />

      <PageHeader
        title="Response Center"
        subtitle="Review evidence, procedure guidance, and recommended actions before approval"
        status={<StatusBadge status={incident.status} />}
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <section className="space-y-4">
          <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Incident Summary
                </p>
                <h2 className="mt-1 text-xl font-semibold text-foreground">
                  {incident.title}
                </h2>
                <p className="mt-1 font-mono text-xs text-muted-foreground">
                  {incident.id}
                </p>
              </div>
              <SeverityBadge severity={incident.severity} />
            </div>

            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Location</dt>
                <dd className="font-medium text-foreground">{incident.location}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Camera</dt>
                <dd className="font-medium text-foreground">{incident.cameraName}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Detected</dt>
                <dd className="font-medium text-foreground">{incident.relativeTime}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Confidence</dt>
                <dd className="font-medium text-foreground">{incident.confidence}%</dd>
              </div>
            </dl>

            <div className="mt-4">
              <div
                className="h-2 overflow-hidden rounded-full bg-muted"
                role="progressbar"
                aria-valuenow={incident.confidence}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Confidence ${incident.confidence}%`}
              >
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${incident.confidence}%` }}
                />
              </div>
            </div>
          </article>

          <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <FileWarning className="size-4 text-warning" aria-hidden="true" />
              <h2 className="text-base font-semibold text-foreground">Evidence Panel</h2>
            </div>
            <div className="relative mb-4 aspect-video overflow-hidden rounded-lg border border-border bg-[#070d18]">
              <div className="camera-grid absolute inset-0 opacity-60" />
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-center">
                <p className="text-sm font-medium text-slate-200">
                  Preserved evidence clip
                </p>
                <p className="text-xs text-slate-400">
                  Camera 04 · Loading Zone B · Stage 2 record
                </p>
              </div>
              <span className="absolute top-3 left-3 rounded bg-black/50 px-2 py-1 text-[11px] text-red-300">
                EVIDENCE
              </span>
            </div>
            <ul className="space-y-2 text-sm leading-relaxed text-slate-200">
              {evidenceDescriptions.map((item) => (
                <li key={item} className="rounded-lg border border-border/60 bg-secondary/25 px-3 py-2">
                  {item}
                </li>
              ))}
              {evidenceDescriptions.length === 0 ? (
                <li>{incident.evidence}</li>
              ) : null}
            </ul>
          </article>

          <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <ClipboardList className="size-4 text-primary" aria-hidden="true" />
              <h2 className="text-base font-semibold text-foreground">Audit Preview</h2>
            </div>
            <ul className="space-y-2 text-sm">
              {[
                "Incident detected by edge monitoring",
                "Evidence clip preserved for review",
                "Procedure matched: Worker Fall Response",
                "Awaiting human approval before action execution",
              ].map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-2 rounded-lg border border-border/70 bg-secondary/30 px-3 py-2"
                >
                  <CheckCircle2
                    className="mt-0.5 size-3.5 shrink-0 text-emerald-300"
                    aria-hidden="true"
                  />
                  <span className="text-slate-200">{item}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-muted-foreground">
              Demo Environment · No real notifications or emergency actions are sent.
            </p>
          </article>
        </section>

        <section className="space-y-4">
          <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <ShieldAlert className="size-4 text-emerald-300" aria-hidden="true" />
              <h2 className="text-base font-semibold text-foreground">
                Relevant Procedure
              </h2>
            </div>
            {procedure ? (
              <>
                <h3 className="text-lg font-medium text-foreground">
                  {procedure.title} — {procedure.section}
                </h3>
                <ol className="mt-4 space-y-2.5 text-sm text-slate-200">
                  {procedure.steps.map((step, index) => (
                    <li
                      key={step}
                      className="flex gap-3 rounded-lg border border-border/60 bg-secondary/25 px-3 py-2.5"
                    >
                      <span className="font-mono text-xs text-muted-foreground">
                        {index + 1}.
                      </span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No matched procedure.</p>
            )}
          </article>

          <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
            <h2 className="mb-3 text-base font-semibold text-foreground">
              Recommended Actions
            </h2>
            <ul className="space-y-2">
              {actions.map((action) => (
                <li
                  key={action.id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-secondary/30 px-3 py-2.5 text-sm"
                >
                  <span className="text-foreground">{action.label}</span>
                  <span className="rounded-md border border-border px-2 py-0.5 text-[11px] capitalize text-muted-foreground">
                    {action.priority}
                  </span>
                </li>
              ))}
            </ul>

            <div className="mt-4 flex flex-wrap gap-2">
              <Button onClick={() => setApproveOpen(true)}>Approve Actions</Button>
              <Button variant="outline" onClick={() => setRejectOpen(true)}>
                Reject Recommendation
              </Button>
            </div>
          </article>
        </section>
      </div>

      <ConfirmationDialog
        open={approveOpen}
        onOpenChange={setApproveOpen}
        title="Approve recommended actions?"
        description="In Stage 2 this is a mock approval. No alerts, tickets, or emergency actions will be executed."
        confirmLabel="Approve for Demo"
        onConfirm={() =>
          toast.success("Actions approved in demo mode. Execution arrives in a later stage.")
        }
      />

      <ConfirmationDialog
        open={rejectOpen}
        onOpenChange={setRejectOpen}
        title="Reject recommendation?"
        description="This mock rejection will not change the demo dataset permanently."
        confirmLabel="Reject for Demo"
        tone="destructive"
        onConfirm={() =>
          toast.message("Recommendation rejected in this demo session.")
        }
      />
    </div>
  );
}
