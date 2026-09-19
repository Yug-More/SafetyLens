import { CheckCircle2 } from "lucide-react";
import { cn } from "cn";
import type { SystemService } from "@/types";

interface SystemStatusProps {
  services: SystemService[];
  className?: string;
}

export function SystemStatus({ services, className }: SystemStatusProps) {
  return (
    <section
      className={cn(
        "rounded-xl border border-border bg-panel p-4 shadow-sm",
        className
      )}
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">System Status</h2>
          <p className="text-sm text-muted-foreground">
            Platform health across core services
          </p>
        </div>
        <span className="rounded-md border border-border bg-secondary px-2 py-1 text-[11px] font-medium text-muted-foreground">
          Demo Environment
        </span>
      </div>

      <ul className="space-y-2.5">
        {services.map((service) => (
          <li
            key={service.id}
            className="flex items-center justify-between gap-3 rounded-lg border border-border/70 bg-secondary/30 px-3 py-2.5"
          >
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground">{service.name}</p>
              <p className="truncate text-xs text-muted-foreground">{service.detail}</p>
            </div>
            <span className="inline-flex shrink-0 items-center gap-1.5 text-xs font-medium text-emerald-300">
              <CheckCircle2 className="size-3.5" aria-hidden="true" />
              Operational
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
