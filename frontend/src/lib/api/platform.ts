import { ApiError, getApiBaseUrl, getCsrfToken } from "./client";
export async function platformRequest<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method,
    credentials: "include",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(body ? { "Content-Type": "application/json" } : {}),
      "X-CSRF-Token": getCsrfToken(),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const payload = await response.json();
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new Event("session-expired"));
    throw new ApiError(
      payload.error?.code ?? "HTTP_ERROR",
      payload.error?.message ?? "Request failed",
      response.status,
    );
  }
  return payload.data as T;
}
export interface ManagedCamera {
  id: string;
  name: string;
  location: string;
  status: string;
  facility: string;
  zone: string;
  enabled: boolean;
  source_kind: string;
  source_configured: boolean;
  snapshot_url: string;
  heartbeat_age_seconds: number;
  health_details: string;
  capability_status: string;
  policy: {
    detectors?: string[];
    sample_fps?: number;
    required_ppe?: string[];
    confidence_threshold?: number;
    pre_event_seconds?: number;
    post_event_seconds?: number;
    retention_days?: number;
  };
}
export interface SafetyAnalytics {
  incidents: number;
  window_days: number;
  by_day: [string, number][];
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  by_camera: Record<string, number>;
  confirmed_reviews: number;
  rejected_reviews: number;
  mean_review_seconds: number | null;
  review_sample_size: number;
  false_alarm_review_fraction: number | null;
  definitions: Record<string, string>;
  includes_demo_records: boolean;
}
