/** API contract types matching the FastAPI Stage 2 schemas. */

export type ApiSeverity = "low" | "medium" | "high" | "critical";
export type ApiIncidentStatus =
  | "detected"
  | "awaiting_review"
  | "approved"
  | "dismissed"
  | "resolved"
  | "closed";
export type ApiReviewStatus = "pending" | "approved" | "rejected" | "not_required";
export type ApiCameraStatus = "online" | "offline" | "warning";
export type ApiActionStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "completed"
  | "failed";
export type ApiServiceStatus = "operational" | "degraded" | "offline";
export type ApiActionPriority = "critical" | "high" | "standard";

export interface ApiMeta {
  count: number;
  limit: number;
  offset: number;
}

export interface ApiItemResponse<T> {
  data: T;
}

export interface ApiCollectionResponse<T> {
  data: T[];
  meta: ApiMeta;
}

export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
  };
}

export interface ApiCamera {
  id: string;
  name: string;
  location: string;
  status: ApiCameraStatus;
  stream_status: string;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
}

export interface ApiIncident {
  id: string;
  incident_code: string;
  title: string;
  incident_type: string;
  location: string;
  camera_id: string;
  severity: ApiSeverity;
  confidence: number;
  evidence_summary: string;
  detected_at: string;
  status: ApiIncidentStatus;
  review_status: ApiReviewStatus;
  matched_procedure_id: string | null;
  created_at: string;
  updated_at: string;
  camera_name: string | null;
}

export interface ApiEvidence {
  id: string;
  incident_id: string;
  evidence_type: string;
  description: string;
  timestamp_seconds: number;
  media_url: string | null;
  created_at: string;
}

