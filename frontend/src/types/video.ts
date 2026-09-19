export type VideoStatus =
  | "uploading"
  | "uploaded"
  | "processing"
  | "ready"
  | "failed";

export type JobStatus = "queued" | "processing" | "completed" | "failed";

export interface VideoAsset {
  id: string;
  assetCode: string;
  originalFilename: string;
  mimeType: string;
  fileSizeBytes: number;
  durationSeconds: number | null;
  width: number | null;
  height: number | null;
  fps: number | null;
  frameCount: number | null;
  cameraId: string | null;
  cameraName: string | null;
  location: string;
  status: VideoStatus;
  createdAt: string;
  contentUrl: string;
  latestJobCode: string | null;
  latestJobStatus: JobStatus | null;
}

export interface VideoFrameItem {
  id: string;
  frameCode: string;
  frameNumber: number;
  timestampSeconds: number;
  width: number;
  height: number;
  contentUrl: string;
}

export interface ProcessingJobView {
  id: string;
  jobCode: string;
  videoAssetCode: string | null;
  status: JobStatus;
  progress: number;
  currentStep: string;
  errorCode: string | null;
  errorMessage: string | null;
}

export type AnalysisStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "needs_review";

export type AnalysisSeverity = "none" | "low" | "medium" | "high" | "critical";

export type ReviewDecision =
  | "pending"
  | "confirmed"
  | "rejected"
  | "needs_more_info";

export interface AnalysisEvidenceItem {
  id: string;
  frameId: string;
  frameCode: string;
  timestampSeconds: number;
  observation: string;
  relevance: string;
  contentUrl: string;
}

export interface AnalysisReviewView {
  id: string;
  decision: ReviewDecision;
  reviewerName: string;
  notes: string | null;
  reviewedAt: string | null;
}

export interface IncidentAnalysisView {
  id: string;
  analysisCode: string;
  videoAssetCode: string | null;
  status: AnalysisStatus;
  providerName: string;
  isDemo: boolean;
  isSimulated: boolean;
  providerLabel: string;
  incidentDetected: boolean | null;
  incidentType: string | null;
  summary: string | null;
  detailedAnalysis: string | null;
  severity: AnalysisSeverity | null;
  confidence: number | null;
  recommendedActions: string[];
  limitations: string[];
  inconclusive: boolean;
  requiredPpe: string[];
  observedPpe: string[];
  possiblyMissingPpe: string[];
  analysisMode: string | null;
  humanReviewRequired: boolean;
  errorCode: string | null;
  errorMessage: string | null;
  evidence: AnalysisEvidenceItem[];
  review: AnalysisReviewView | null;
  humanApprovalRequired: boolean;
}
