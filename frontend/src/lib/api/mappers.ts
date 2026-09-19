import { formatDistanceToNowStrict } from "date-fns";
import type {
  ApiActivityEvent,
  ApiCamera,
  ApiDashboardSummary,
  ApiIncident,
  ApiIncidentDetail,
  ApiIncidentStatus,
  ApiProcedure,
  ApiRecommendedAction,
  ApiSeverity,
  ApiSystemService,
} from "@/lib/api/types";
import type {
  ActivityEvent,
  Camera,
  FacilityInfo,
  Incident,
  IncidentSeverity,
  IncidentStatus,
  RecommendedAction,
  SafetyProcedure,
  SystemService,
} from "@/types";

export function formatRelativeTime(iso: string): string {
  try {
    return `${formatDistanceToNowStrict(new Date(iso))} ago`;
  } catch {
    return iso;
  }
}

export function mapSeverity(severity: ApiSeverity): IncidentSeverity {
  if (severity === "critical") return "high";
  return severity;
}

export function mapIncidentStatus(status: ApiIncidentStatus): IncidentStatus {
  switch (status) {
    case "awaiting_review":
    case "detected":
    case "approved":
      return status === "approved" ? "in_progress" : "awaiting_review";
    case "dismissed":
      return "closed";
    case "resolved":
      return "resolved";
    case "closed":
      return "closed";
    default:
      return "awaiting_review";
  }
}

export function mapCamera(camera: ApiCamera): Camera {
  return {
    id: camera.id,
    name: camera.name,
    location: camera.location,
    status:
      camera.status === "warning"
        ? "degraded"
        : camera.status === "offline"
          ? "offline"
          : "online",
    monitoringActive: camera.status === "online",
    lastHeartbeat: formatRelativeTime(camera.last_seen_at),
  };
}

export function mapIncident(incident: ApiIncident): Incident {
  return {
    id: incident.incident_code,
    title: incident.title,
    location: incident.location,
    cameraId: incident.camera_id,
    cameraName: incident.camera_name ?? "Unknown camera",
    severity: mapSeverity(incident.severity),
    confidence: Math.round(incident.confidence * 100),
    detectedAt: incident.detected_at,
    relativeTime: formatRelativeTime(incident.detected_at),
    evidence: incident.evidence_summary,
    status: mapIncidentStatus(incident.status),
    procedureId: incident.matched_procedure_id ?? undefined,
  };
}

export function mapAction(action: ApiRecommendedAction): RecommendedAction {
  return {
    id: action.id,
    label: action.title,
    completed: action.status === "completed" || action.status === "approved",
    priority: action.priority,
  };
}

export function mapProcedure(procedure: ApiProcedure): SafetyProcedure {
  return {
    id: procedure.id,
    title: procedure.title,
    section: `Version ${procedure.version}`,
    category: procedure.category,
    description: `${procedure.source_name} · ${procedure.procedure_code}`,
    steps: procedure.steps.length > 0 ? procedure.steps : [procedure.content],
    lastUpdated: procedure.updated_at.slice(0, 10),
    documentPages: Math.max(1, Math.ceil(procedure.content.length / 400)),
  };
}

export function mapActivity(event: ApiActivityEvent): ActivityEvent {
  const icon =
    event.event_type === "detection"
      ? "alert"
      : event.event_type === "evidence"
        ? "clip"
        : event.event_type === "procedure"
          ? "procedure"
          : event.event_type === "review"
            ? "review"
            : event.event_type === "resolution"
              ? "resolved"
              : "system";

  const status =
    event.status === "warning"
      ? "warning"
      : event.status === "pending"
        ? "pending"
        : event.status === "success"
          ? "success"
          : "info";

  return {
    id: event.id,
    description: event.title,
    timestamp: formatRelativeTime(event.occurred_at),
    status,
    icon,
  };
}

export function mapSystemService(service: ApiSystemService): SystemService {
  return {
    id: service.id,
    name: service.name,
    status: service.status,
    detail: service.message,
  };
}

export function mapFacilityInfo(
  summary: ApiDashboardSummary,
  extras?: Partial<FacilityInfo>
): FacilityInfo {
  return {
    name: summary.facility_name,
    operationalStatus:
      summary.system_health_percentage >= 99
        ? "All Systems Operational"
        : "Attention Required",
    currentUser: extras?.currentUser ?? "Yug More",
    role: extras?.role ?? "Safety Administrator",
    activeCameras: summary.active_cameras,
    totalCameras: summary.total_cameras,
    openIncidents: summary.open_incidents,
    averageResponseTime: `${summary.average_response_time_seconds} sec`,
    responseTimeTrend: extras?.responseTimeTrend ?? "18% faster than last week",
    systemHealth: `${summary.system_health_percentage}%`,
    systemHealthDetail:
      extras?.systemHealthDetail ?? "All services operational",
  };
}

export function mapIncidentDetail(detail: ApiIncidentDetail): {
  incident: Incident;
  camera: Camera;
  actions: RecommendedAction[];
  procedure: SafetyProcedure | null;
  evidenceDescriptions: string[];
} {
  return {
    incident: mapIncident({
      ...detail.incident,
      camera_name: detail.camera.name,
    }),
    camera: mapCamera(detail.camera),
    actions: detail.actions.map(mapAction),
    procedure: detail.matched_procedure
      ? mapProcedure(detail.matched_procedure)
      : null,
    evidenceDescriptions: detail.evidence.map((item) => item.description),
  };
}
