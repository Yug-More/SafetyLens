"use client";

import { Suspense, useCallback, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Upload } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { CameraMonitor, CameraCard } from "@/components/CameraMonitor";
import { VideoUploadDialog } from "@/components/VideoUploadDialog";
import { VideoAnalysisWorkspace } from "@/components/VideoAnalysisWorkspace";
import { DetectorHandoffPanel } from "@/components/DetectorHandoffPanel";
import { GuidedDemoPanel } from "@/components/GuidedDemoPanel";
import { Button } from "@/components/ui/button";
import {
  ConnectionBanner,
  PanelSkeleton,
} from "@/components/ConnectionBanner";
import { EmptyState } from "@/components/EmptyState";
import { useApiResource } from "@/hooks/useApiResource";
import {
  fetchCameras,
  fetchDashboardSummary,
  fetchVideos,
} from "@/lib/api";
import {
  formatRelativeTime,
  mapCamera,
  mapFacilityInfo,
  mapVideoAsset,
} from "@/lib/api/mappers";
import { getFallbackCameras, getFallbackFacility } from "@/data/fallback";
import { getApiBaseUrl } from "@/lib/api/client";
import type { ApiVideoUploadResponse } from "@/lib/api/types";
import type { VideoAsset } from "@/types/video";

function MonitorPageContent() {
  const searchParams = useSearchParams();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [localUpload, setLocalUpload] = useState<ApiVideoUploadResponse | null>(null);
  const [selectedVideoUrl, setSelectedVideoUrl] = useState<string | null>(null);

  const queryUpload = useMemo<ApiVideoUploadResponse | null>(() => {
    const asset = searchParams.get("asset");
    const job = searchParams.get("job");
    if (!asset || !job) return null;
    return {
      asset_code: asset,
      job_code: job,
      status: "uploaded",
      original_filename: "",
      location: "Loading Zone B",
      created_at: new Date(0).toISOString(),
    };
  }, [searchParams]);

  const activeUpload = localUpload ?? queryUpload;

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

  const loadLibrary = useCallback(async () => {
    const response = await fetchVideos({ limit: 20 });
    return response.data.map(mapVideoAsset);
  }, []);

  const emptyLibrary = useCallback(() => [] as VideoAsset[], []);

  const {
    data: library,
    error: libraryError,
    source: librarySource,
    isLoading: libraryLoading,
    reload: reloadLibrary,
  } = useApiResource({
    loader: loadLibrary,
    fallback: emptyLibrary,
    allowFallback: false,
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
          description="Connect to the API to load live monitor cards and upload videos."
          actionLabel="Retry"
          onAction={reload}
        />
      </div>
    );
  }

  const primary =
    data.cameras.find((camera) => camera.name === "Camera 04") ?? data.cameras[0];
  const secondary = data.cameras
    .filter((camera) => camera.id !== primary?.id)
    .slice(0, 3);
  const videos = library ?? [];

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
            onClick={() => {
              if (source === "fallback") {
                return;
              }
              setUploadOpen(true);
            }}
          >
            <Upload data-icon="inline-start" />
            Upload Demo Video
          </Button>
        }
      />

      <GuidedDemoPanel />

      <DetectorHandoffPanel
        onOpenAsset={(assetCode, jobCode) => {
          setLocalUpload({
            asset_code: assetCode,
            job_code: jobCode ?? "JOB-PENDING",
            status: "uploaded",
            original_filename: "detector-clip.mp4",
            location: "Loading Zone B",
            created_at: new Date().toISOString(),
          });
          setSelectedVideoUrl(null);
          reloadLibrary();
        }}
      />

      <div className="grid gap-4 rounded-xl border border-border bg-panel p-4 text-sm sm:grid-cols-3">
        <div>
          <p className="text-muted-foreground">Facility</p>
          <p className="mt-1 font-medium text-foreground">{data.facility.name}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Primary location</p>
          <p className="mt-1 font-medium text-foreground">{primary?.location ?? "—"}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Connection state</p>
          <p className="mt-1 font-medium text-emerald-300">All feeds online</p>
        </div>
      </div>

      {primary ? (
        <CameraMonitor
          camera={primary}
          size="large"
          showActions={false}
          videoUrl={selectedVideoUrl}
          recordedLabel={Boolean(selectedVideoUrl)}
        />
      ) : null}

      {activeUpload ? (
        <VideoAnalysisWorkspace
          assetCode={activeUpload.asset_code}
          jobCode={activeUpload.job_code}
          onReady={(video) => {
            setSelectedVideoUrl(video.contentUrl);
            reloadLibrary();
          }}
        />
      ) : null}

      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <div className="mb-3">
          <h2 className="text-base font-semibold text-foreground">Video Library</h2>
          <p className="text-sm text-muted-foreground">
            Uploaded recordings prepared for Stage 4 AI analysis
          </p>
        </div>

        {libraryLoading ? <PanelSkeleton className="min-h-32" /> : null}

        {!libraryLoading && librarySource === "error" ? (
          <EmptyState
            title="Video library unavailable"
            description={
              libraryError ??
              `Unable to load videos from ${getApiBaseUrl()}. Uploads require the live API.`
            }
            actionLabel="Retry"
            onAction={reloadLibrary}
          />
        ) : null}

        {!libraryLoading && librarySource !== "error" && videos.length === 0 ? (
          <EmptyState
            title="No uploaded videos yet"
            description="Upload a short MP4, MOV, or WebM clip to extract metadata and frames."
            actionLabel="Upload Demo Video"
            onAction={() => setUploadOpen(true)}
          />
        ) : null}

        {!libraryLoading && videos.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-border text-xs tracking-wide text-muted-foreground uppercase">
                <tr>
                  <th className="px-3 py-2 font-medium">Filename</th>
                  <th className="px-3 py-2 font-medium">Location</th>
                  <th className="px-3 py-2 font-medium">Camera</th>
                  <th className="px-3 py-2 font-medium">Duration</th>
                  <th className="px-3 py-2 font-medium">Resolution</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Uploaded</th>
                  <th className="px-3 py-2 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {videos.map((video) => (
                  <tr key={video.id} className="border-b border-border/70 last:border-0">
                    <td className="px-3 py-2">
                      <p className="font-medium text-foreground">{video.originalFilename}</p>
                      <p className="font-mono text-[11px] text-muted-foreground">
                        {video.assetCode}
                      </p>
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">{video.location}</td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {video.cameraName ?? "—"}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {video.durationSeconds != null
                        ? `${video.durationSeconds.toFixed(1)}s`
                        : "—"}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {video.width && video.height
                        ? `${video.width}×${video.height}`
                        : "—"}
                    </td>
                    <td className="px-3 py-2 capitalize text-muted-foreground">
                      {video.status}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {formatRelativeTime(video.createdAt)}
                    </td>
                    <td className="px-3 py-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setSelectedVideoUrl(video.contentUrl);
                          if (video.latestJobCode) {
                            setLocalUpload({
                              asset_code: video.assetCode,
                              job_code: video.latestJobCode,
                              status: video.status,
                              original_filename: video.originalFilename,
                              location: video.location,
                              created_at: video.createdAt,
                            });
                          }
                        }}
                      >
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-foreground">Additional Cameras</h2>
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

      <VideoUploadDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        cameras={data.cameras}
        defaultCameraId={primary?.id ?? "cam-04"}
        defaultLocation={primary?.location ?? "Loading Zone B"}
        onUploaded={(response) => {
          setLocalUpload(response);
          setSelectedVideoUrl(null);
          reloadLibrary();
        }}
      />
    </div>
  );
}

export default function MonitorPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-7xl p-6 text-sm text-muted-foreground">
          Loading monitor…
        </div>
      }
    >
      <MonitorPageContent />
    </Suspense>
  );
}
