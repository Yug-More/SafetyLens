export type IncidentSeverity = "high" | "medium" | "low";

export type IncidentStatus =
  | "awaiting_review"
  | "resolved"
  | "closed"
  | "in_progress";

export type CameraStatus = "online" | "degraded" | "offline";

export type ServiceStatus = "operational" | "degraded" | "offline";

export type ActivityStatus = "success" | "pending" | "info" | "warning";

export interface Camera {
  id: string;
  name: string;
  location: string;
  status: CameraStatus;
  monitoringActive: boolean;
  lastHeartbeat: string;
}

export interface RecommendedAction {
  id: string;
  label: string;
  completed: boolean;
  priority: "critical" | "high" | "standard";
}

export interface SafetyProcedure {
  id: string;
  title: string;
  section: string;
  category: string;
  description: string;
  steps: string[];
  lastUpdated: string;
  documentPages: number;
  procedureCode?: string;
  version?: string;
  sourceFilename?: string | null;
  sourceFormat?: string | null;
  chunkCount?: number;
  isSample?: boolean;
  isActive?: boolean;
}

export interface SystemService {
  id: string;
  name: string;
  status: ServiceStatus;
  detail: string;
}

export interface ActivityEvent {
  id: string;
  description: string;
  timestamp: string;
  status: ActivityStatus;
  icon:
    | "alert"
    | "clip"
    | "procedure"
    | "review"
    | "resolved"
    | "system";
}

export interface Incident {
  id: string;
  title: string;
  location: string;
  cameraId: string;
  cameraName: string;
  severity: IncidentSeverity;
  confidence: number;
  detectedAt: string;
  relativeTime: string;
  evidence: string;
  status: IncidentStatus;
  procedureId?: string;
  recommendedActionIds?: string[];
}

export interface FacilityInfo {
  name: string;
  operationalStatus: string;
  currentUser: string;
  role: string;
  activeCameras: number;
  totalCameras: number;
  openIncidents: number;
  averageResponseTime: string;
  responseTimeTrend: string;
  systemHealth: string;
  systemHealthDetail: string;
}

export interface ReportSummary {
  id: string;
  title: string;
  period: string;
  incidentCount: number;
  status: "ready" | "generating";
  generatedAt: string;
}
