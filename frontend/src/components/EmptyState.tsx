import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-panel/60 px-6 py-12 text-center",
        className
      )}
    >
      <div className="mb-4 rounded-full border border-border bg-secondary p-3 text-muted-foreground">
        <Icon className="size-5" aria-hidden="true" />
      </div>
      <h3 className="text-base font-medium text-foreground">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">{description}</p>
      {actionLabel && onAction ? (
        <Button className="mt-5" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
