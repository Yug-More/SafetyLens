"use client";

import { Suspense, useCallback, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertTriangle, Bell, Upload, X } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import {
  CameraCard,
  DEFAULT_UPLOAD_CAMERA_ID,
  DEFAULT_UPLOAD_LOCATION,
  MONITOR_CAMERA_SLOTS,
  resolveMonitorCamera,
  type CameraOperationalState,
} from "@/components/CameraMonitor";
import { VideoUploadDialog } from "@/components/VideoUploadDialog";
import {
  VideoAnalysisWorkspace,
  type VideoWorkspaceState,
} from "@/components/VideoAnalysisWorkspace";
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
  dismissOperatorNotification,
  fetchCameras,
  fetchDashboardSummary,
  fetchOperatorNotifications,
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
import { buildResponseHref } from "@/lib/incident-context";
import type { ApiOperatorNotification, ApiVideoUploadResponse } from "@/lib/api/types";
import type { VideoAsset } from "@/types/video";

function OperatorNotificationAlert({
  notification,
  onDismiss,
}: {
  notification: ApiOperatorNotification;
  onDismiss?: () => void;
}) {
  const reviewHref = buildResponseHref({
    analysis_id: notification.analysis_code ?? notification.analysis_id,
    video_id: notification.video_code,
    camera_id: notification.camera_id,
  });

  return (
    <div
      className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-red-500/50 bg-red-500/10 px-4 py-3 shadow-sm"
      role="alert"
    >
      <div className="flex min-w-0 items-start gap-3">
        <div className="mt-0.5 rounded-md border border-red-500/40 bg-red-500/15 p-2 text-red-200">
          <Bell className="size-4" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-red-100">{notification.title}</p>
          <p className="mt-1 text-xs text-red-200/90">{notification.message}</p>
          <p className="mt-1 text-[11px] text-red-200/70">
            {notification.camera_name ?? "Unknown camera"} · {notification.location}
            {notification.severity ? ` · ${notification.severity} severity` : ""}
            {" · "}
            {formatRelativeTime(notification.detected_at)}
          </p>
        </div>
      </div>
      <div className="flex shrink-0 flex-wrap items-center gap-2">
        <Button size="sm" render={<Link href={reviewHref} />}>
          Review Incident
        </Button>
        {onDismiss ? (
          <Button size="sm" variant="ghost" onClick={onDismiss} aria-label="Dismiss alert">
            <X className="size-4" />
          </Button>
        ) : null}
      </div>
    </div>
  );
}

