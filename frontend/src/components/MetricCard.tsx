import type { LucideIcon } from "lucide-react";
import { cn } from "cn";

interface MetricCardProps {
  title: string;
  value: string | number;
  detail: string;
  icon: LucideIcon;
  trendLabel?: string;
  trendTone?: "positive" | "neutral" | "attention";
  className?: string;
}

export function MetricCard({
  title,
  value,
  detail,
  icon: Icon,
  trendLabel,
  trendTone = "neutral",
  className,
}: MetricCardProps) {
  return (
    <article
      className={cn(
        "group rounded-xl border border-border bg-panel p-4 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-border/80 hover:bg-panel-elevated hover:shadow-md",
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-2 text-3xl font-semibold tracking-tight text-foreground">
            {value}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-secondary/70 p-2.5 text-primary transition group-hover:border-primary/30">
          <Icon className="size-4" aria-hidden="true" />
        </div>
      </div>
      <p className="mt-3 text-sm text-muted-foreground">{detail}</p>
      {trendLabel ? (
        <p
          className={cn(
            "mt-2 text-xs font-medium",
            trendTone === "positive" && "text-success",
            trendTone === "attention" && "text-warning",
            trendTone === "neutral" && "text-muted-foreground"
          )}
        >
          {trendLabel}
        </p>
      ) : null}
    </article>
  );
}
