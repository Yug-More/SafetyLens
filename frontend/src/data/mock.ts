import type {
  ActivityEvent,
  Camera,
  FacilityInfo,
  Incident,
  RecommendedAction,
  ReportSummary,
  SafetyProcedure,
  SystemService,
} from "@/types";

export const facilityInfo: FacilityInfo = {
  name: "Redwood Distribution Center",
  operationalStatus: "All Systems Operational",
  currentUser: "Yug More",
  role: "Safety Administrator",
  activeCameras: 12,
  totalCameras: 12,
  openIncidents: 1,
  averageResponseTime: "42 sec",
  responseTimeTrend: "18% faster than last week",
  systemHealth: "99.9%",
  systemHealthDetail: "All services operational",
};

export const cameras: Camera[] = [
  {
    id: "cam-04",
    name: "Camera 04",
    location: "Loading Zone B",
    status: "online",
    monitoringActive: true,
    lastHeartbeat: "2s ago",
  },
  {
    id: "cam-01",
    name: "Camera 01",
    location: "Main Entrance",
    status: "online",
    monitoringActive: true,
    lastHeartbeat: "1s ago",
  },
  {
    id: "cam-07",
    name: "Camera 07",
    location: "Assembly Line 2",
    status: "online",
    monitoringActive: true,
    lastHeartbeat: "3s ago",
  },
  {
    id: "cam-11",
    name: "Camera 11",
    location: "Storage Zone C",
    status: "online",
    monitoringActive: true,
    lastHeartbeat: "2s ago",
  },
];

export const incidents: Incident[] = [
  {
    id: "INC-2026-0042",
    title: "Possible Worker Fall",
    location: "Loading Zone B",
    cameraId: "cam-04",
    cameraName: "Camera 04",
    severity: "high",
    confidence: 94,
    detectedAt: "2026-09-19T17:05:46.000Z",
    relativeTime: "14 seconds ago",
    evidence:
      "The worker experienced a sudden posture change and remained on the floor.",
    status: "awaiting_review",
    procedureId: "proc-fall",
    recommendedActionIds: [
      "action-alert",
      "action-medical",
      "action-machinery",
      "action-footage",
      "action-report",
    ],
  },
  {
    id: "INC-2026-0041",
    title: "Missing Safety Helmet",
    location: "Assembly Line 2",
    cameraId: "cam-07",
    cameraName: "Camera 07",
    severity: "medium",
    confidence: 88,
    detectedAt: "2026-09-19T16:28:00.000Z",
    relativeTime: "38 minutes ago",
    evidence:
      "A worker entered the assembly area without a detectable safety helmet.",
    status: "resolved",
    procedureId: "proc-ppe",
  },
  {
    id: "INC-2026-0040",
    title: "Restricted Area Entry",
    location: "Storage Zone C",
    cameraId: "cam-11",
    cameraName: "Camera 11",
    severity: "medium",
    confidence: 91,
    detectedAt: "2026-09-19T15:06:00.000Z",
    relativeTime: "2 hours ago",
    evidence:
      "An unauthorized person crossed into a marked restricted storage zone.",
    status: "resolved",
    procedureId: "proc-restricted",
  },
  {
    id: "INC-2026-0039",
    title: "Obstructed Emergency Exit",
    location: "North Corridor",
    cameraId: "cam-01",
    cameraName: "Camera 01",
    severity: "low",
    confidence: 82,
    detectedAt: "2026-09-18T14:00:00.000Z",
    relativeTime: "Yesterday",
    evidence:
      "Pallet staging partially blocked the marked emergency exit pathway.",
    status: "closed",
  },
];

export const activeIncident = incidents[0];

export const recommendedActions: RecommendedAction[] = [
  {
    id: "action-alert",
    label: "Alert the floor supervisor",
    completed: false,
    priority: "critical",
  },
  {
    id: "action-medical",
    label: "Request medical assistance",
    completed: false,
    priority: "critical",
  },
  {
    id: "action-machinery",
    label: "Stop nearby machinery",
    completed: false,
    priority: "high",
  },
  {
    id: "action-footage",
    label: "Preserve incident footage",
    completed: false,
    priority: "high",
  },
  {
    id: "action-report",
    label: "Create an incident report",
    completed: false,
    priority: "standard",
  },
];

