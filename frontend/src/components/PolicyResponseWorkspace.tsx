"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BookOpenCheck,
  ClipboardList,
  Loader2,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import {
  fetchVideoAnalyses,
  fetchVideos,
  generateResponsePlan,
  retrieveProceduresForAnalysis,
} from "@/lib/api";
import type {
  ApiIncidentAnalysis,
  ApiProcedureRetrieval,
  ApiResponsePlan,
  ApiVideoAsset,
} from "@/lib/api/types";

export function PolicyResponseWorkspace() {
  const [videos, setVideos] = useState<ApiVideoAsset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<string>("");
  const [analyses, setAnalyses] = useState<ApiIncidentAnalysis[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<string>("");
  const [retrieval, setRetrieval] = useState<ApiProcedureRetrieval | null>(null);
  const [plan, setPlan] = useState<ApiResponsePlan | null>(null);
  const [activeCitation, setActiveCitation] = useState<string | null>(null);
  const [loadingVideos, setLoadingVideos] = useState(true);
  const [loadingAnalyses, setLoadingAnalyses] = useState(false);
  const [retrieving, setRetrieving] = useState(false);
  const [planning, setPlanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnalysesForAsset = useCallback(async (assetCode: string) => {
    if (!assetCode) {
      setAnalyses([]);
      setSelectedAnalysis("");
      return;
    }
    setLoadingAnalyses(true);
    setError(null);
    try {
      const response = await fetchVideoAnalyses(assetCode);
      const completed = response.data.filter((item) =>
        ["completed", "needs_review"].includes(item.status)
      );
      setAnalyses(completed);
      setSelectedAnalysis(completed[0]?.analysis_code ?? "");
      setRetrieval(null);
      setPlan(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load analyses.");
      setAnalyses([]);
      setSelectedAnalysis("");
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
        if (first) {
          await loadAnalysesForAsset(first);
        }
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

  async function handleAssetChange(assetCode: string) {
    setSelectedAsset(assetCode);
    await loadAnalysesForAsset(assetCode);
  }

  async function handleRetrieve() {
    if (!selectedAnalysis) return;
    setRetrieving(true);
    setError(null);
    setPlan(null);
    try {
      const result = await retrieveProceduresForAnalysis(selectedAnalysis);
      setRetrieval(result);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Retrieval failed."
      );
    } finally {
      setRetrieving(false);
    }
  }

  async function handlePlan() {
    if (!selectedAnalysis) return;
    setPlanning(true);
    setError(null);
    try {
      const result = await generateResponsePlan(
        selectedAnalysis,
        retrieval?.id
      );
      setPlan(result);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Plan generation failed."
      );
    } finally {
      setPlanning(false);
    }
  }

  return (
    <section className="space-y-4 rounded-xl border border-border bg-panel p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Policy retrieval & response plan
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Stage 5 generates grounded recommendations only. Actions are not
            executed.
          </p>
        </div>
        <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-100">
          Recommended, not executed
        </span>
      </div>

      {loadingVideos ? (
        <p className="text-sm text-muted-foreground">Loading ready videos…</p>
      ) : videos.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No ready videos with analyses yet. Upload and analyze a video on
          Monitor first.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="space-y-1 text-xs text-muted-foreground">
            Video asset
            <select
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
              value={selectedAsset}
              onChange={(event) => void handleAssetChange(event.target.value)}
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
        <Button
          size="sm"
          onClick={() => void handleRetrieve()}
          disabled={!selectedAnalysis || retrieving}
        >
          {retrieving ? (
            <Loader2 className="size-4 animate-spin" data-icon="inline-start" />
          ) : (
            <BookOpenCheck data-icon="inline-start" />
          )}
          Retrieve procedure
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => void handlePlan()}
          disabled={!selectedAnalysis || planning}
        >
          {planning ? (
            <Loader2 className="size-4 animate-spin" data-icon="inline-start" />
          ) : (
            <Sparkles data-icon="inline-start" />
          )}
          Generate response plan
        </Button>
      </div>

      {error ? (
        <div
          className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-red-200"
          role="alert"
        >
          {error}
        </div>
      ) : null}

      {retrieval ? (
        <div className="space-y-3 rounded-lg border border-border bg-background/40 p-3">
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-md border border-border px-2 py-1">
              {retrieval.retrieval_code}
            </span>
            <span className="rounded-md border border-border px-2 py-1">
              method: {retrieval.method}
            </span>
            <span className="rounded-md border border-border px-2 py-1 capitalize">
              status: {retrieval.status}
            </span>
          </div>
          {retrieval.status === "insufficient" ? (
            <p className="text-sm text-muted-foreground">
              {retrieval.message ?? "No adequate procedure matches were found."}
            </p>
          ) : (
            <ul className="space-y-2">
              {retrieval.matches.map((match) => (
                <li
                  key={`${match.chunk_id}-${match.rank}`}
                  className="rounded-lg border border-border/70 p-3 text-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                    <span>
                      #{match.rank} · {match.procedure_code} · {match.chunk_code}
                      {match.section_heading ? ` · ${match.section_heading}` : ""}
                      {match.page_number != null ? ` · p.${match.page_number}` : ""}
                    </span>
                    <span>score {match.score.toFixed(3)}</span>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-slate-200">
                    {match.excerpt}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      {plan ? (
        <div className="space-y-4 rounded-lg border border-border bg-background/40 p-3">
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-md border border-border px-2 py-1">
              {plan.plan_code}
            </span>
            <span className="rounded-md border border-border px-2 py-1">
              {plan.provider_label}
            </span>
            <span className="rounded-md border border-border px-2 py-1 capitalize">
              {plan.status.replaceAll("_", " ")}
            </span>
            <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-amber-100">
              Not executed
            </span>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Summary</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {plan.summary ?? "No summary."}
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Rationale</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {plan.rationale ?? "No rationale."}
            </p>
          </div>
          {plan.status === "insufficient_policy" ? (
            <p className="text-sm text-amber-100">
              Insufficient verified policy evidence — no invented recommendations
              were produced.
            </p>
          ) : null}
          {plan.status === "failed" ? (
            <p className="text-sm text-red-200" role="alert">
              {plan.error_message ?? "Plan generation failed."}
            </p>
          ) : null}
          <ul className="space-y-3">
            {plan.actions.map((action) => (
              <li key={action.id} className="rounded-lg border border-border p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {action.action_order}. {action.title}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {action.responsible_role}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-1 text-[11px]">
                    <span className="rounded border border-border px-2 py-0.5 capitalize">
                      {action.priority}
                    </span>
                    {action.requires_human_approval ? (
                      <span className="rounded border border-primary/40 px-2 py-0.5 text-primary">
                        Human approval required
                      </span>
                    ) : null}
                  </div>
                </div>
                <p className="mt-2 text-sm text-slate-200">{action.description}</p>
                {action.citations.length > 0 ? (
                  <div className="mt-3 space-y-2">
                    <p className="text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
                      Citations
                    </p>
                    {action.citations.map((cite) => (
                      <button
                        key={cite.id}
                        type="button"
                        className="block w-full rounded-md border border-border/70 bg-secondary/20 p-2 text-left text-xs hover:border-primary/50"
                        onClick={() =>
                          setActiveCitation(
                            activeCitation === cite.id ? null : cite.id
                          )
                        }
                      >
                        <span className="text-muted-foreground">
                          {cite.procedure_code} · {cite.chunk_code}
                          {cite.section_heading ? ` · ${cite.section_heading}` : ""}
                        </span>
                        {activeCitation === cite.id ? (
                          <span className="mt-2 block whitespace-pre-wrap text-slate-200">
                            {cite.excerpt}
                          </span>
                        ) : (
                          <span className="mt-1 block text-muted-foreground">
                            Click to show exact stored excerpt
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
          {plan.limitations.length > 0 ? (
            <div className="rounded-md border border-border/80 p-3 text-xs text-muted-foreground">
              <div className="mb-1 flex items-center gap-2 font-semibold">
                <ClipboardList className="size-3.5" />
                Limitations
              </div>
              <ul className="list-disc space-y-1 pl-5">
                {plan.limitations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
