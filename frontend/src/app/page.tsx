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
  activeIncident,
  activityEvents,
  cameras,
  facilityInfo,
  incidents,
  systemServices,
} from "@/data/mock";

export default function OverviewPage() {
  const primaryCamera = cameras[0];

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <PageHeader
        title="Safety Operations"
        subtitle="Real-time visibility across Redwood Distribution Center"
        status={
          <span className="inline-flex items-center gap-1.5 rounded-md border border-success/30 bg-success/10 px-2.5 py-1 text-xs font-medium text-emerald-300">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            Monitoring Active
          </span>
        }
        actions={
          <LiveClock className="rounded-md border border-border bg-panel px-3 py-2 text-xs text-muted-foreground" />
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Active Cameras"
          value={facilityInfo.activeCameras}
          detail="All camera feeds connected"
          icon={Camera}
          trendLabel="12 / 12 online"
          trendTone="positive"
        />
        <MetricCard
          title="Open Incidents"
          value={facilityInfo.openIncidents}
          detail="One incident awaiting review"
          icon={Activity}
          trendLabel="Requires supervisor attention"
          trendTone="attention"
        />
        <MetricCard
          title="Average Response Time"
          value={facilityInfo.averageResponseTime}
          detail={facilityInfo.responseTimeTrend}
          icon={Clock3}
          trendLabel="Improving week over week"
          trendTone="positive"
        />
        <MetricCard
          title="System Health"
          value={facilityInfo.systemHealth}
          detail={facilityInfo.systemHealthDetail}
          icon={HeartPulse}
          trendLabel="Demo Environment"
          trendTone="neutral"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
        <CameraMonitor camera={primaryCamera} />
        <IncidentCard incident={activeIncident} />
      </section>

      <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        <IncidentTimeline incidents={incidents} className="xl:col-span-1" />
        <SystemStatus services={systemServices} />
        <ActivityFeed events={activityEvents} />
      </section>
    </div>
  );
}
