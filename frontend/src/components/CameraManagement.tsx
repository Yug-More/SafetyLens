"use client";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { Camera, Plus, RefreshCw, Pencil, Maximize2 } from "lucide-react";
import { platformRequest, ManagedCamera } from "@/lib/api/platform";
import { getApiBaseUrl } from "@/lib/api/client";
import { useApiResource } from "@/hooks/useApiResource";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
const empty = () => [] as ManagedCamera[];
const ppeRequirements = [
  ["hat", "hard_hat", "Require hard hat"],
  ["vest", "high_visibility_vest", "Require safety vest"],
  ["goggles", "safety_goggles", "Require protective eyewear"],
  ["boots", "protective_footwear", "Require protective footwear"],
  ["gloves", "protective_gloves", "Require protective gloves"],
  ["shield", "face_shield", "Require face shield"],
  ["hearing", "hearing_protection", "Require hearing protection"],
  ["respirator", "respiratory_protection", "Require respiratory protection"],
] as const;

function CameraPreview({ camera }: { camera: ManagedCamera }) {
  const [url, setUrl] = useState("");
  const [failed, setFailed] = useState(false);
  const frame = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let cancelled = false;
    let current = "";
    let controller: AbortController;
    let timer: ReturnType<typeof setTimeout>;
    const refresh = async () => {
      controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 5000);
      try {
        const response = await fetch(getApiBaseUrl() + camera.snapshot_url, {
          credentials: "include",
          cache: "no-store",
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("No preview");
        const blob = await response.blob();
        if (cancelled) return;
        const next = URL.createObjectURL(blob);
        if (current) URL.revokeObjectURL(current);
        current = next;
        setUrl(next);
        setFailed(false);
      } catch {
        if (!cancelled) setFailed(true);
      } finally {
        clearTimeout(timeout);
        if (!cancelled) timer = setTimeout(() => void refresh(), 3000);
      }
    };
    void refresh();

    return () => {
      cancelled = true;
      clearTimeout(timer);
      controller?.abort();
      if (current) URL.revokeObjectURL(current);
    };
  }, [camera.snapshot_url]);
  return (
    <div
      ref={frame}
      className="relative flex aspect-video items-center justify-center overflow-hidden rounded-lg bg-black"
    >
      {url && !failed ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={url}
          alt={`${camera.name} camera preview`}
          className="h-full w-full object-contain"
        />
      ) : (
        <div className="text-center text-slate-400">
          <Camera className="mx-auto size-8" />
          <p className="mt-2 text-sm">No recent preview</p>
          <p className="mt-1 text-xs">
            Connect the authenticated camera worker.
          </p>
        </div>
      )}
      <span className="absolute left-2 top-2 rounded bg-black/80 px-2 py-1 text-[10px] text-slate-100">
        {camera.source_kind === "replay"
          ? "RECORDED REPLAY"
          : camera.source_kind === "simulator" || camera.source_kind === "demo"
            ? "SIMULATED / DEMO"
            : "CAMERA PREVIEW · 3s refresh"}
      </span>
      <button
        aria-label={`Fullscreen ${camera.name}`}
        className="absolute bottom-2 right-2 rounded bg-black/80 p-2 text-white"
        onClick={() => void frame.current?.requestFullscreen()}
      >
        <Maximize2 className="size-4" />
      </button>
    </div>
  );
}

