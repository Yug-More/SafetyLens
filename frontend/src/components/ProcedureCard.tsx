"use client";

import { FileText, Upload } from "lucide-react";
import { toast } from "sonner";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import type { SafetyProcedure } from "@/types";

interface ProcedureCardProps {
  procedure: SafetyProcedure;
  className?: string;
  compact?: boolean;
}

export function ProcedureCard({
  procedure,
  className,
  compact = false,
}: ProcedureCardProps) {
  return (
    <article
      className={cn(
        "flex h-full flex-col rounded-xl border border-border bg-panel p-4 shadow-sm transition hover:border-border/80 hover:bg-panel-elevated",
        className
      )}
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="rounded-lg border border-border bg-secondary p-2.5 text-primary">
          <FileText className="size-4" aria-hidden="true" />
        </div>
        <span className="rounded-md border border-border bg-secondary px-2 py-1 text-[11px] text-muted-foreground">
          {procedure.category}
        </span>
      </div>

      <h3 className="text-base font-semibold text-foreground">{procedure.title}</h3>
      <p className="mt-1 text-xs font-medium text-primary">{procedure.section}</p>
      <p className="mt-2 text-sm text-muted-foreground">{procedure.description}</p>

      {!compact ? (
        <ol className="mt-4 space-y-1.5 text-sm text-slate-300">
          {procedure.steps.slice(0, 3).map((step, index) => (
            <li key={step} className="flex gap-2">
              <span className="text-muted-foreground">{index + 1}.</span>
              <span>{step}</span>
            </li>
          ))}
          {procedure.steps.length > 3 ? (
            <li className="text-xs text-muted-foreground">
              +{procedure.steps.length - 3} more steps
            </li>
          ) : null}
        </ol>
      ) : null}

      <div className="mt-auto flex items-center justify-between gap-3 pt-4 text-xs text-muted-foreground">
        <span>
          Updated {procedure.lastUpdated} · {procedure.documentPages} pages
        </span>
        <Button
          size="sm"
          variant="ghost"
          onClick={() =>
            toast.message("Procedure detail view will expand in a later stage.")
          }
        >
          Open
        </Button>
      </div>
    </article>
  );
}

interface ProcedureUploadButtonProps {
  className?: string;
}

export function ProcedureUploadButton({ className }: ProcedureUploadButtonProps) {
  return (
    <Button
      className={className}
      onClick={() =>
        toast.message("Document upload will be connected in a later stage.")
      }
    >
      <Upload data-icon="inline-start" />
      Upload Procedure
    </Button>
  );
}
