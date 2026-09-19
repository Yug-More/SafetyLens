import { apiGetCollection, apiGetItem } from "@/lib/api/client";
import type {
  ApiActivityEvent,
  ApiCamera,
  ApiDashboardSummary,
  ApiDemoInfo,
  ApiHealth,
  ApiIncident,
  ApiIncidentDetail,
  ApiIncidentStatus,
  ApiProcedure,
  ApiSeverity,
  ApiSystemStatus,
} from "@/lib/api/types";

export function fetchHealth() {
  return apiGetItem<ApiHealth>("/api/health");
}

export function fetchDashboardSummary() {
  return apiGetItem<ApiDashboardSummary>("/api/dashboard/summary");
}

export function fetchDashboardActivity(limit = 20) {
  return apiGetCollection<ApiActivityEvent>("/api/dashboard/activity", { limit });
}

export function fetchCameras(params?: {
  status?: string;
  location?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  return apiGetCollection<ApiCamera>("/api/cameras", params);
}

export function fetchCamera(cameraId: string) {
  return apiGetItem<ApiCamera>(`/api/cameras/${cameraId}`);
}

export function fetchIncidents(params?: {
  severity?: ApiSeverity | string;
  status?: ApiIncidentStatus | string;
  camera_id?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  return apiGetCollection<ApiIncident>("/api/incidents", params);
}

export function fetchIncidentDetail(identifier: string) {
  return apiGetItem<ApiIncidentDetail>(`/api/incidents/${identifier}`);
}

export function fetchProcedures(params?: {
  search?: string;
  category?: string;
  active?: boolean;
  limit?: number;
  offset?: number;
}) {
  return apiGetCollection<ApiProcedure>("/api/procedures", params);
}

export function fetchProcedure(identifier: string) {
  return apiGetItem<ApiProcedure>(`/api/procedures/${identifier}`);
}

export function fetchSystemStatus() {
  return apiGetItem<ApiSystemStatus>("/api/system/status");
}

export function fetchDemoInfo() {
  return apiGetItem<ApiDemoInfo>("/api/demo/info");
}