export function CameraManagement({ monitor = false }: { monitor?: boolean }) {
  const loader = useCallback(
    () => platformRequest<ManagedCamera[]>("/api/camera-management"),
    [],
  );
  const { data, error, isLoading, reload } = useApiResource({
    loader,
    fallback: empty,
    allowFallback: false,
  });
  const [search, setSearch] = useState("");
  const [facility, setFacility] = useState("");
  const [editing, setEditing] = useState<ManagedCamera | null | undefined>();
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [columns, setColumns] = useState(2);
  const [role, setRole] = useState("");
  useEffect(() => {
    void platformRequest<{ role: string }>("/api/auth/me").then((x) =>
      setRole(x.role),
    );
  }, []);
  const canEdit = role === "administrator";
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setSaving(true);
    setMessage("");
    try {
      const body = {
        name: form.get("name"),
        location: form.get("location"),
        facility: form.get("facility"),
        zone: form.get("zone"),
        source_kind: form.get("source_kind"),
        source: form.get("source") || null,
        enabled: form.get("enabled") === "on",
        policy: {
          detectors: [
            "fall",
            "camera_health",
            ...(form.get("ppe") === "on" ? ["ppe"] : []),
          ],
          required_ppe: ppeRequirements.filter(([name]) => form.get(name) === "on").map(([, category]) => category),
          ppe_context_rules: JSON.parse(String(form.get("ppe_context_rules") || "[]")),
          sample_fps: Number(form.get("fps")),
          maximum_pose_people: Number(form.get("people")),
          pose_region: String(form.get("pose_region") ?? "").trim()
            ? String(form.get("pose_region")).split(",").map(Number) : null,
          confidence_threshold: Number(form.get("confidence")),
          pre_event_seconds: Number(form.get("pre")),
          post_event_seconds: Number(form.get("post")),
          retention_days: Number(form.get("retention")),
        },
      };
      await platformRequest(
        editing ? `/api/cameras/${editing.id}` : "/api/cameras",
        editing ? "PUT" : "POST",
        body,
      );
      setEditing(undefined);
      reload();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }
  async function remove(camera: ManagedCamera) {
    if (
      !window.confirm(
        `Delete ${camera.name}? Cameras with evidence cannot be deleted.`,
      )
    )
      return;
    try {
      await platformRequest(`/api/cameras/${camera.id}`, "DELETE");
      reload();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Delete failed");
    }
  }
  const cameras = (data ?? []).filter(
    (x) =>
      (!facility || x.facility === facility) &&
      `${x.name} ${x.location} ${x.zone}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <PageHeader
        title={monitor ? "Camera operations" : "Camera management"}
        subtitle="Connection health, detection policies, and evidence settings."
        actions={
          <>
            <Button variant="outline" onClick={reload}>
              <RefreshCw />
              Refresh
            </Button>
            {canEdit && (
              <Button
                onClick={() => {
                  setEditing(null);
                  setMessage("");
                }}
              >
                <Plus />
                Register camera
              </Button>
            )}
          </>
        }
      />
      <div className="flex flex-wrap gap-3">
        <Input
          className="max-w-sm"
          aria-label="Search cameras"
          placeholder="Search camera, location, zone…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          aria-label="Filter by facility"
          className="rounded border border-border bg-panel px-3"
          value={facility}
          onChange={(e) => setFacility(e.target.value)}
        >
          <option value="">All facilities</option>
          {[...new Set(data?.map((x) => x.facility))].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
        {monitor && (
          <select
            aria-label="Grid layout"
            className="rounded border border-border bg-panel px-3"
            value={columns}
            onChange={(e) => setColumns(Number(e.target.value))}
          >
            <option value={1}>Focus view</option>
            <option value={2}>2 columns</option>
            <option value={3}>3 columns</option>
          </select>
        )}
      </div>
      {(error || message) && (
        <p
          role="alert"
          className="rounded-xl border border-amber-400/30 p-4 text-amber-200"
        >
          {error || message}
        </p>
      )}
      {isLoading && <p role="status">Loading cameras…</p>}
      {!isLoading && !cameras.length && (
        <div className="rounded-xl border border-dashed border-border p-12 text-center">
          <Camera className="mx-auto mb-4 size-8" />
          <h2 className="font-semibold">No matching cameras</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Register a camera or adjust your filters.
          </p>
        </div>
      )}
      <div
        className={`grid gap-5 ${columns === 1 ? "grid-cols-1" : columns === 3 ? "md:grid-cols-2 xl:grid-cols-3" : "md:grid-cols-2"}`}
      >
        {cameras.map((camera) => (
          <section
            key={camera.id}
            className="rounded-xl border border-border bg-panel p-4"
          >
            {monitor && <CameraPreview camera={camera} />}
            <div className="mt-3 flex items-start justify-between gap-3">
              <div>
                <h2 className="font-semibold">{camera.name}</h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  {camera.facility} / {camera.zone} · {camera.location}
                </p>
              </div>
              <span
                className={`rounded-full border px-2 py-1 text-xs ${camera.status === "online" ? "border-emerald-500/30 text-emerald-300" : "border-amber-500/30 text-amber-300"}`}
              >
                {camera.capability_status === "demo_simulation"
                  ? "Historical demo"
                  : camera.status}
              </span>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              {camera.policy.detectors?.join(" · ") ||
                "No active detector policy"}{" "}
              · {camera.enabled ? "Enabled" : "Disabled"}
            </p>
            <p
              className="mt-2 truncate font-mono text-[10px] text-muted-foreground"
              title={camera.id}
            >
              {camera.id}
            </p>
            {canEdit && (
              <div className="mt-4 flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setEditing(camera);
                    setMessage("");
                  }}
                >
                  <Pencil />
                  Edit configuration
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => void remove(camera)}
                >
                  Delete
                </Button>
              </div>
            )}
          </section>
        ))}
      </div>
      {editing !== undefined && (
        <section
          aria-label="Camera configuration form"
          className="rounded-xl border border-blue-500/30 bg-panel p-6"
        >
          <h2 className="text-lg font-semibold">
            {editing ? "Edit camera" : "Register camera"}
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Sources are encrypted server-side. A blank source preserves the
            existing credential.
          </p>
          <form
            onSubmit={save}
            className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            key={editing?.id ?? "new"}
          >
            {[
              ["name", "Camera name", editing?.name ?? ""],
              ["location", "Location", editing?.location ?? ""],
              ["facility", "Facility", editing?.facility ?? "Default facility"],
              ["zone", "Zone", editing?.zone ?? "Unassigned"],
            ].map(([name, label, value]) => (
              <label key={name} className="text-sm">
                {label}
                <Input
                  className="mt-2"
                  name={name}
                  defaultValue={value}
                  required
                  maxLength={name === "location" ? 200 : 120}
                />
              </label>
            ))}
            <label className="text-sm">
              Source type
              <select
                name="source_kind"
                defaultValue={
                  editing?.source_kind === "demo"
                    ? "replay"
                    : (editing?.source_kind ?? "webcam")
                }
                className="mt-2 block w-full rounded border border-border bg-panel p-2"
              >
                {["webcam", "rtsp", "network", "replay", "simulator"].map(
                  (x) => (
                    <option key={x}>{x}</option>
                  ),
                )}
              </select>
            </label>
            <label className="text-sm">
              Private source
              <Input
                className="mt-2"
                type="password"
                name="source"
                autoComplete="off"
                placeholder="Index, path or stream URL"
              />
            </label>
            <div className="text-sm">
              <label htmlFor="pose-region">Pose region (normalized x1,y1,x2,y2)</label>
              <Input id="pose-region" name="pose_region" aria-describedby="pose-region-help"
                defaultValue={editing?.policy.pose_region?.join(",") ?? ""}
                placeholder="Blank: full frame; RGB right panel: 0.5,0,1,1" />
              <p id="pose-region-help" className="text-xs text-muted-foreground">Calibrate only for a known camera layout. Evidence retains the full frame.</p>
            </div>
            {[
              [
                "people",
                "Maximum poses (experimental above 1)",
                editing?.policy.maximum_pose_people ?? 1,
                1,4,1,
              ],
              [
                "fps",
                "Sample FPS",
                editing?.policy.sample_fps ?? 8,
                1,
                30,
                0.5,
              ],
              [
                "confidence",
                "PPE score threshold",
                editing?.policy.confidence_threshold ?? 0.5,
                0.05,
                0.99,
                0.05,
              ],
              [
                "pre",
                "Pre-event seconds",
                editing?.policy.pre_event_seconds ?? 3,
                0.5,
                30,
                0.5,
              ],
              [
                "post",
                "Post-event seconds",
                editing?.policy.post_event_seconds ?? 3,
                0.5,
                30,
                0.5,
              ],
              [
                "retention",
                "Retention days",
                editing?.policy.retention_days ?? 30,
                1,
                3650,
                1,
              ],
            ].map(([name, label, value, min, max, step]) => (
              <label key={name} className="text-sm">
                {label}
                <Input
                  className="mt-2"
                  name={String(name)}
                  type="number"
                  defaultValue={value}
                  min={min}
                  max={max}
                  step={step}
                  required
                />
              </label>
            ))}
            <div className="space-y-3 text-sm">
              {[
                ["enabled", "Enable camera", editing?.enabled ?? false],
                [
                  "ppe",
                  "PPE deployment excluded — model not validated",
                  editing?.policy.detectors?.includes("ppe") ?? false,
                ],
                ...ppeRequirements.map(([name, category, label]) => [name, label, editing?.policy.required_ppe?.includes(category) ?? false]),
              ].map(([name, label, checked]) => (
                <label className="block" key={String(name)}>
                  <input
                    type="checkbox"
                    name={String(name)}
                    defaultChecked={name === "ppe" ? false : Boolean(checked)}
                    disabled={name === "ppe"}
                    className="mr-2"
                  />
                  {label}
                </label>
              ))}
            </div>
            <label className="col-span-full text-sm">
              Conditional PPE rules (JSON)
              <textarea name="ppe_context_rules" rows={4} className="mt-2 w-full rounded-md border border-border bg-background p-3 font-mono text-xs"
                defaultValue={JSON.stringify(editing?.policy.ppe_context_rules ?? [], null, 2)} />
              <span className="mt-1 block text-xs text-muted-foreground">Optional rules use label, required_ppe, activity, worker_role and minute_range [0–1439]. Context is supplied by operators, never inferred identity. Missing context stays unknown. Configuring requirements does not enable visual detection.</span>
            </label>
            <div className="col-span-full flex gap-3">
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save camera"}
              </Button>
              <Button
                variant="outline"
                type="button"
                onClick={() => setEditing(undefined)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </section>
      )}
    </div>
  );
}
