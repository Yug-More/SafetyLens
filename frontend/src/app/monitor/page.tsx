"use client";

import { toast } from "sonner";
import { Upload } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { CameraMonitor, CameraCard } from "@/components/CameraMonitor";
import { Button } from "@/components/ui/button";
import { cameras, facilityInfo } from "@/data/mock";

export default function MonitorPage() {
  const [primary, ...secondary] = cameras;

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <PageHeader
        title="Live Monitor"
        subtitle="Facility camera coverage for Redwood Distribution Center"
        status={
          <span className="inline-flex items-center gap-1.5 rounded-md border border-success/30 bg-success/10 px-2.5 py-1 text-xs font-medium text-emerald-300">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            {facilityInfo.activeCameras} cameras connected
          </span>
        }
        actions={
          <Button
            variant="outline"
            onClick={() =>
              toast.message("Video analysis will be connected in Stage 2.")
            }
          >
            <Upload data-icon="inline-start" />
            Upload Demo Video
          </Button>
        }
      />

      <div className="grid gap-4 rounded-xl border border-border bg-panel p-4 text-sm sm:grid-cols-3">
        <div>
          <p className="text-muted-foreground">Facility</p>
          <p className="mt-1 font-medium text-foreground">{facilityInfo.name}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Primary location</p>
          <p className="mt-1 font-medium text-foreground">{primary.location}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Connection state</p>
          <p className="mt-1 font-medium text-emerald-300">All feeds online</p>
        </div>
      </div>

      <CameraMonitor camera={primary} size="large" showActions={false} />

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground">
            Additional Cameras
          </h2>
          <p className="text-xs text-muted-foreground">Demo Environment</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {secondary.map((camera) => (
            <CameraCard key={camera.id} camera={camera} />
          ))}
        </div>
      </section>
    </div>
  );
}
