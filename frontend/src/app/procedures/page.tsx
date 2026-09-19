"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { ProcedureCard, ProcedureUploadButton } from "@/components/ProcedureCard";
import { EmptyState } from "@/components/EmptyState";
import { Input } from "@/components/ui/input";
import { procedures } from "@/data/mock";

export default function ProceduresPage() {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return procedures;
    }

    return procedures.filter(
      (procedure) =>
        procedure.title.toLowerCase().includes(normalized) ||
        procedure.category.toLowerCase().includes(normalized) ||
        procedure.section.toLowerCase().includes(normalized)
    );
  }, [query]);

  return (
    <div className="mx-auto max-w-7xl space-y-6">
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

      {filtered.length === 0 ? (
        <EmptyState
          title="No procedures found"
          description="Try a different search term or clear the filter to browse the demo library."
          actionLabel="Clear search"
          onAction={() => setQuery("")}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {filtered.map((procedure) => (
            <ProcedureCard key={procedure.id} procedure={procedure} />
          ))}
        </div>
      )}
    </div>
  );
}