function MonitorPageContent() {
  const searchParams = useSearchParams();
  const workspaceRef = useRef<HTMLDivElement>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [localUpload, setLocalUpload] = useState<ApiVideoUploadResponse | null>(null);
  const [selectedVideoUrl, setSelectedVideoUrl] = useState<string | null>(null);
  const [activeCameraId, setActiveCameraId] = useState(DEFAULT_UPLOAD_CAMERA_ID);
  const [focusedCameraId, setFocusedCameraId] = useState<string | null>(null);
  const [workspaceState, setWorkspaceState] = useState<VideoWorkspaceState | null>(null);

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

  const loadNotifications = useCallback(async () => {
    const response = await fetchOperatorNotifications(false);
    return response.data;
  }, []);

  const emptyNotifications = useCallback(() => [] as ApiOperatorNotification[], []);

  const {
    data: notifications,
    source: notificationsSource,
    reload: reloadNotifications,
  } = useApiResource({
    loader: loadNotifications,
    fallback: emptyNotifications,
    allowFallback: false,
  });

  const videos = useMemo(() => library ?? [], [library]);

  const queryUpload = useMemo<ApiVideoUploadResponse | null>(() => {
    const asset = searchParams.get("asset");
    const job = searchParams.get("job");
    if (!asset || !job) return null;
    const fromLibrary = videos.find((video) => video.assetCode === asset);
    const defaultCam = data?.cameras.find((camera) => camera.id === DEFAULT_UPLOAD_CAMERA_ID);
    return {
      asset_code: asset,
      job_code: job,
      status: "uploaded",
      original_filename: fromLibrary?.originalFilename ?? "",
      location: fromLibrary?.location ?? defaultCam?.location ?? DEFAULT_UPLOAD_LOCATION,
      created_at: fromLibrary?.createdAt ?? new Date(0).toISOString(),
    };
  }, [searchParams, videos, data?.cameras]);

  const activeUpload = localUpload ?? queryUpload;

  const uploadCamera = useMemo(() => {
    if (!data) return null;
    return (
      data.cameras.find((camera) => camera.id === DEFAULT_UPLOAD_CAMERA_ID) ??
      resolveMonitorCamera(
        MONITOR_CAMERA_SLOTS.find((slot) => slot.id === DEFAULT_UPLOAD_CAMERA_ID)!,
        data.cameras
      )
    );
  }, [data]);

  const unreadNotifications = useMemo(
    () => (notifications ?? []).filter((item) => !item.dismissed),
    [notifications]
  );

  const topNotification = unreadNotifications[0] ?? null;

  const monitorCameras = useMemo(() => {
    if (!data) return [];
    return MONITOR_CAMERA_SLOTS.map((slot) => ({
      slot,
      camera: resolveMonitorCamera(slot, data.cameras),
    }));
  }, [data]);

  function resolveOperationalState(cameraId: string): CameraOperationalState {
    if (cameraId !== activeCameraId || !activeUpload) {
      const camera = monitorCameras.find((item) => item.slot.id === cameraId)?.camera;
      if (camera?.status === "offline") return "offline";
      if (camera?.status === "degraded") return "warning";
      return "monitoring";
    }
    if (workspaceState?.incidentDetected) return "incident";
    if (workspaceState?.analyzing) return "analyzing";
    if (workspaceState?.processing) return "processing";
    return "monitoring";
  }

  function openUploadForCamera(cameraId: string) {
    setActiveCameraId(cameraId);
    setFocusedCameraId(cameraId);
    if (source !== "fallback") {
      setUploadOpen(true);
    }
  }

  function handleUploaded(response: ApiVideoUploadResponse) {
    setLocalUpload(response);
    setSelectedVideoUrl(null);
    setActiveCameraId(DEFAULT_UPLOAD_CAMERA_ID);
    setFocusedCameraId(DEFAULT_UPLOAD_CAMERA_ID);
    reloadLibrary();
  }

  function handleOpenAsset(assetCode: string, jobCode: string | null) {
    const fromLibrary = videos.find((video) => video.assetCode === assetCode);
    const defaultCam = data?.cameras.find((camera) => camera.id === DEFAULT_UPLOAD_CAMERA_ID);
    setLocalUpload({
      asset_code: assetCode,
      job_code: jobCode ?? "JOB-PENDING",
      status: "uploaded",
      original_filename: fromLibrary?.originalFilename ?? "detector-clip.mp4",
      location: fromLibrary?.location ?? defaultCam?.location ?? DEFAULT_UPLOAD_LOCATION,
      created_at: fromLibrary?.createdAt ?? new Date().toISOString(),
    });
    setSelectedVideoUrl(null);
    setActiveCameraId(fromLibrary?.cameraId ?? DEFAULT_UPLOAD_CAMERA_ID);
    setFocusedCameraId(fromLibrary?.cameraId ?? DEFAULT_UPLOAD_CAMERA_ID);
    reloadLibrary();
  }

  function handleSelectVideo(video: VideoAsset) {
    setSelectedVideoUrl(video.contentUrl);
    const cameraId = video.cameraId ?? DEFAULT_UPLOAD_CAMERA_ID;
    setActiveCameraId(cameraId);
    setFocusedCameraId(cameraId);
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
  }

  function scrollToWorkspace() {
    workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

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

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <ConnectionBanner
        mode={source === "fallback" ? "fallback" : "api"}
        message={error}
        onRetry={reload}
      />

      {topNotification && notificationsSource === "api" ? (
        <OperatorNotificationAlert
          notification={topNotification}
          onDismiss={() => {
            void dismissOperatorNotification(topNotification.id)
              .then(() => reloadNotifications())
              .catch(() => reloadNotifications());
          }}
        />
      ) : null}

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
              setActiveCameraId(DEFAULT_UPLOAD_CAMERA_ID);
              setUploadOpen(true);
            }}
          >
            <Upload data-icon="inline-start" />
            Upload Demo Video
          </Button>
        }
      />

      <div className="rounded-xl border border-border bg-panel/60 px-4 py-3 text-sm text-muted-foreground">
        <p className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-sky-400" aria-hidden="true" />
          <span>
            Lightweight detection monitors every feed. Multimodal AI is invoked only when an
            event requires deeper analysis.
          </span>
        </p>
      </div>

      <GuidedDemoPanel defaultCollapsed />

      <DetectorHandoffPanel onOpenAsset={handleOpenAsset} />

      <div className="grid gap-4 rounded-xl border border-border bg-panel p-4 text-sm sm:grid-cols-3">
        <div>
          <p className="text-muted-foreground">Facility</p>
          <p className="mt-1 font-medium text-foreground">{data.facility.name}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Demo upload camera</p>
          <p className="mt-1 font-medium text-foreground">
            {uploadCamera?.name ?? "Camera 03"} —{" "}
            {uploadCamera?.location ?? DEFAULT_UPLOAD_LOCATION}
          </p>
        </div>
        <div>
          <p className="text-muted-foreground">Connection state</p>
          <p className="mt-1 font-medium text-emerald-300">All feeds online</p>
        </div>
      </div>

      <section>
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-foreground">Operations Grid</h2>
            <p className="text-sm text-muted-foreground">
              Four-camera presentation view — focus a tile to jump to the active pipeline
            </p>
          </div>
          <p className="text-xs text-muted-foreground">
            {source === "fallback" ? "Demo Data" : "Live API"}
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {monitorCameras.map(({ slot, camera }) => {
            const isActive = slot.id === activeCameraId && Boolean(activeUpload);
            const operationalState = resolveOperationalState(slot.id);
            const highlighted = isActive;
            const highlightVariant =
              operationalState === "incident" ? "incident" : "processing";

            return (
              <CameraCard
                key={slot.id}
                camera={camera}
                displayName={slot.name}
                displayLocation={slot.location}
                videoUrl={isActive ? selectedVideoUrl : null}
                highlighted={highlighted}
                highlightVariant={highlightVariant}
                operationalState={operationalState}
                focused={focusedCameraId === slot.id}
                onFocus={() => {
                  setFocusedCameraId(slot.id);
                  if (isActive) {
                    scrollToWorkspace();
                  } else if (slot.id === DEFAULT_UPLOAD_CAMERA_ID) {
                    openUploadForCamera(slot.id);
                  }
                }}
              />
            );
          })}
        </div>
      </section>

      {activeUpload ? (
        <div ref={workspaceRef}>
          <VideoAnalysisWorkspace
            assetCode={activeUpload.asset_code}
            jobCode={activeUpload.job_code}
            onReady={(video) => {
              setSelectedVideoUrl(video.contentUrl);
              if (video.cameraId) {
                setActiveCameraId(video.cameraId);
              }
              reloadLibrary();
              void reloadNotifications();
            }}
            onStateChange={setWorkspaceState}
          />
        </div>
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
                        onClick={() => handleSelectVideo(video)}
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

      <VideoUploadDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        cameras={data.cameras}
        defaultCameraId={DEFAULT_UPLOAD_CAMERA_ID}
        defaultLocation={uploadCamera?.location ?? DEFAULT_UPLOAD_LOCATION}
        onUploaded={handleUploaded}
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
