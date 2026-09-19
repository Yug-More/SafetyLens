"use client";

import { AlertTriangle, RefreshCw, WifiOff } from "lucide-react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";

interface ConnectionBannerProps {
  mode: "api" | "fallback" | "error";
  message?: string | null;
  onRetry?: () => void;
  className?: string;
}

export function ConnectionBanner({
  mode,
  message,
  onRetry,
  className,
}: ConnectionBannerProps) {
  if (mode === "api") {
    return null;
  }

  if (mode === "fallback") {
    return (
      <div
        className={cn(
          "mb-4 flex flex-col gap-3 rounded-xl border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-amber-100 sm:flex-row sm:items-center sm:justify-between",
          className
        )}
        role="status"
      >
        <div className="flex items-start gap-2">
          <WifiOff className="mt-0.5 size-4 shrink-0 text-amber-300" aria-hidden="true" />
          <div>
            <p className="font-medium text-amber-100">Offline Demo Mode</p>
            <p className="text-xs text-amber-100/80">
              API unavailable. Showing centralized demo data.
              {message ? ` (${message})` : null}
            </p>
          </div>
        </div>
        {onRetry ? (
          <Button variant="outline" size="sm" onClick={onRetry}>
            <RefreshCw data-icon="inline-start" />
            Retry connection
          </Button>
        ) : null}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "mb-4 flex flex-col gap-3 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-red-100 sm:flex-row sm:items-center sm:justify-between",
        className
      )}
      role="alert"
    >
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-red-300" aria-hidden="true" />
        <div>
          <p className="font-medium">Unable to connect to SafetyLens API</p>
          <p className="text-xs text-red-100/80">
            {message ?? "Start the backend or enable demo fallback."}
          </p>
        </div>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw data-icon="inline-start" />
          Retry
        </Button>
      ) : null}
    </div>
  );
}

export function PanelSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-xl border border-border bg-panel p-4",
        className
      )}
      aria-hidden="true"
    >
      <div className="mb-3 h-4 w-1/3 rounded bg-secondary" />
      <div className="mb-2 h-3 w-2/3 rounded bg-secondary/80" />
      <div className="h-24 rounded bg-secondary/60" />
    </div>
  );
}

export function MetricSkeleton() {
  return (
    <div className="animate-pulse rounded-xl border border-border bg-panel p-4">
      <div className="mb-3 h-3 w-24 rounded bg-secondary" />
      <div className="mb-2 h-8 w-16 rounded bg-secondary" />
      <div className="h-3 w-40 rounded bg-secondary/70" />
    </div>
  );
}
