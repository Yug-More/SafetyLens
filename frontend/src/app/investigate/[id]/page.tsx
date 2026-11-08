"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useCallback, useState } from "react";
import { platformRequest } from "@/lib/api/platform";
import { useApiResource } from "@/hooks/useApiResource";
import type { ApiIncidentAnalysis, ApiWorkflowStatus } from "@/lib/api/types";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
interface Investigation {
  incident: {
    id: string;
    incident_code: string;
    title: string;
    location: string;
    severity: string;
    status: string;
    detected_at: string;
  };
  analysis: ApiIncidentAnalysis | null;
  workflow: ApiWorkflowStatus | null;
  related: { id: string; title: string; status: string }[];
}
interface Operation {
  version: number;
  notes: string;
  assigned_user_id: string | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
}
const empty = () => null;
export default function InvestigationPage() {
  const { id } = useParams<{ id: string }>();
  const [notes, setNotes] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const loader = useCallback(
    async () => ({
      investigation: await platformRequest<Investigation>(
        `/api/investigations/${id}`,
      ),
      operation: await platformRequest<Operation>(
        `/api/incidents/${id}/operations`,
      ),
    }),
    [id],
  );
  const { data, error, isLoading, reload } = useApiResource({
    loader,
    fallback: empty,
    allowFallback: false,
  });
  async function save(resolve = false) {
    if (!data) return;
    try {
      await platformRequest(`/api/incidents/${id}/operations`, "PUT", {
        version: data.operation.version,
        notes: notes ?? data.operation.notes,
        assigned_user_id: data.operation.assigned_user_id,
        acknowledge: true,
        resolve,
      });
      setMessage("Saved.");
      setNotes(null);
      reload();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Save failed");
    }
  }
  if (isLoading) return <p role="status">Loading investigation…</p>;
  if (error || !data)
    return (
      <p role="alert">
        {error ?? "Incident unavailable"}
        <Button onClick={reload}>Retry</Button>
      </p>
    );
  const { incident, analysis, workflow, related } = data.investigation;
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title={incident.title}
        subtitle={`${incident.incident_code} · ${incident.location}`}
        actions={
          <span className="text-sm text-amber-300">
            {incident.severity} / {incident.status.replaceAll("_", " ")}
          </span>
        }
      />
      <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <section className="rounded-xl border border-border bg-panel p-6">
          <p className="text-xs uppercase tracking-wider text-muted-foreground">
            Evidence & interpretation
          </p>
          <h2 className="mt-3 text-lg font-semibold">
            {analysis?.summary ?? "Historical record: no linked analysis"}
          </h2>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            {analysis?.detailed_analysis ??
              "Open the historical demonstration for seeded example evidence. No live model result is implied."}
          </p>
          <p className="mt-4 text-xs text-muted-foreground">
            Provider: {analysis?.provider_name ?? "not recorded"} ·{" "}
            {analysis?.is_demo
              ? "DEMO / SCRIPTED"
              : "human verification required"}
          </p>
          {analysis?.limitations?.map((x, i) => (
            <p className="mt-2 text-xs text-amber-200" key={i}>
              {x}
            </p>
          ))}
          {workflow?.analysis_code && (
            <Link
              className="mt-6 inline-flex rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white"
              href={`/response?analysis_id=${encodeURIComponent(workflow.analysis_code)}&video_id=${encodeURIComponent(workflow.video_code ?? "")}`}
            >
              Open evidence, SOP citations & approval controls →
            </Link>
          )}
        </section>
        <section className="rounded-xl border border-border bg-panel p-6">
          <h2 className="font-semibold">Operator coordination</h2>
          <p className="mt-2 text-xs text-muted-foreground">
            Updates use version checks to prevent stale overwrites. Managers and
            administrators can save.
          </p>
          <label htmlFor="incident-notes" className="mt-5 block text-sm">
            Notes
          </label>
          <textarea
            id="incident-notes"
            className="mt-2 min-h-32 w-full rounded-lg border border-border bg-background p-3"
            maxLength={4000}
            value={notes ?? data.operation.notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <div className="mt-4 flex flex-wrap gap-2">
            <Button onClick={() => void save()}>Acknowledge & save</Button>
            <Button
              variant="outline"
              onClick={() => {
                if (
                  window.confirm(
                    "Mark this incident resolved? No physical action is performed.",
                  )
                )
                  void save(true);
              }}
            >
              Resolve
            </Button>
          </div>
          <p role="status" className="mt-3 text-sm">
            {message}
          </p>
        </section>
      </div>
      <section className="rounded-xl border border-border bg-panel p-6">
        <h2 className="font-semibold">Related camera incidents</h2>
        {related.length ? (
          related.map((x) => (
            <Link
              className="mt-3 block text-sm text-blue-400"
              key={x.id}
              href={`/investigate/${x.id}`}
            >
              {x.title} · {x.status}
            </Link>
          ))
        ) : (
          <p className="mt-3 text-sm text-muted-foreground">
            No other recorded incidents for this camera.
          </p>
        )}
      </section>
    </div>
  );
}
