/** Durable incident-workflow navigation helpers. Prefer URL query params. */

export interface IncidentContextIds {
  camera_id?: string | null;
  video_id?: string | null;
  processing_job_id?: string | null;
  analysis_id?: string | null;
  incident_id?: string | null;
  retrieval_id?: string | null;
  response_plan_id?: string | null;
  approval_id?: string | null;
  execution_ids?: string[] | null;
  report_id?: string | null;
}

const CONTEXT_KEYS = [
  "camera_id",
  "video_id",
  "processing_job_id",
  "analysis_id",
  "incident_id",
  "retrieval_id",
  "response_plan_id",
  "approval_id",
  "report_id",
] as const;

export function parseIncidentContext(
  searchParams: URLSearchParams | { get(name: string): string | null }
): IncidentContextIds {
  const result: IncidentContextIds = {};
  for (const key of CONTEXT_KEYS) {
    const value = searchParams.get(key);
    if (value) {
      result[key] = value;
    }
  }
  const executions = searchParams.get("execution_ids");
  if (executions) {
    result.execution_ids = executions
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return result;
}

export function buildIncidentQuery(
  ids: IncidentContextIds,
  existing?: URLSearchParams | string
): string {
  const params =
    typeof existing === "string"
      ? new URLSearchParams(existing)
      : existing
        ? new URLSearchParams(existing.toString())
        : new URLSearchParams();

  for (const key of CONTEXT_KEYS) {
    const value = ids[key];
    if (value) {
      params.set(key, value);
    }
  }
  if (ids.execution_ids?.length) {
    params.set("execution_ids", ids.execution_ids.join(","));
  }
  return params.toString();
}

export function buildIncidentHref(
  path: string,
  ids: IncidentContextIds,
  existing?: URLSearchParams | string
): string {
  const query = buildIncidentQuery(ids, existing);
  if (!query) return path;
  return `${path}?${query}`;
}

export function buildResponseHref(ids: {
  video_id?: string | null;
  analysis_id?: string | null;
  incident_id?: string | null;
  camera_id?: string | null;
}): string {
  return buildIncidentHref("/response", {
    video_id: ids.video_id,
    analysis_id: ids.analysis_id,
    incident_id: ids.incident_id,
    camera_id: ids.camera_id,
  });
}

export function hasIncidentContext(ids: IncidentContextIds): boolean {
  return Boolean(ids.analysis_id || ids.video_id || ids.incident_id);
}
