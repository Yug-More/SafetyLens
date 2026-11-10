"use client";
import Link from "next/link";
import { useCallback, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Camera,
  CheckCircle2,
  ShieldAlert,
  RefreshCw,
} from "lucide-react";
import { useApiResource } from "@/hooks/useApiResource";
import {
  platformRequest,
  type ManagedCamera,
  type SafetyAnalytics,
} from "@/lib/api/platform";
import { apiGetCollection, getApiBaseUrl } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/PageHeader";
interface Incident {
  id: string;
  incident_code: string;
  title: string;
  camera_name: string;
  severity: string;
  status: string;
  detected_at: string;
}
const empty = () => ({
  cameras: [] as ManagedCamera[],
  analytics: null as SafetyAnalytics | null,
  incidents: [] as Incident[],
});

export function OperationsConsole({
  analyticsOnly = false,
}: {
  analyticsOnly?: boolean;
}) {
  const [search, setSearch] = useState("");
  const [days, setDays] = useState(30);
  const loader = useCallback(async () => {
    const [cameras, analytics, incidents] = await Promise.all([
      platformRequest<ManagedCamera[]>("/api/camera-management"),
      platformRequest<SafetyAnalytics>(`/api/analytics?days=${days}`),
      apiGetCollection<Incident>("/api/incidents", { limit: 10, search }),
    ]);
    return { cameras, analytics, incidents: incidents.data };
  }, [search, days]);
  const { data, error, isLoading, reload } = useApiResource({
    loader,
    fallback: empty,
    allowFallback: false,
  });
  const stats = data?.analytics;
  const online =
    data?.cameras.filter(
      (x) => x.status === "online" && x.capability_status !== "demo_simulation",
    ).length ?? 0;
  return (
    <div className="mx-auto max-w-[1500px] space-y-7">
      <PageHeader
        title={analyticsOnly ? "Safety analytics" : "Operations overview"}
        subtitle="Evidence first. Human decisions. Traceable response."
        actions={
          <Button variant="outline" onClick={reload}>
            <RefreshCw />
            Refresh
          </Button>
        }
      />
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-blue-400/20 bg-blue-500/5 px-4 py-3 text-sm">
        <span>
          <Activity className="mr-2 inline size-4 text-blue-400" />
          Live application records · camera previews require a connected worker
        </span>
        <label className="text-muted-foreground">
          Time window{" "}
          <select
            aria-label="Analytics time window"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="ml-2 rounded border border-border bg-panel p-2"
          >
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={365}>365 days</option>
          </select>
        </label>
      </div>
      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-400/30 p-4 text-red-300"
        >
          {error}
          <Button onClick={reload} variant="outline" className="ml-4">
            Retry
          </Button>
        </div>
      )}
      <section
        aria-label="Operational metrics"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        {[
          {
            label: "Connected cameras",
            value: online,
            detail: `${data?.cameras.length ?? 0} registered · seed records excluded`,
            icon: Camera,
          },
          {
            label: "Incident records",
            value: stats?.incidents,
            detail: `Last ${days} days · may include demo seeds`,
            icon: ShieldAlert,
          },
          {
            label: "Confirmed reviews",
            value: stats?.confirmed_reviews,
            detail: "Human decisions, not detector accuracy",
            icon: CheckCircle2,
          },
          {
            label: "Mean review interval",
            value:
              stats?.mean_review_seconds == null
                ? "—"
                : `${Math.round(stats.mean_review_seconds)}s`,
            detail: `${stats?.review_sample_size ?? 0} reviewed analyses`,
            icon: Activity,
          },
        ].map((metric) => (
          <article
            key={metric.label}
            className="rounded-xl border border-border bg-panel p-5"
          >
            <div className="flex justify-between text-sm text-muted-foreground">
              {metric.label}
              <metric.icon className="size-4" />
            </div>
            <p className="mt-4 text-4xl font-semibold tracking-tight">
              {isLoading ? "…" : (metric.value ?? "—")}
            </p>
            <p className="mt-3 text-xs text-muted-foreground">
              {metric.detail}
            </p>
          </article>
        ))}
      </section>
      <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <section className="rounded-xl border border-border bg-panel p-5">
          <h2 className="text-base font-semibold">Incident activity</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Stored incidents by day. Missing dates have no recorded events.
          </p>
          <div
            className="mt-6 flex min-h-44 items-end gap-2 overflow-x-auto pb-4"
            role="img"
            aria-label={
              stats?.by_day
                .map(([day, n]) => `${day}: ${n} incidents`)
                .join("; ") || "No incidents in this time window"
            }
          >
            {!stats?.by_day.length ? (
              <p className="m-auto text-sm text-muted-foreground">
                No incidents recorded in this window.
              </p>
            ) : (
              stats.by_day.map(([day, n]) => (
                <div
                  className="flex min-w-16 flex-1 flex-col items-center gap-2"
                  key={day}
                >
                  <span className="text-xs">{n}</span>
                  <div
                    className="w-full rounded-t bg-blue-500/80"
                    style={{
                      height: `${Math.max(8, (120 * n) / Math.max(...stats.by_day.map((x) => x[1])))}px`,
                    }}
                  />
                  <span className="text-[10px] text-muted-foreground">
                    {day.slice(5)}
                  </span>
                </div>
              ))
            )}
          </div>
        </section>
        <section className="rounded-xl border border-border bg-panel p-5">
          <h2 className="font-semibold">Review outcomes</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {stats?.confirmed_reviews ?? 0} confirmed ·{" "}
            {stats?.rejected_reviews ?? 0} rejected
          </p>
          <p className="mt-5 text-3xl font-semibold">
            {stats?.false_alarm_review_fraction == null
              ? "—"
              : `${Math.round(stats.false_alarm_review_fraction * 100)}%`}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Rejected fraction among conclusive reviews. This is operational
            feedback, not a held-out false-positive rate.
          </p>
          <p className="mt-5 border-t border-border pt-4 text-xs text-muted-foreground">
            PPE accuracy and detector precision are available only from a
            labeled evaluation. No performance percentages are inferred from
            dashboard activity.
          </p>
        </section>
      </div>
      {!analyticsOnly && (
        <section className="rounded-xl border border-border bg-panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-semibold">Camera health</h2>
            <Link className="text-sm text-blue-400" href="/cameras">
              Manage cameras <ArrowUpRight className="inline size-4" />
            </Link>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {data?.cameras.slice(0, 8).map((camera) => (
              <div
                key={camera.id}
                className="rounded-lg border border-border p-4"
              >
                <p className="font-medium">{camera.name}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {camera.location}
                </p>
                <p
                  className={`mt-3 text-xs ${camera.status === "online" ? "text-emerald-300" : "text-amber-300"}`}
                >
                  {camera.capability_status === "demo_simulation"
                    ? "Historical demo · no live connection"
                    : camera.status}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}
      <section className="overflow-hidden rounded-xl border border-border bg-panel">
        <div className="flex flex-wrap items-center justify-between gap-3 p-5">
          <h2 className="font-semibold">Recent incidents</h2>
          <Input
            aria-label="Search recent incidents"
            className="max-w-xs"
            placeholder="Search incidents…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {isLoading && (
          <p role="status" className="p-6 text-muted-foreground">
            Loading records…
          </p>
        )}
        {!isLoading && !data?.incidents.length && (
          <div className="p-10 text-center">
            <CheckCircle2 className="mx-auto mb-3 size-7 text-muted-foreground" />
            <p>No matching incident records.</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Connected detectors will create reviewable records when evidence
              is available.
            </p>
          </div>
        )}
        {data?.incidents.map((incident) => (
          <Link
            key={incident.id}
            href={`/investigate/${incident.id}`}
            className="grid gap-2 border-t border-border p-5 transition hover:bg-secondary/40 sm:grid-cols-[1fr_auto_auto]"
          >
            <div>
              <p className="text-xs text-muted-foreground">
                {incident.incident_code} · {incident.camera_name}
              </p>
              <p className="mt-1 font-medium">{incident.title}</p>
            </div>
            <span className="text-sm text-amber-300">{incident.severity}</span>
            <span className="text-xs text-muted-foreground">
              {incident.status.replaceAll("_", " ")}
            </span>
          </Link>
        ))}
      </section>
      <p className="text-xs text-muted-foreground">
        Experimental decision support. Consequential actions remain
        human-approved and simulated.{" "}
        <a
          href={`${getApiBaseUrl()}/api/incidents-export`}
          className="text-blue-400 underline underline-offset-2"
        >
          Export incident CSV
        </a>
      </p>
    </div>
  );
}
