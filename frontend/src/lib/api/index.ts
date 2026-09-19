import { apiGetCollection, apiGetItem, apiPostMultipart } from "@/lib/api/client";
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
  ApiProcessingJob,
  ApiSeverity,
  ApiSystemStatus,
  ApiVideoAsset,
  ApiVideoFrame,
  ApiVideoStatus,
  ApiVideoUploadResponse,
  VideoUploadRequest,
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

export function uploadVideo(request: VideoUploadRequest) {
  const formData = new FormData();
  formData.append("file", request.file);
  formData.append("location", request.location);
  if (request.cameraId) {
    formData.append("camera_id", request.cameraId);
  }
  return apiPostMultipart<ApiVideoUploadResponse>("/api/videos/upload", formData);
}

export function fetchVideos(params?: {
  status?: ApiVideoStatus | string;
  camera_id?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  return apiGetCollection<ApiVideoAsset>("/api/videos", params);
}

export function fetchVideo(identifier: string) {
  return apiGetItem<ApiVideoAsset>(`/api/videos/${identifier}`);
}

export function fetchVideoFrames(identifier: string) {
  return apiGetCollection<ApiVideoFrame>(`/api/videos/${identifier}/frames`);
}

export function fetchProcessingJob(identifier: string) {
  return apiGetItem<ApiProcessingJob>(`/api/processing-jobs/${identifier}`);
}
