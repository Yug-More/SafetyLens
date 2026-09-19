"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle2, ChevronDown, Circle, Loader2, RotateCcw } from "lucide-react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog } from "@/components/ConfirmationDialog";
import { ApiError } from "@/lib/api/client";
import { resetDemoState } from "@/lib/api";

const STEPS = [
  "Reset demo state (optional)",
  "Upload or select the worker-fall clip on Live Monitor",
  "Wait for frame processing to complete",
  "Run Demo AI analysis and review evidence timestamps",
  "Open Response Center → retrieve SOP-FALL-4.2",
  "Generate a cited response plan",
  "Approve selected actions (confirmation required)",
  "Run simulated execution — every step labeled SIMULATED",
  "Review the audit timeline",
  "Generate and download the PDF incident report",
] as const;

export function GuidedDemoPanel({
  defaultCollapsed = false,
}: {
  defaultCollapsed?: boolean;
}) {
  const [expanded, setExpanded] = useState(!defaultCollapsed);
  const [checked, setChecked] = useState<boolean[]>(() => STEPS.map(() => false));
  const [resetOpen, setResetOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function confirmReset() {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await resetDemoState(true);
      setMessage(result.message);
      setChecked(STEPS.map(() => false));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Demo reset failed.");
    } finally {
      setBusy(false);
      setResetOpen(false);
    }
  }

  return (
    <section className="space-y-3 rounded-xl border border-border bg-panel p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <button
          type="button"
          className="flex min-w-0 flex-1 items-start gap-2 text-left"
          onClick={() => setExpanded((value) => !value)}
          aria-expanded={expanded}
        >
          <ChevronDown
            className={cn(
              "mt-0.5 size-4 shrink-0 text-muted-foreground transition-transform",
              expanded ? "rotate-0" : "-rotate-90"
            )}
            aria-hidden="true"
          />
          <div>
            <h2 className="text-base font-semibold text-foreground">Guided demo journey</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Backend-driven checklist for the worker-fall path. Checklist marks are local only —
              each product step still uses live API state.
            </p>
          </div>
        </button>
        <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-100">
          SIMULATED actions / Demo AI
        </span>
      </div>

      {expanded ? (
        <>
      <ol className="space-y-2">
        {STEPS.map((step, index) => (
          <li key={step}>
            <button
              type="button"
              className="flex w-full items-start gap-2 rounded-md border border-border/70 px-3 py-2 text-left text-sm hover:bg-secondary/40"
              onClick={() =>
                setChecked((current) =>
                  current.map((value, itemIndex) =>
                    itemIndex === index ? !value : value
                  )
                )
              }
            >
              {checked[index] ? (
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-400" />
              ) : (
                <Circle className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
              )}
              <span className={checked[index] ? "text-muted-foreground line-through" : ""}>
                {index + 1}. {step}
              </span>
            </button>
          </li>
        ))}
      </ol>

      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" disabled={busy} onClick={() => setResetOpen(true)}>
          {busy ? (
            <Loader2 className="size-4 animate-spin" data-icon="inline-start" />
          ) : (
            <RotateCcw data-icon="inline-start" />
          )}
          Reset demo state
        </Button>
        <Link
          href="/monitor"
          className="inline-flex h-7 items-center rounded-lg border border-border bg-background px-2.5 text-[0.8rem] font-medium hover:bg-muted"
        >
          Live Monitor
        </Link>
        <Link
          href="/response"
          className="inline-flex h-7 items-center rounded-lg border border-border bg-background px-2.5 text-[0.8rem] font-medium hover:bg-muted"
        >
          Response Center
        </Link>
        <Link
          href="/reports"
          className="inline-flex h-7 items-center rounded-lg border border-border bg-background px-2.5 text-[0.8rem] font-medium hover:bg-muted"
        >
          Reports
        </Link>
        <Link
          href="/demo-help"
          className="inline-flex h-7 items-center rounded-lg border border-border bg-background px-2.5 text-[0.8rem] font-medium hover:bg-muted"
        >
          Demo Guide
        </Link>
      </div>

      {message ? (
        <p className="rounded-md border border-emerald-500/30 bg-emerald-500/10 p-2 text-xs text-emerald-100">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-red-200" role="alert">
          {error}
        </p>
      ) : null}

      <ConfirmationDialog
        open={resetOpen}
        onOpenChange={setResetOpen}
        title="Reset demo state?"
        description="This clears uploaded clips, detector ingestions, analyses, plans, executions, and generated reports from configured demo directories, then restores seed data. It will not delete arbitrary files outside demo storage roots."
        confirmLabel="Confirm demo reset"
        onConfirm={() => void confirmReset()}
      />
        </>
      ) : null}
    </section>
  );
}
