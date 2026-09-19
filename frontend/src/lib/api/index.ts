import { apiGetCollection, apiGetItem, apiPostJson, apiPostMultipart } from "@/lib/api/client";
import type {
  ApiActivityEvent,
  ApiAIProviderInfo,
  ApiAnalyzeVideoResponse,
  ApiCamera,
  ApiDashboardSummary,
  ApiDemoInfo,
  ApiHealth,
  ApiIncident,
  ApiIncidentAnalysis,
  ApiIncidentDetail,
  ApiIncidentStatus,
  ApiProcedure,
  ApiProcedureChunk,
  ApiProcedureRetrieval,
  ApiProcedureUploadResponse,
  ApiProcessingJob,
  ApiResponsePlan,
  ApiSeverity,
  ApiSystemStatus,
  ApiVideoAsset,
  ApiVideoFrame,
  ApiVideoStatus,
  ApiVideoUploadResponse,
  AnalysisReviewRequest,
  ProcedureUploadRequest,
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

export function fetchProcedureChunks(identifier: string) {
  return apiGetCollection<ApiProcedureChunk>(`/api/procedures/${identifier}/chunks`);
}

export function uploadProcedure(request: ProcedureUploadRequest) {
  const formData = new FormData();
  formData.append("file", request.file);
  formData.append("procedure_code", request.procedureCode);
  formData.append("title", request.title);
  formData.append("category", request.category);
  formData.append("version", request.version);
  if (request.sourceName) {
    formData.append("source_name", request.sourceName);
  }
  if (request.isSample !== undefined) {
    formData.append("is_sample", String(request.isSample));
  }
  return apiPostMultipart<ApiProcedureUploadResponse>("/api/procedures/upload", formData);
}

export function retrieveProceduresForAnalysis(
  analysisIdentifier: string,
  query?: string
) {
  return apiPostJson<ApiProcedureRetrieval>(
    `/api/analyses/${analysisIdentifier}/retrieve-procedures`,
    query ? { query } : {}
  );
}

export function generateResponsePlan(
  analysisIdentifier: string,
  retrievalId?: string
) {
  return apiPostJson<ApiResponsePlan>(
    `/api/analyses/${analysisIdentifier}/response-plan`,
    retrievalId ? { retrieval_id: retrievalId } : {}
  );
}

export function fetchResponsePlan(identifier: string) {
  return apiGetItem<ApiResponsePlan>(`/api/response-plans/${identifier}`);
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

export function fetchAIProvider() {
  return apiGetItem<ApiAIProviderInfo>("/api/ai/provider");
}

export function startVideoAnalysis(identifier: string) {
  return apiPostJson<ApiAnalyzeVideoResponse>(`/api/videos/${identifier}/analyze`);
}

export function fetchAnalysis(identifier: string) {
  return apiGetItem<ApiIncidentAnalysis>(`/api/analyses/${identifier}`);
}

export function fetchVideoAnalyses(identifier: string) {
  return apiGetCollection<ApiIncidentAnalysis>(`/api/videos/${identifier}/analyses`);
}

export function submitAnalysisReview(
  identifier: string,
  request: AnalysisReviewRequest
) {
  return apiPostJson<ApiIncidentAnalysis>(`/api/analyses/${identifier}/review`, {
    decision: request.decision,
    reviewer_name: request.reviewerName ?? "demo-reviewer",
    notes: request.notes ?? null,
  });
}
