import { cn } from "cn";
import type { IncidentSeverity } from "@/types";

const severityStyles: Record<IncidentSeverity, string> = {
  high: "border-destructive/30 bg-destructive/15 text-red-300",
  medium: "border-warning/30 bg-warning/15 text-amber-300",
  low: "border-slate-500/30 bg-slate-500/15 text-slate-300",
};

const severityLabels: Record<IncidentSeverity, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

interface SeverityBadgeProps {
  severity: IncidentSeverity;
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        severityStyles[severity],
        className
      )}
    >
      {severityLabels[severity]}
    </span>
  );
}