export interface ApiRecommendedAction {
  id: string;
  incident_id: string;
  title: string;
  description: string;
  priority: ApiActionPriority;
  status: ApiActionStatus;
  requires_approval: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiProcedure {
  id: string;
  procedure_code: string;
  title: string;
  category: string;
  version: string;
  content: string;
  source_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  steps: string[];
  effective_date?: string | null;
  source_filename?: string | null;
  source_format?: string | null;
  chunk_count?: number;
  is_sample?: boolean;
}

export interface ApiProcedureChunk {
  id: string;
  chunk_code: string;
  chunk_order: number;
  section_heading: string | null;
  page_number: number | null;
  content: string;
  procedure_id: string;
  procedure_code: string | null;
  procedure_title: string | null;
  procedure_version: string | null;
}

export interface ApiRetrievalMatch {
  procedure_id: string;
  procedure_code: string;
  procedure_title: string;
  procedure_version: string;
  chunk_id: string;
  chunk_code: string;
  chunk_order: number;
  section_heading: string | null;
  page_number: number | null;
  excerpt: string;
  score: number;
  method: string;
  rank: number;
}

export interface ApiProcedureRetrieval {
  id: string;
  retrieval_code: string;
  analysis_id: string;
  analysis_code: string | null;
  query_text: string;
  method: string;
  status: "completed" | "insufficient" | "failed";
  match_count: number;
  message: string | null;
  matches: ApiRetrievalMatch[];
  created_at: string;
}

export interface ApiPlanCitation {
  id: string;
  chunk_id: string;
  chunk_code: string | null;
  procedure_code: string | null;
  procedure_title: string | null;
  section_heading: string | null;
  page_number: number | null;
  excerpt: string;
}

export interface ApiPlannedAction {
  id: string;
  action_order: number;
  title: string;
  description: string;
  priority: ApiActionPriority;
  responsible_role: string;
  requires_human_approval: boolean;
  is_policy_grounded: boolean;
  citations: ApiPlanCitation[];
}

export interface ApiResponsePlan {
  id: string;
  plan_code: string;
  analysis_id: string;
  analysis_code: string | null;
  retrieval_id: string | null;
  retrieval_code: string | null;
  status: "queued" | "completed" | "insufficient_policy" | "failed";
  summary: string | null;
  rationale: string | null;
  provider_name: string;
  provider_model: string | null;
  is_demo: boolean;
  is_simulated: boolean;
  provider_label: string;
  limitations: string[];
  error_code: string | null;
  error_message: string | null;
  actions: ApiPlannedAction[];
  recommendations_executed: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiProcedureUploadResponse {
  id: string;
  procedure_code: string;
  title: string;
  version: string;
  source_format: string;
  source_filename: string;
  chunk_count: number;
  is_sample: boolean;
  message: string;
}

export interface ProcedureUploadRequest {
  file: File;
  procedureCode: string;
  title: string;
  category: string;
  version: string;
  sourceName?: string;
  isSample?: boolean;
}

export interface ApiIncidentDetail {
  incident: ApiIncident;
  camera: ApiCamera;
  evidence: ApiEvidence[];
  actions: ApiRecommendedAction[];
  matched_procedure: ApiProcedure | null;
}

export interface ApiDashboardSummary {
  active_cameras: number;
  total_cameras: number;
  open_incidents: number;
  average_response_time_seconds: number;
  system_health_percentage: number;
  facility_name: string;
  monitoring_active: boolean;
}

export interface ApiActivityEvent {
  id: string;
  event_type: string;
  title: string;
  description: string;
  incident_id: string | null;
  status: string;
  occurred_at: string;
}

export interface ApiSystemService {
  id: string;
  name: string;
  status: ApiServiceStatus;
  message: string;
  last_checked_at: string;
}

export interface ApiSystemStatus {
  services: ApiSystemService[];
  overall_status: ApiServiceStatus;
  demo_environment: boolean;
}

export interface ApiDemoInfo {
  demo_mode: boolean;
  facility: string;
  scenario: string;
  description: string;
  simulated_capabilities: string[];
  limitations: string[];
}

export interface ApiHealth {
  status: string;
  app_name: string;
  environment: string;
  demo_mode: boolean;
  database_status: string;
  timestamp: string;
}

export type ApiVideoStatus =
  | "uploading"
  | "uploaded"
  | "processing"
  | "ready"
  | "failed";

export type ApiJobStatus = "queued" | "processing" | "completed" | "failed";

export interface ApiVideoAsset {
  id: string;
  asset_code: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  fps: number | null;
  frame_count: number | null;
  camera_id: string | null;
  camera_name: string | null;
  location: string;
  status: ApiVideoStatus;
  created_at: string;
  updated_at: string;
  content_url: string | null;
  latest_job_code: string | null;
  latest_job_status: ApiJobStatus | null;
}

export interface ApiVideoFrame {
  id: string;
  frame_code: string;
  video_asset_id: string;
  frame_number: number;
  timestamp_seconds: number;
  width: number;
  height: number;
  created_at: string;
  content_url: string;
}

export interface ApiProcessingJob {
  id: string;
  job_code: string;
  video_asset_id: string;
  video_asset_code: string | null;
  job_type: string;
  status: ApiJobStatus;
  progress: number;
  current_step: string;
  error_code: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiVideoUploadResponse {
  asset_code: string;
  job_code: string;
  status: ApiVideoStatus;
  original_filename: string;
  location: string;
  created_at: string;
}

export interface VideoUploadRequest {
  file: File;
  location: string;
  cameraId?: string;
}

export type ApiAnalysisStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "needs_review";

export type ApiAnalysisSeverity = "none" | "low" | "medium" | "high" | "critical";

export type ApiReviewDecision =
  | "pending"
  | "confirmed"
  | "rejected"
  | "needs_more_info";

export interface ApiAnalysisEvidence {
  id: string;
  frame_id: string;
  frame_code: string;
  timestamp_seconds: number;
  observation: string;
  relevance: string;
  content_url: string;
}

export interface ApiAnalysisReview {
  id: string;
  decision: ApiReviewDecision;
  reviewer_name: string;
  notes: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiIncidentAnalysis {
  id: string;
  analysis_code: string;
  video_asset_id: string;
  video_asset_code: string | null;
  processing_job_id: string | null;
  processing_job_code: string | null;
  status: ApiAnalysisStatus;
  provider_name: string;
  is_demo: boolean;
  is_simulated: boolean;
  incident_detected: boolean | null;
  incident_type: string | null;
  summary: string | null;
  detailed_analysis: string | null;
  severity: ApiAnalysisSeverity | null;
  confidence: number | null;
  recommended_actions: string[];
  limitations: string[];
  inconclusive: boolean;
  error_code: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  evidence: ApiAnalysisEvidence[];
  review: ApiAnalysisReview | null;
  provider_label: string | null;
  human_approval_required: boolean;
}

export interface ApiAnalyzeVideoResponse {
  analysis_code: string;
  job_code: string;
  status: ApiAnalysisStatus;
  provider_name: string;
  is_demo: boolean;
  is_simulated: boolean;
  message: string;
}

export interface ApiAIProviderInfo {
  provider_name: string;
  is_demo: boolean;
  is_simulated: boolean;
  label: string;
  description: string;
}

export interface AnalysisReviewRequest {
  decision: Exclude<ApiReviewDecision, "pending">;
  reviewerName?: string;
  notes?: string;
}
