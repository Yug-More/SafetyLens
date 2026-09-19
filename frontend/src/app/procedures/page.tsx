"use client";

import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { ProcedureCard, ProcedureUploadButton } from "@/components/ProcedureCard";
import { EmptyState } from "@/components/EmptyState";
import {
  ConnectionBanner,
  PanelSkeleton,
} from "@/components/ConnectionBanner";
import { Input } from "@/components/ui/input";
import { useApiResource } from "@/hooks/useApiResource";
import { fetchProcedures } from "@/lib/api";
import { mapProcedure } from "@/lib/api/mappers";
import { getFallbackProcedures } from "@/data/fallback";

export default function ProceduresPage() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(query.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  const loader = useCallback(async () => {
    const response = await fetchProcedures({
      search: debouncedQuery || undefined,
      active: true,
      limit: 50,
    });
    return response.data.map(mapProcedure);
  }, [debouncedQuery]);

  const fallback = useCallback(() => {
    const all = getFallbackProcedures();
    if (!debouncedQuery) return all;
    const q = debouncedQuery.toLowerCase();
    return all.filter(
      (procedure) =>
        procedure.title.toLowerCase().includes(q) ||
        procedure.category.toLowerCase().includes(q) ||
        procedure.section.toLowerCase().includes(q)
    );
  }, [debouncedQuery]);

  const { data, error, source, isLoading, reload } = useApiResource({
    loader,
    fallback,
  });

  const procedures = data ?? [];

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <ConnectionBanner
        mode={source === "fallback" ? "fallback" : source === "error" ? "error" : "api"}
        message={error}
        onRetry={reload}
      />

      <PageHeader
        title="Procedures"
        subtitle="Company safety procedure library for Redwood Distribution Center"
        actions={<ProcedureUploadButton />}
      />

      <div className="rounded-xl border border-border bg-panel p-4">
        <label className="block max-w-md space-y-1.5">
          <span className="text-xs font-medium text-muted-foreground">
            Search procedures
          </span>
          <div className="relative">
            <Search
              className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by title, category, or section"
              className="pl-9"
              aria-label="Search procedures"
            />
          </div>
        </label>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <PanelSkeleton />
          <PanelSkeleton />
          <PanelSkeleton />
          <PanelSkeleton />
        </div>
      ) : null}

      {!isLoading && source === "error" ? (
        <EmptyState
          title="Unable to load procedures"
          description={error ?? "Start the backend API and retry."}
          actionLabel="Retry"
          onAction={reload}
        />
      ) : null}

      {!isLoading && procedures.length === 0 && source !== "error" ? (
        <EmptyState
          title="No procedures found"
          description="Try a different search term or clear the filter to browse the library."
          actionLabel="Clear search"
          onAction={() => setQuery("")}
        />
      ) : null}

      {!isLoading && procedures.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {procedures.map((procedure) => (
            <ProcedureCard key={procedure.id} procedure={procedure} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
