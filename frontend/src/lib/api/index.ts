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
  ApiPlanApproval,
  ApiActionExecution,
  ApiExecutePlanResponse,
  ApiAuditEvent,
  ApiIncidentReport,
  ApiDetectorEvent,
  ApiDemoResetResponse,
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

export function approveResponsePlan(
  planIdentifier: string,
  body: {
    selectedActionIds: string[];
    reviewerName?: string;
    notes?: string;
    incidentIdentifier?: string;
    confirmed: boolean;
  }
) {
  return apiPostJson<ApiPlanApproval>(`/api/response-plans/${planIdentifier}/approve`, {
    selected_action_ids: body.selectedActionIds,
    reviewer_name: body.reviewerName ?? "demo-reviewer",
    notes: body.notes ?? null,
    incident_identifier: body.incidentIdentifier ?? "INC-2026-0042",
    confirmed: body.confirmed,
  });
}

export function rejectResponsePlan(
  planIdentifier: string,
  body: { reviewerName?: string; reason?: string; notes?: string }
) {
  return apiPostJson<ApiPlanApproval>(`/api/response-plans/${planIdentifier}/reject`, {
    reviewer_name: body.reviewerName ?? "demo-reviewer",
    reason: body.reason ?? null,
    notes: body.notes ?? null,
  });
}

export function executeResponsePlan(planIdentifier: string) {
  return apiPostJson<ApiExecutePlanResponse>(
    `/api/response-plans/${planIdentifier}/execute`,
    { confirmed: true }
  );
}

export function fetchPlanExecutions(planIdentifier: string) {
  return apiGetCollection<ApiActionExecution>(
    `/api/response-plans/${planIdentifier}/executions`
  );
}

export function retryExecution(executionIdentifier: string) {
  return apiPostJson<ApiActionExecution>(
    `/api/executions/${executionIdentifier}/retry`
  );
}

export function fetchIncidentAudit(incidentIdentifier: string) {
  return apiGetCollection<ApiAuditEvent>(
    `/api/incidents/${incidentIdentifier}/audit`
  );
}

export function generateIncidentReport(
  incidentIdentifier: string,
  planIdentifier?: string,
  forceRegenerate = false
) {
  return apiPostJson<ApiIncidentReport>(
    `/api/incidents/${incidentIdentifier}/reports`,
    {
      plan_identifier: planIdentifier ?? null,
      force_regenerate: forceRegenerate,
    }
  );
}

export function fetchIncidentReports(incidentIdentifier: string) {
  return apiGetCollection<ApiIncidentReport>(
    `/api/incidents/${incidentIdentifier}/reports`
  );
}

export function fetchReport(reportIdentifier: string) {
  return apiGetItem<ApiIncidentReport>(`/api/reports/${reportIdentifier}`);
}

export function getReportDownloadUrl(reportIdentifier: string) {
  const base = process.env.NEXT_PUBLIC_API_URL?.trim() || "http://localhost:8000";
  return `${base.replace(/\/$/, "")}/api/reports/${reportIdentifier}/download`;
}

export function fetchSystemStatus() {
  return apiGetItem<ApiSystemStatus>("/api/system/status");
}

export function fetchDemoInfo() {
  return apiGetItem<ApiDemoInfo>("/api/demo/info");
}

export function resetDemoState(confirmed = true) {
  return apiPostJson<ApiDemoResetResponse>("/api/demo/reset", {
    confirmed,
    preserve_seed_incidents: true,
  });
}

export function fetchDetectorEvents(limit = 20) {
  return apiGetCollection<ApiDetectorEvent>("/api/detector/events", { limit });
}

export function fetchDetectorEvent(eventId: string) {
  return apiGetItem<ApiDetectorEvent>(`/api/detector/events/${eventId}`);
}

export function retryDetectorEvent(eventId: string) {
  return apiPostJson<ApiDetectorEvent>(`/api/detector/events/${eventId}/retry`);
}

export function ingestDetectorEvent(request: {
  event: Record<string, unknown>;
  clip?: File;
  location?: string;
  autoAnalyze?: boolean;
  incidentIdentifier?: string;
}) {
  const formData = new FormData();
  formData.append("event_json", JSON.stringify(request.event));
  formData.append("location", request.location ?? "Loading Zone B");
  formData.append("auto_analyze", String(request.autoAnalyze ?? true));
  formData.append(
    "incident_identifier",
    request.incidentIdentifier ?? "INC-2026-0042"
  );
  if (request.clip) {
    formData.append("clip", request.clip);
  }
  return apiPostMultipart<ApiDetectorEvent>("/api/detector/events", formData);
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
