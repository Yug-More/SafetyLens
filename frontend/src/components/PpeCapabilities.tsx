"use client";
import { useCallback } from "react";
import { platformRequest } from "@/lib/api/platform";
import { useApiResource } from "@/hooks/useApiResource";
import { Button } from "@/components/ui/button";

type Capability = { category: string; label: string; deployment_enabled: boolean; model_status: string; reason: string; metrics: { appearance_label: string; appearance_ap50: number | null } | null };
const empty = () => [] as Capability[];
export function PpeCapabilities() {
  const loader = useCallback(() => platformRequest<Capability[]>("/api/ppe-capabilities"), []);
  const { data, error, isLoading, reload } = useApiResource({ loader, fallback: empty, allowFallback: false });
  return <section aria-labelledby="ppe-capabilities" className="space-y-4">
    <div><h2 id="ppe-capabilities" className="text-lg font-semibold">PPE capability gates</h2>
      <p className="mt-1 text-sm text-muted-foreground">Eight configurable requirement categories. Each remains excluded from local deployment until its model, license and person-specific evaluation qualify. Object appearance cannot establish equipment certification.</p></div>
    {isLoading && <p role="status">Loading PPE model status…</p>}
    {error && <div role="alert" className="rounded-lg border border-amber-500/30 p-4">Model status unavailable: {error} <Button variant="outline" onClick={reload}>Retry model status</Button></div>}
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{data?.map(item => <article key={item.category} className="rounded-xl border border-border bg-panel p-4">
      <h3 className="font-medium">{item.label}</h3>
      <p className="mt-2 text-xs font-medium text-amber-400">{item.deployment_enabled ? "Enabled" : "Deployment disabled"}</p>
      <p className="mt-2 text-xs text-muted-foreground">{item.model_status === "experimental_offline_appearance" ? "Offline appearance diagnostic" : "No validated visual model"}</p>
      {item.metrics && <p className="mt-2 font-mono text-xs text-muted-foreground">{item.metrics.appearance_label.replaceAll("_", " ")} · AP50 {item.metrics.appearance_ap50?.toFixed(3) ?? "unmeasured"}</p>}
      <p className="mt-2 text-xs text-muted-foreground">{item.reason}</p>
    </article>)}</div>
    <p className="text-xs text-muted-foreground">Invisible equipment stays unknown. Ordinary glasses, shoes and medical masks do not prove protective rating. Human-confirmed findings remain distinct from CV and AI interpretations.</p>
  </section>;
}
