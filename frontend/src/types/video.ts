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
