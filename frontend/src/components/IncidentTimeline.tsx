import Link from "next/link";
import {
  AlertTriangle,
  HardHat,
  DoorClosed,
  ShieldAlert,
  ChevronRight,
} from "lucide-react";
import { cn } from "cn";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import type { Incident, IncidentSeverity } from "@/types";

const severityIcons = {
  high: AlertTriangle,
  medium: ShieldAlert,
  low: DoorClosed,
} as const;

function getIncidentIcon(title: string, severity: IncidentSeverity) {
  if (title.toLowerCase().includes("helmet")) {
    return HardHat;
  }
  if (title.toLowerCase().includes("exit")) {
    return DoorClosed;
  }
  return severityIcons[severity];
}

interface IncidentTimelineProps {
  incidents: Incident[];
  className?: string;
}

export function IncidentTimeline({ incidents, className }: IncidentTimelineProps) {
  return (
    <section
      className={cn(
        "rounded-xl border border-border bg-panel p-4 shadow-sm",
        className
      )}
    >
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">Incident Timeline</h2>
          <p className="text-sm text-muted-foreground">
            Recent facility events · Demo data
          </p>
        </div>
        <Link
          href="/incidents"
          className="text-sm font-medium text-primary hover:underline"
        >
          View all
        </Link>
      </div>

      <ol className="space-y-3">
        {incidents.map((incident, index) => {
          const Icon = getIncidentIcon(incident.title, incident.severity);

          return (
            <li key={incident.id}>
              <Link
                href={
                  incident.status === "awaiting_review"
                    ? "/response"
                    : `/incidents`
                }
                className="group flex items-start gap-3 rounded-lg border border-transparent p-2.5 transition hover:border-border hover:bg-secondary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <div className="relative mt-0.5">
                  <div
                    className={cn(
                      "flex size-9 items-center justify-center rounded-lg border",
                      incident.severity === "high" &&
                        "border-destructive/30 bg-destructive/10 text-red-300",
                      incident.severity === "medium" &&
                        "border-warning/30 bg-warning/10 text-amber-300",
                      incident.severity === "low" &&
                        "border-slate-500/30 bg-slate-500/10 text-slate-300"
                    )}
                  >
                    <Icon className="size-4" aria-hidden="true" />
                  </div>
                  {index < incidents.length - 1 ? (
                    <span className="absolute top-10 left-1/2 h-[calc(100%+0.25rem)] w-px -translate-x-1/2 bg-border" />
                  ) : null}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="truncate text-sm font-medium text-foreground">
                      {incident.title}
                    </h3>
                    <SeverityBadge severity={incident.severity} />
                    <StatusBadge status={incident.status} />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {incident.location} · {incident.relativeTime}
                  </p>
                </div>

                <span className="mt-1 inline-flex items-center gap-0.5 text-xs text-muted-foreground opacity-0 transition group-hover:opacity-100">
                  Details
                  <ChevronRight className="size-3.5" aria-hidden="true" />
                </span>
              </Link>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
