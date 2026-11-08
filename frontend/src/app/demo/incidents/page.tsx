"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { EmptyState } from "@/components/EmptyState";
import {
  ConnectionBanner,
  PanelSkeleton,
} from "@/components/ConnectionBanner";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useApiResource } from "@/hooks/useApiResource";
import { fetchIncidents } from "@/lib/api";
import { mapIncident } from "@/lib/api/mappers";
import { getFallbackIncidents } from "@/data/fallback";
import { isDemoFallbackEnabled } from "@/lib/api/client";
import type { Incident, IncidentSeverity, IncidentStatus } from "@/types";

type SeverityFilter = "all" | IncidentSeverity;
type StatusFilter = "all" | IncidentStatus;

function toApiStatus(status: StatusFilter): string | undefined {
  if (status === "all") return undefined;
  if (status === "in_progress") return "approved";
  return status;
}

export default function IncidentsPage() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [severity, setSeverity] = useState<SeverityFilter>("all");
  const [status, setStatus] = useState<StatusFilter>("all");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  const loader = useCallback(async () => {
    const response = await fetchIncidents({
      severity: severity === "all" ? undefined : severity,
      status: toApiStatus(status),
      search: debouncedQuery || undefined,
      limit: 50,
    });
    return {
      incidents: response.data.map(mapIncident),
      count: response.meta.count,
    };
  }, [debouncedQuery, severity, status]);

  const fallback = useCallback(() => {
    let list = getFallbackIncidents();
    if (severity !== "all") {
      list = list.filter((item) => item.severity === severity);
    }
    if (status !== "all") {
      list = list.filter((item) => item.status === status);
    }
    if (debouncedQuery) {
      const q = debouncedQuery.toLowerCase();
      list = list.filter(
        (item) =>
          item.title.toLowerCase().includes(q) ||
          item.id.toLowerCase().includes(q) ||
          item.location.toLowerCase().includes(q)
      );
    }
    return { incidents: list, count: list.length };
  }, [debouncedQuery, severity, status]);

  const { data, error, source, isLoading, reload } = useApiResource({
    loader,
    fallback,
  });

  const incidents: Incident[] = data?.incidents ?? [];

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <ConnectionBanner
        mode={source === "fallback" ? "fallback" : source === "error" ? "error" : "api"}
        message={error}
        onRetry={reload}
      />

      <PageHeader
        title="Incidents"
        subtitle="Search, filter, and review facility safety events"
        status={
          <span className="rounded-md border border-border bg-panel px-2.5 py-1 text-xs text-muted-foreground">
            {data?.count ?? 0} incidents
            {source === "fallback" ? " · Demo Data" : ""}
          </span>
        }
      />

      <section className="grid gap-3 rounded-xl border border-border bg-panel p-4 md:grid-cols-2 xl:grid-cols-3">
        <label className="block space-y-1.5 md:col-span-2 xl:col-span-1">
          <span className="text-xs font-medium text-muted-foreground">Search</span>
          <div className="relative">
            <Search
              className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search incidents"
              className="pl-9"
              aria-label="Search incidents"
            />
          </div>
        </label>

        <label className="block space-y-1.5">
          <span className="text-xs font-medium text-muted-foreground">Severity</span>
          <Select
            value={severity}
            onValueChange={(value) => {
              if (value) setSeverity(value as SeverityFilter);
            }}
          >
            <SelectTrigger className="w-full" aria-label="Filter by severity">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All severities</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </label>

        <label className="block space-y-1.5">
          <span className="text-xs font-medium text-muted-foreground">Status</span>
          <Select
            value={status}
            onValueChange={(value) => {
              if (value) setStatus(value as StatusFilter);
            }}
          >
            <SelectTrigger className="w-full" aria-label="Filter by status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="awaiting_review">Awaiting Review</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
            </SelectContent>
          </Select>
        </label>
      </section>

      {isLoading ? <PanelSkeleton className="min-h-64" /> : null}

      {!isLoading && source === "error" && !isDemoFallbackEnabled() ? (
        <EmptyState
          title="Unable to load incidents"
          description={error ?? "Start the backend API and retry."}
          actionLabel="Retry"
          onAction={reload}
        />
      ) : null}

      {!isLoading && incidents.length === 0 && source !== "error" ? (
        <EmptyState
          title="No incidents match these filters"
          description="Adjust search or filter criteria to view incident records."
          actionLabel="Clear filters"
          onAction={() => {
            setQuery("");
            setSeverity("all");
            setStatus("all");
          }}
        />
      ) : null}

      {!isLoading && incidents.length > 0 ? (
        <div className="overflow-hidden rounded-xl border border-border bg-panel">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-border bg-secondary/40 text-xs tracking-wide text-muted-foreground uppercase">
                <tr>
                  <th className="px-4 py-3 font-medium">Incident</th>
                  <th className="px-4 py-3 font-medium">Location</th>
                  <th className="px-4 py-3 font-medium">Severity</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Detected</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((incident) => (
                  <tr
                    key={incident.id}
                    className="border-b border-border/70 last:border-0 hover:bg-secondary/30"
                  >
                    <td className="px-4 py-3">
                      <p className="font-medium text-foreground">{incident.title}</p>
                      <p className="font-mono text-xs text-muted-foreground">
                        {incident.id}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {incident.location}
                    </td>
                    <td className="px-4 py-3">
                      <SeverityBadge severity={incident.severity} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={incident.status} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {incident.relativeTime}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={
                          incident.status === "awaiting_review"
                            ? "/response"
                            : "/incidents"
                        }
                        className="text-sm font-medium text-primary hover:underline"
                      >
                        View details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
