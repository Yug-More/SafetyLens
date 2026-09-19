"use client";

import { useCallback } from "react";
import {
  Activity,
  Camera,
  Clock3,
  HeartPulse,
} from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { MetricCard } from "@/components/MetricCard";
import { CameraMonitor } from "@/components/CameraMonitor";
import { IncidentCard } from "@/components/IncidentCard";
import { IncidentTimeline } from "@/components/IncidentTimeline";
import { SystemStatus } from "@/components/SystemStatus";
import { ActivityFeed } from "@/components/ActivityFeed";
import { LiveClock } from "@/components/LiveClock";
import {
  ConnectionBanner,
  MetricSkeleton,
  PanelSkeleton,
} from "@/components/ConnectionBanner";
import { EmptyState } from "@/components/EmptyState";
import { useApiResource } from "@/hooks/useApiResource";
import {
  fetchCameras,
  fetchDashboardActivity,
  fetchDashboardSummary,
  fetchIncidents,
  fetchSystemStatus,
} from "@/lib/api";
import {
  mapActivity,
  mapCamera,
  mapFacilityInfo,
  mapIncident,
  mapSystemService,
} from "@/lib/api/mappers";
import {
  getFallbackActivity,
  getFallbackCameras,
  getFallbackFacility,
  getFallbackIncidents,
  getFallbackServices,
} from "@/data/fallback";

export default function OverviewPage() {
  const loadOverview = useCallback(async () => {
    const [summary, camerasRes, incidentsRes, activityRes, systemRes] =
      await Promise.all([
        fetchDashboardSummary(),
        fetchCameras({ limit: 12 }),
        fetchIncidents({ limit: 20 }),
        fetchDashboardActivity(10),
        fetchSystemStatus(),
      ]);

    return {
      facility: mapFacilityInfo(summary),
      cameras: camerasRes.data.map(mapCamera),
      incidents: incidentsRes.data.map(mapIncident),
      activity: activityRes.data.map(mapActivity),
      services: systemRes.services.map(mapSystemService),
      monitoringActive: summary.monitoring_active,
    };
  }, []);

  const fallbackOverview = useCallback(
    () => ({
      facility: getFallbackFacility(),
      cameras: getFallbackCameras(),
      incidents: getFallbackIncidents(),
      activity: getFallbackActivity(),
      services: getFallbackServices(),
      monitoringActive: true,
    }),
    []
  );

  const { data, error, source, isLoading, reload } = useApiResource({
    loader: loadOverview,
    fallback: fallbackOverview,
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader
          title="Safety Operations"
          subtitle="Real-time visibility across Redwood Distribution Center"
        />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricSkeleton />
          <MetricSkeleton />
          <MetricSkeleton />
          <MetricSkeleton />
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <PanelSkeleton className="min-h-72" />
          <PanelSkeleton className="min-h-72" />
        </div>
      </div>
    );
  }

  if (source === "error" || !data) {
    return (
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader
          title="Safety Operations"
          subtitle="Real-time visibility across Redwood Distribution Center"
        />
        <ConnectionBanner mode="error" message={error} onRetry={reload} />
        <EmptyState
          title="API connection required"
          description="Start the SafetyLens backend or enable NEXT_PUBLIC_DEMO_FALLBACK=true."
          actionLabel="Retry"
          onAction={reload}
        />
      </div>
    );
  }

  const primaryCamera =
    data.cameras.find((camera) => camera.name === "Camera 04") ??
    data.cameras[0];
  const activeIncident =
    data.incidents.find((incident) => incident.status === "awaiting_review") ??
    data.incidents[0];

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <ConnectionBanner
        mode={source === "fallback" ? "fallback" : "api"}
        message={error}
        onRetry={reload}
      />

      <PageHeader
        title="Safety Operations"
        subtitle={`Real-time visibility across ${data.facility.name}`}
        status={
          <span className="inline-flex items-center gap-1.5 rounded-md border border-success/30 bg-success/10 px-2.5 py-1 text-xs font-medium text-emerald-300">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            {data.monitoringActive ? "Monitoring Active" : "Monitoring Paused"}
          </span>
        }
        actions={
          <LiveClock className="rounded-md border border-border bg-panel px-3 py-2 text-xs text-muted-foreground" />
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Active Cameras"
          value={data.facility.activeCameras}
          detail="All camera feeds connected"
          icon={Camera}
          trendLabel={`${data.facility.activeCameras} / ${data.facility.totalCameras} online`}
          trendTone="positive"
        />
        <MetricCard
          title="Open Incidents"
          value={data.facility.openIncidents}
          detail="One incident awaiting review"
          icon={Activity}
          trendLabel="Requires supervisor attention"
          trendTone="attention"
        />
        <MetricCard
          title="Average Response Time"
          value={data.facility.averageResponseTime}
          detail={data.facility.responseTimeTrend}
          icon={Clock3}
          trendLabel="Improving week over week"
          trendTone="positive"
        />
        <MetricCard
          title="System Health"
          value={data.facility.systemHealth}
          detail={data.facility.systemHealthDetail}
          icon={HeartPulse}
          trendLabel={source === "fallback" ? "Demo Data" : "Live API"}
          trendTone="neutral"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
        {primaryCamera ? <CameraMonitor camera={primaryCamera} /> : null}
        {activeIncident ? <IncidentCard incident={activeIncident} /> : null}
      </section>

      <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        <IncidentTimeline incidents={data.incidents} className="xl:col-span-1" />
        <SystemStatus services={data.services} />
        <ActivityFeed events={data.activity} />
      </section>
    </div>
  );
}
