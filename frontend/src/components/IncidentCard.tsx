"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { MapPin, Video, Clock3, Sparkles } from "lucide-react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { ConfirmationDialog } from "@/components/ConfirmationDialog";
import type { Incident } from "@/types";

interface IncidentCardProps {
  incident: Incident;
  className?: string;
}

export function IncidentCard({ incident, className }: IncidentCardProps) {
  const [dismissOpen, setDismissOpen] = useState(false);

  return (
    <>
      <section
        className={cn(
          "rounded-xl border border-destructive/25 bg-gradient-to-br from-red-950/40 via-panel to-panel p-4 shadow-sm ring-1 ring-destructive/10",
          className
        )}
      >
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium tracking-wide text-red-300/90 uppercase">
              Active Incident
            </p>
            <h2 className="mt-1 text-lg font-semibold text-foreground">
              {incident.title}
            </h2>
            <p className="mt-1 font-mono text-xs text-muted-foreground">
              {incident.id}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <SeverityBadge severity={incident.severity} />
            <StatusBadge status={incident.status} />
          </div>
        </div>

        <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div className="flex items-start gap-2">
            <MapPin className="mt-0.5 size-4 text-muted-foreground" aria-hidden="true" />
            <div>
              <dt className="text-muted-foreground">Location</dt>
              <dd className="font-medium text-foreground">{incident.location}</dd>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Video className="mt-0.5 size-4 text-muted-foreground" aria-hidden="true" />
            <div>
              <dt className="text-muted-foreground">Camera</dt>
              <dd className="font-medium text-foreground">{incident.cameraName}</dd>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Clock3 className="mt-0.5 size-4 text-muted-foreground" aria-hidden="true" />
            <div>
              <dt className="text-muted-foreground">Detected</dt>
              <dd className="font-medium text-foreground">{incident.relativeTime}</dd>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <Sparkles className="mt-0.5 size-4 text-muted-foreground" aria-hidden="true" />
            <div className="w-full">
              <dt className="mb-1.5 flex items-center justify-between text-muted-foreground">
                <span>Confidence</span>
                <span className="font-medium text-foreground">{incident.confidence}%</span>
              </dt>
              <div
                className="h-1.5 overflow-hidden rounded-full bg-muted"
                role="progressbar"
                aria-valuenow={incident.confidence}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Confidence ${incident.confidence}%`}
              >
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${incident.confidence}%` }}
                />
              </div>
            </div>
          </div>
        </dl>

        <div className="mt-4 rounded-lg border border-border bg-secondary/40 p-3">
          <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Evidence
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-slate-200">
            {incident.evidence}
          </p>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Button render={<Link href="/response" />}>Review Incident</Button>
          <Button variant="outline" onClick={() => setDismissOpen(true)}>
            Dismiss
          </Button>
        </div>
      </section>

      <ConfirmationDialog
        open={dismissOpen}
        onOpenChange={setDismissOpen}
        title="Dismiss this incident?"
        description="This is a Stage 1 mock interaction. The incident will remain in the demo dataset and will not be permanently deleted."
        confirmLabel="Dismiss for Demo"
        tone="destructive"
        onConfirm={() =>
          toast.message("Incident marked as dismissed in this demo session.")
        }
      />
    </>
  );
}