export const procedures: SafetyProcedure[] = [
  {
    id: "proc-fall",
    title: "Worker Fall and Person-Down Response",
    section: "Section 4.2",
    category: "Emergency Response",
    description:
      "Immediate response protocol for suspected worker falls on the facility floor.",
    steps: [
      "Notify the floor supervisor immediately.",
      "Request medical assistance.",
      "Do not move the worker unless immediate danger exists.",
      "Stop nearby machinery.",
      "Preserve the relevant camera footage.",
      "Record the incident and all actions taken.",
    ],
    lastUpdated: "2026-08-12",
    documentPages: 6,
  },
  {
    id: "proc-fire",
    title: "Fire and Smoke Response",
    section: "Section 2.1",
    category: "Emergency Response",
    description:
      "Facility-wide response steps for visible smoke or confirmed fire events.",
    steps: [
      "Activate the nearest fire alarm.",
      "Evacuate personnel using designated routes.",
      "Contact emergency services.",
      "Account for all staff at muster points.",
      "Preserve camera evidence after evacuation.",
    ],
    lastUpdated: "2026-07-03",
    documentPages: 8,
  },
  {
    id: "proc-ppe",
    title: "PPE Compliance Procedure",
    section: "Section 3.4",
    category: "Compliance",
    description:
      "Required personal protective equipment checks for production and loading areas.",
    steps: [
      "Identify the non-compliant worker and zone.",
      "Issue an immediate PPE reminder.",
      "Pause work if risk remains elevated.",
      "Document the compliance event.",
      "Schedule refresher training if recurring.",
    ],
    lastUpdated: "2026-06-21",
    documentPages: 4,
  },
  {
    id: "proc-restricted",
    title: "Restricted Area Access Procedure",
    section: "Section 5.1",
    category: "Access Control",
    description:
      "Response guidance for unauthorized entry into restricted facility zones.",
    steps: [
      "Confirm the restricted-zone boundary breach.",
      "Notify security and the area supervisor.",
      "Escort unauthorized personnel from the zone.",
      "Inspect for safety or inventory impact.",
      "Log the access event and corrective actions.",
    ],
    lastUpdated: "2026-05-18",
    documentPages: 5,
  },
];

export const systemServices: SystemService[] = [
  {
    id: "svc-cameras",
    name: "Camera Network",
    status: "operational",
    detail: "12 of 12 cameras connected",
  },
  {
    id: "svc-edge",
    name: "Edge Detector",
    status: "operational",
    detail: "Edge detector operational",
  },
  {
    id: "svc-ai",
    name: "AI Verification",
    status: "operational",
    detail: "AI verification operational",
  },
  {
    id: "svc-procedures",
    name: "Procedure Database",
    status: "operational",
    detail: "Procedure database synchronized",
  },
  {
    id: "svc-notifications",
    name: "Notification Service",
    status: "operational",
    detail: "Notification service operational",
  },
];

export const activityEvents: ActivityEvent[] = [
  {
    id: "act-1",
    description: "Worker-fall event detected",
    timestamp: "14 seconds ago",
    status: "warning",
    icon: "alert",
  },
  {
    id: "act-2",
    description: "Evidence clip preserved",
    timestamp: "12 seconds ago",
    status: "success",
    icon: "clip",
  },
  {
    id: "act-3",
    description: "Safety procedure matched",
    timestamp: "10 seconds ago",
    status: "success",
    icon: "procedure",
  },
  {
    id: "act-4",
    description: "Supervisor review requested",
    timestamp: "8 seconds ago",
    status: "pending",
    icon: "review",
  },
  {
    id: "act-5",
    description: "Previous helmet incident resolved",
    timestamp: "38 minutes ago",
    status: "success",
    icon: "resolved",
  },
];

export const reportSummaries: ReportSummary[] = [
  {
    id: "rpt-001",
    title: "Weekly Safety Operations Summary",
    period: "Sep 13 – Sep 19, 2026",
    incidentCount: 4,
    status: "ready",
    generatedAt: "Today, 08:15",
  },
  {
    id: "rpt-002",
    title: "Loading Zone Incident Digest",
    period: "Sep 1 – Sep 19, 2026",
    incidentCount: 7,
    status: "ready",
    generatedAt: "Yesterday, 17:42",
  },
  {
    id: "rpt-003",
    title: "PPE Compliance Trends",
    period: "August 2026",
    incidentCount: 12,
    status: "ready",
    generatedAt: "Sep 1, 09:00",
  },
];

export const severityBreakdown = [
  { name: "High", value: 1, fill: "#ef4444" },
  { name: "Medium", value: 2, fill: "#f59e0b" },
  { name: "Low", value: 1, fill: "#64748b" },
];

export const resolutionBreakdown = [
  { name: "Awaiting Review", value: 1 },
  { name: "Resolved", value: 2 },
  { name: "Closed", value: 1 },
];

export function getProcedureById(id: string): SafetyProcedure | undefined {
  return procedures.find((procedure) => procedure.id === id);
}

export function getIncidentById(id: string): Incident | undefined {
  return incidents.find((incident) => incident.id === id);
}

export function getActionsForIncident(incident: Incident): RecommendedAction[] {
  if (!incident.recommendedActionIds) {
    return [];
  }

  return recommendedActions.filter((action) =>
    incident.recommendedActionIds?.includes(action.id)
  );
}
