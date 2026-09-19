"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Download, Eye, FileBarChart, Loader2, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { ConnectionBanner, PanelSkeleton } from "@/components/ConnectionBanner";
import { EmptyState } from "@/components/EmptyState";
import { useApiResource } from "@/hooks/useApiResource";
import { ApiError } from "@/lib/api/client";
import {
  fetchIncidentReports,
  fetchIncidents,
  generateIncidentReport,
  getReportDownloadUrl,
} from "@/lib/api";
import type { ApiIncident, ApiIncidentReport } from "@/lib/api/types";

const emptyReports = () => [] as ApiIncidentReport[];

function ReportsPageContent() {
  const searchParams = useSearchParams();
  const incidentFromUrl = useMemo(
    () =>
      searchParams.get("incident_id") ??
      searchParams.get("incident") ??
      null,
    [searchParams]
  );

  const [manualIncidentCode, setManualIncidentCode] = useState<string | null>(
    null
  );
  const selectedIncidentCode = manualIncidentCode ?? incidentFromUrl;
  const [incidents, setIncidents] = useState<ApiIncident[]>([]);
  const [selected, setSelected] = useState<ApiIncidentReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          const response = await fetchIncidents({ limit: 50 });
          setIncidents(response.data);
        } catch {
          // Incident list is optional for manual selection.
        }
      })();
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const loader = useCallback(async () => {
    if (!selectedIncidentCode) return [];
    const response = await fetchIncidentReports(selectedIncidentCode);
    return response.data;
  }, [selectedIncidentCode]);

  const { data, error, source, isLoading, reload } = useApiResource({
    loader,
    fallback: emptyReports,
    allowFallback: false,
  });

  const reports = data ?? [];

  async function handleGenerate() {
    if (!selectedIncidentCode) return;
    setBusy(true);
    setActionError(null);
    try {
      const report = await generateIncidentReport(
        selectedIncidentCode,
        undefined,
        true
      );
      setSelected(report);
      reload();
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Report generation failed."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <PageHeader
        title="Reports"
        subtitle="Persisted incident reports with simulated execution disclosure and PDF download"
      />

      <ConnectionBanner
        mode={
          source === "fallback"
            ? "fallback"
            : source === "error"
              ? "error"
              : "api"
        }
        message={
          error
            ? `${error} Reports require the live API — offline PDF generation is never faked.`
            : null
        }
        onRetry={reload}
      />

      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <label className="block space-y-1 text-xs text-muted-foreground">
          Incident
          <select
            className="w-full max-w-md rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
            value={selectedIncidentCode ?? ""}
            onChange={(event) => {
              setManualIncidentCode(event.target.value || null);
              setSelected(null);
            }}
          >
            <option value="">Select an incident…</option>
            {incidents.map((incident) => (
              <option key={incident.id} value={incident.incident_code}>
                {incident.incident_code} · {incident.title}
              </option>
            ))}
          </select>
        </label>
        <p className="mt-2 text-xs text-muted-foreground">
          Choose an incident explicitly, or open Reports with an{" "}
          <span className="font-mono">incident_id</span> URL parameter after
          completing response workflow.
        </p>
      </section>

      {!selectedIncidentCode ? (
        <EmptyState
          title="No incident selected"
          description="Select an incident above or add ?incident_id=INC-YYYY-NNNN to the URL after approving and executing a response."
        />
      ) : (
        <>
          <section className="flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={isLoading || busy}
              onClick={reload}
            >
              {isLoading ? (
                <Loader2 className="size-4 animate-spin" data-icon="inline-start" />
              ) : (
                <RefreshCw data-icon="inline-start" />
              )}
              Refresh
            </Button>
            <Button size="sm" disabled={busy} onClick={() => void handleGenerate()}>
              {busy ? (
                <Loader2 className="size-4 animate-spin" data-icon="inline-start" />
              ) : (
                <FileBarChart data-icon="inline-start" />
              )}
              Generate report for {selectedIncidentCode}
            </Button>
            <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-100">
              SIMULATED actions only
            </span>
          </section>

          {actionError ? (
            <div
              className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-red-200"
              role="alert"
            >
              {actionError}
            </div>
          ) : null}

          <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <h2 className="text-base font-semibold text-foreground">
                Incident reports
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Reports for {selectedIncidentCode}. Incomplete reports are labeled
                explicitly.
              </p>

              {isLoading ? (
                <div className="mt-4">
                  <PanelSkeleton />
                </div>
              ) : reports.length === 0 ? (
                <p className="mt-4 text-sm text-muted-foreground">
                  No reports yet. Complete approval and simulated execution in
                  Response, then generate a report.
                </p>
              ) : (
                <ul className="mt-4 space-y-2">
                  {reports.map((report) => (
                    <li
                      key={report.id}
                      className={`flex flex-col gap-3 rounded-lg border px-4 py-3 sm:flex-row sm:items-center sm:justify-between ${
                        selected?.id === report.id
                          ? "border-primary/50 bg-primary/5"
                          : "border-border bg-secondary/30"
                      }`}
                    >
                      <div>
                        <p className="font-medium text-foreground">{report.title}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {report.report_code} ·{" "}
                          {report.incident_code ?? selectedIncidentCode} ·{" "}
                          {new Date(report.generated_at).toLocaleString()} ·{" "}
                          <span className="capitalize">{report.status}</span>
                          {report.simulation ? " · SIMULATED" : ""}
                        </p>
                        {report.incomplete_reason ? (
                          <p className="mt-1 text-xs text-amber-100">
                            {report.incomplete_reason}
                          </p>
                        ) : null}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setSelected(report)}
                        >
                          <Eye data-icon="inline-start" />
                          View
                        </Button>
                        <a
                          className="inline-flex h-7 items-center gap-1 rounded-lg border border-transparent bg-secondary px-2.5 text-[0.8rem] font-medium text-secondary-foreground hover:bg-[color-mix(in_oklch,var(--secondary),var(--foreground)_5%)]"
                          href={getReportDownloadUrl(report.report_code)}
                          download
                        >
                          <Download className="size-3.5" />
                          Download PDF
                        </a>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </article>

            <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <h2 className="text-base font-semibold text-foreground">
                Report detail
              </h2>
              {!selected ? (
                <p className="mt-3 text-sm text-muted-foreground">
                  Select a report to inspect metadata.
                </p>
              ) : (
                <div className="mt-3 space-y-3 text-sm">
                  <p>
                    <span className="text-muted-foreground">Title:</span>{" "}
                    {selected.title}
                  </p>
                  <p>
                    <span className="text-muted-foreground">Identifiers:</span>{" "}
                    {selected.report_code} /{" "}
                    {selected.incident_code ?? selected.incident_id}
                  </p>
                  <p>
                    <span className="text-muted-foreground">Plan:</span>{" "}
                    {selected.plan_code ?? "Not linked"}
                  </p>
                  <p>
                    <span className="text-muted-foreground">Status:</span>{" "}
                    <span className="capitalize">{selected.status}</span>
                  </p>
                  <p>
                    <span className="text-muted-foreground">Simulation:</span>{" "}
                    {selected.simulation
                      ? "Yes — no real workplace systems contacted"
                      : "No"}
                  </p>
                  <p>
                    <span className="text-muted-foreground">Generated:</span>{" "}
                    {new Date(selected.generated_at).toLocaleString()}
                  </p>
                  {selected.incomplete_reason ? (
                    <p className="rounded-md border border-amber-500/40 bg-amber-500/10 p-2 text-xs text-amber-100">
                      Incomplete: {selected.incomplete_reason}
                    </p>
                  ) : null}
                  <a
                    className="inline-flex h-7 items-center gap-1 rounded-lg border border-transparent bg-primary px-2.5 text-[0.8rem] font-medium text-primary-foreground hover:bg-primary/80"
                    href={getReportDownloadUrl(selected.report_code)}
                    download
                  >
                    <Download className="size-3.5" />
                    Download PDF
                  </a>
                </div>
              )}
            </article>
          </section>
        </>
      )}
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense fallback={<PanelSkeleton className="min-h-96" />}>
      <ReportsPageContent />
    </Suspense>
  );
}
