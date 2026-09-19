import { cn } from "cn";
import type { IncidentStatus } from "@/types";

const statusStyles: Record<IncidentStatus, string> = {
  awaiting_review: "border-warning/30 bg-warning/10 text-amber-300",
  in_progress: "border-info/30 bg-info/10 text-blue-300",
  resolved: "border-success/30 bg-success/10 text-emerald-300",
  closed: "border-slate-500/30 bg-slate-500/10 text-slate-300",
};

const statusLabels: Record<IncidentStatus, string> = {
  awaiting_review: "Awaiting Review",
  in_progress: "In Progress",
  resolved: "Resolved",
  closed: "Closed",
};

interface StatusBadgeProps {
  status: IncidentStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
        statusStyles[status],
        className
      )}
    >
      {statusLabels[status]}
    </span>
  );
}
