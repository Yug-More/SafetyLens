import { formatDistanceToNowStrict } from "date-fns";
import { resolveMediaUrl } from "@/lib/api/client";
import type {
  ApiActivityEvent,
  ApiCamera,
  ApiDashboardSummary,
  ApiIncident,
  ApiIncidentAnalysis,
  ApiIncidentDetail,
  ApiIncidentStatus,
  ApiProcedure,
  ApiProcessingJob,
  ApiRecommendedAction,
  ApiSeverity,
  ApiSystemService,
  ApiVideoAsset,
  ApiVideoFrame,
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
import type {
  IncidentAnalysisView,
  ProcessingJobView,
  VideoAsset,
  VideoFrameItem,
} from "@/types/video";

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
    section: `${procedure.procedure_code} · v${procedure.version}`,
    category: procedure.category,
    description: `${procedure.source_name}${
      procedure.is_sample ? " · sample company procedure" : ""
    }`,
    steps: procedure.steps.length > 0 ? procedure.steps : [procedure.content],
    lastUpdated: procedure.updated_at.slice(0, 10),
    documentPages: Math.max(1, procedure.chunk_count ?? Math.ceil(procedure.content.length / 400)),
    procedureCode: procedure.procedure_code,
    version: procedure.version,
    sourceFilename: procedure.source_filename ?? null,
    sourceFormat: procedure.source_format ?? null,
    chunkCount: procedure.chunk_count ?? 0,
    isSample: procedure.is_sample ?? false,
    isActive: procedure.is_active,
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

export function mapVideoAsset(video: ApiVideoAsset): VideoAsset {
  return {
    id: video.id,
    assetCode: video.asset_code,
    originalFilename: video.original_filename,
    mimeType: video.mime_type,
    fileSizeBytes: video.file_size_bytes,
    durationSeconds: video.duration_seconds,
    width: video.width,
    height: video.height,
    fps: video.fps,
    frameCount: video.frame_count,
    cameraId: video.camera_id,
    cameraName: video.camera_name,
    location: video.location,
    status: video.status,
    createdAt: video.created_at,
    contentUrl: resolveMediaUrl(video.content_url),
    latestJobCode: video.latest_job_code,
    latestJobStatus: video.latest_job_status,
  };
}

export function mapVideoFrame(frame: ApiVideoFrame): VideoFrameItem {
  return {
    id: frame.id,
    frameCode: frame.frame_code,
    frameNumber: frame.frame_number,
    timestampSeconds: frame.timestamp_seconds,
    width: frame.width,
    height: frame.height,
    contentUrl: resolveMediaUrl(frame.content_url),
  };
}

export function mapProcessingJob(job: ApiProcessingJob): ProcessingJobView {
  return {
    id: job.id,
    jobCode: job.job_code,
    videoAssetCode: job.video_asset_code,
    status: job.status,
    progress: job.progress,
    currentStep: job.current_step,
    errorCode: job.error_code,
    errorMessage: job.error_message,
  };
}

export function mapIncidentAnalysis(
  analysis: ApiIncidentAnalysis
): IncidentAnalysisView {
  return {
    id: analysis.id,
    analysisCode: analysis.analysis_code,
    videoAssetCode: analysis.video_asset_code,
    status: analysis.status,
    providerName: analysis.provider_name,
    isDemo: analysis.is_demo,
    isSimulated: analysis.is_simulated,
    providerLabel:
      analysis.provider_label ??
      (analysis.is_demo ? "Demo AI (simulated)" : analysis.provider_name),
    incidentDetected: analysis.incident_detected,
    incidentType: analysis.incident_type,
    summary: analysis.summary,
    detailedAnalysis: analysis.detailed_analysis,
    severity: analysis.severity,
    confidence: analysis.confidence,
    recommendedActions: analysis.recommended_actions ?? [],
    limitations: analysis.limitations ?? [],
    inconclusive: analysis.inconclusive,
    errorCode: analysis.error_code,
    errorMessage: analysis.error_message,
    evidence: (analysis.evidence ?? []).map((item) => ({
      id: item.id,
      frameId: item.frame_id,
      frameCode: item.frame_code,
      timestampSeconds: item.timestamp_seconds,
      observation: item.observation,
      relevance: item.relevance,
      contentUrl: resolveMediaUrl(item.content_url),
    })),
    review: analysis.review
      ? {
          id: analysis.review.id,
          decision: analysis.review.decision,
          reviewerName: analysis.review.reviewer_name,
          notes: analysis.review.notes,
          reviewedAt: analysis.review.reviewed_at,
        }
      : null,
    humanApprovalRequired: analysis.human_approval_required,
  };
}
