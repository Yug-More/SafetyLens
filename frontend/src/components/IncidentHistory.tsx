"use client";
import { useCallback, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useApiResource } from "@/hooks/useApiResource";
import { apiGetCollection, getApiBaseUrl } from "@/lib/api/client";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
interface Row {
  id: string;
  incident_code: string;
  title: string;
  severity: string;
  status: string;
  camera_name: string;
  incident_type: string;
  detected_at: string;
}
const empty = () => ({
  data: [] as Row[],
  meta: { count: 0, limit: 20, offset: 0 },
});
export function IncidentHistory({ ppeOnly = false }: { ppeOnly?: boolean }) {
  const params = useSearchParams();
  const [search, setSearch] = useState(params.get("search") ?? "");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");
  const [ascending, setAscending] = useState(false);
  const loader = useCallback(
    () =>
      apiGetCollection<Row>("/api/incidents", {
        search: ppeOnly ? "ppe" : search,
        severity,
        status,
        offset,
        limit: 20,
        since: since ? `${since}T00:00:00Z` : undefined,
        until: until ? `${until}T23:59:59Z` : undefined,
        ascending,
      }),
    [search, severity, status, offset, since, until, ascending, ppeOnly],
  );
  const { data, error, isLoading, reload } = useApiResource({
    loader,
    fallback: empty,
    allowFallback: false,
  });
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <PageHeader
        title={ppeOnly ? "PPE compliance review" : "Incident history"}
        subtitle={
          ppeOnly
            ? "Possible noncompliance requires visual verification; no model accuracy is inferred from reviews."
            : "Search stored incidents and open evidence-linked investigations."
        }
        actions={
          <a
            className="text-sm text-blue-400"
            href={`${getApiBaseUrl()}/api/incidents-export`}
          >
            Export CSV
          </a>
        }
      />
      <div className="grid gap-3 rounded-xl border border-border bg-panel p-4 sm:grid-cols-2 xl:grid-cols-6">
        {!ppeOnly && (
          <Input
            aria-label="Search incidents"
            placeholder="Search incidents…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setOffset(0);
            }}
          />
        )}
        <select
          aria-label="Incident severity"
          className="rounded border border-border bg-panel p-2"
          value={severity}
          onChange={(e) => {
            setSeverity(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">All severity</option>
          {["critical", "high", "medium", "low"].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
        <select
          aria-label="Incident status"
          className="rounded border border-border bg-panel p-2"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">All status</option>
          {[
            "detected",
            "awaiting_review",
            "approved",
            "resolved",
            "dismissed",
          ].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
        <label className="text-xs text-muted-foreground">
          From (UTC)
          <Input
            aria-label="From date"
            type="date"
            value={since}
            onChange={(e) => {
              setSince(e.target.value);
              setOffset(0);
            }}
          />
        </label>
        <label className="text-xs text-muted-foreground">
          Through (UTC)
          <Input
            aria-label="Through date"
            type="date"
            value={until}
            min={since}
            onChange={(e) => {
              setUntil(e.target.value);
              setOffset(0);
            }}
          />
        </label>
        <Button variant="outline" onClick={() => setAscending((x) => !x)}>
          {ascending ? "Oldest first" : "Newest first"}
        </Button>
      </div>
      {error && (
        <p role="alert" className="text-red-300">
          {error}
          <Button onClick={reload}>Retry</Button>
        </p>
      )}
      <section
        aria-label="Incident records"
        className="overflow-hidden rounded-xl border border-border bg-panel"
      >
        {isLoading ? (
          <p className="p-10" role="status">
            Loading incidents…
          </p>
        ) : !data?.data.length ? (
          <div className="p-12 text-center">
            <h2 className="font-semibold">No matching incidents</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Try a broader date range or adjust filters.
            </p>
          </div>
        ) : (
          data.data.map((row) => (
            <Link
              className="grid gap-3 border-b border-border p-5 last:border-0 hover:bg-secondary/40 md:grid-cols-[1fr_120px_140px]"
              key={row.id}
              href={`/investigate/${row.id}`}
            >
              <div>
                <p className="text-xs text-muted-foreground">
                  {row.incident_code} · {row.camera_name} ·{" "}
                  {new Date(row.detected_at).toLocaleString()}
                </p>
                <h2 className="mt-1 font-medium">{row.title}</h2>
              </div>
              <span className="text-sm text-amber-300">{row.severity}</span>
              <span className="text-xs text-muted-foreground">
                {row.status.replaceAll("_", " ")}
              </span>
            </Link>
          ))
        )}
      </section>
      <div className="flex items-center justify-between text-sm">
        <p className="text-muted-foreground">
          {data?.meta.count ?? 0} records · page {Math.floor(offset / 20) + 1}
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={offset === 0 || isLoading}
            onClick={() => setOffset((x) => Math.max(0, x - 20))}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            disabled={isLoading || offset + 20 >= (data?.meta.count ?? 0)}
            onClick={() => setOffset((x) => x + 20)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
