import {
  AlertTriangle,
  Clapperboard,
  FileSearch,
  UserCheck,
  CircleCheck,
  Server,
} from "lucide-react";
import { cn } from "cn";
import type { ActivityEvent } from "@/types";

const iconMap = {
  alert: AlertTriangle,
  clip: Clapperboard,
  procedure: FileSearch,
  review: UserCheck,
  resolved: CircleCheck,
  system: Server,
} as const;

const statusDot = {
  success: "bg-emerald-400",
  pending: "bg-amber-400",
  info: "bg-blue-400",
  warning: "bg-red-400",
} as const;

interface ActivityFeedProps {
  events: ActivityEvent[];
  className?: string;
}

export function ActivityFeed({ events, className }: ActivityFeedProps) {
  return (
    <section
      className={cn(
        "rounded-xl border border-border bg-panel p-4 shadow-sm",
        className
      )}
    >
      <div className="mb-4">
        <h2 className="text-base font-semibold text-foreground">Recent Activity</h2>
        <p className="text-sm text-muted-foreground">Audit-style event trail</p>
      </div>

      <ul className="space-y-2">
        {events.map((event) => {
          const Icon = iconMap[event.icon];

          return (
            <li
              key={event.id}
              className="flex items-start gap-3 rounded-lg border border-transparent px-2 py-2.5 hover:border-border hover:bg-secondary/40"
            >
              <div className="rounded-md border border-border bg-secondary p-2 text-muted-foreground">
                <Icon className="size-3.5" aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm text-foreground">{event.description}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">{event.timestamp}</p>
              </div>
              <span
                className={cn("mt-1.5 size-2 rounded-full", statusDot[event.status])}
                aria-label={`Status: ${event.status}`}
              />
            </li>
          );
        })}
      </ul>
    </section>
  );
}
