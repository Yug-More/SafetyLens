"use client";

import { useCallback } from "react";
import { toast } from "sonner";
import { Upload } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { CameraMonitor, CameraCard } from "@/components/CameraMonitor";
import { Button } from "@/components/ui/button";
import {
  ConnectionBanner,
  PanelSkeleton,
} from "@/components/ConnectionBanner";
import { EmptyState } from "@/components/EmptyState";
import { useApiResource } from "@/hooks/useApiResource";
import { fetchCameras, fetchDashboardSummary } from "@/lib/api";
import { mapCamera, mapFacilityInfo } from "@/lib/api/mappers";
import { getFallbackCameras, getFallbackFacility } from "@/data/fallback";

export default function MonitorPage() {
  const loader = useCallback(async () => {
    const [summary, camerasRes] = await Promise.all([
      fetchDashboardSummary(),
      fetchCameras({ limit: 12 }),
    ]);
    return {
      facility: mapFacilityInfo(summary),
      cameras: camerasRes.data.map(mapCamera),
    };
  }, []);

  const fallback = useCallback(
    () => ({
      facility: getFallbackFacility(),
      cameras: getFallbackCameras(),
    }),
    []
  );

  const { data, error, source, isLoading, reload } = useApiResource({
    loader,
    fallback,
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader title="Live Monitor" subtitle="Loading camera network…" />
        <PanelSkeleton className="min-h-80" />
      </div>
    );
  }

  if (source === "error" || !data) {
    return (
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader title="Live Monitor" subtitle="Facility camera coverage" />
        <ConnectionBanner mode="error" message={error} onRetry={reload} />
        <EmptyState
          title="No camera data available"
          description="Connect to the API to load live monitor cards."
          actionLabel="Retry"
          onAction={reload}
        />
      </div>
    );
  }

  const primary =
    data.cameras.find((camera) => camera.name === "Camera 04") ??
    data.cameras[0];
  const secondary = data.cameras.filter((camera) => camera.id !== primary?.id).slice(0, 3);

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <ConnectionBanner
        mode={source === "fallback" ? "fallback" : "api"}
        message={error}
        onRetry={reload}
      />

      <PageHeader
        title="Live Monitor"
        subtitle={`Facility camera coverage for ${data.facility.name}`}
        status={
          <span className="inline-flex items-center gap-1.5 rounded-md border border-success/30 bg-success/10 px-2.5 py-1 text-xs font-medium text-emerald-300">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            {data.facility.activeCameras} cameras connected
          </span>
        }
        actions={
          <Button
            variant="outline"
            onClick={() =>
              toast.message("Video analysis will be connected in Stage 3.")
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
          <p className="mt-1 font-medium text-foreground">{data.facility.name}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Primary location</p>
          <p className="mt-1 font-medium text-foreground">
            {primary?.location ?? "—"}
          </p>
        </div>
        <div>
          <p className="text-muted-foreground">Connection state</p>
          <p className="mt-1 font-medium text-emerald-300">All feeds online</p>
        </div>
      </div>

      {primary ? (
        <CameraMonitor camera={primary} size="large" showActions={false} />
      ) : null}

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground">
            Additional Cameras
          </h2>
          <p className="text-xs text-muted-foreground">
            {source === "fallback" ? "Demo Data" : "Live API"}
          </p>
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
