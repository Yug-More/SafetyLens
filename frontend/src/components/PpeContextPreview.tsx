"use client";
import { FormEvent, useCallback, useState } from "react";
import { ManagedCamera, platformRequest } from "@/lib/api/platform";
import { useApiResource } from "@/hooks/useApiResource";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
type Preview = { required_ppe: string[]; context_unknown_ppe: string[]; applied_rules: string[]; pending_rules: string[] };
const empty = () => ({ cameras: [] as ManagedCamera[], role: "" });
const readable = (values: string[]) => values.length ? values.map(v=>v.replaceAll("_", " ")).join(", ") : "None";
export function PpeContextPreview() {
  const loader = useCallback(async () => {
    const [cameras, user] = await Promise.all([platformRequest<ManagedCamera[]>("/api/camera-management"), platformRequest<{role:string}>("/api/auth/me")]);
    return { cameras, role: user.role };
  }, []);
  const { data, error, isLoading } = useApiResource({loader, fallback: empty, allowFallback:false});
  const [result, setResult] = useState<Preview | null>(null);
  const [failure, setFailure] = useState("");
  const [busy,setBusy] = useState(false);
  async function preview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setResult(null); setFailure("");setBusy(true);
    const form = new FormData(event.currentTarget); const time=String(form.get("time") || "");
    try { setResult(await platformRequest<Preview>(`/api/cameras/${encodeURIComponent(String(form.get("camera")))}/ppe-context-preview`,"POST",{
      activity:form.get("activity") || null, worker_role:form.get("worker_role") || null,
      minute_of_day:time ? Number(time.split(":")[0])*60+Number(time.split(":")[1]) : null,
    })); } catch(e) {setFailure(e instanceof Error ? e.message : "Policy preview failed");} finally {setBusy(false);}
  }
  if(isLoading)return <p role="status">Loading policy context…</p>;
  if(error)return <p role="alert">Policy context unavailable: {error}</p>;
  if(data?.role!=="administrator")return null;
  return <section aria-labelledby="ppe-context-preview" className="rounded-xl border border-border bg-panel p-5">
    <h2 id="ppe-context-preview" className="font-semibold">Preview contextual requirements</h2>
    <p className="mt-2 text-sm text-muted-foreground">Administrator policy check only. Enter known operational context; leave unknown fields blank. This does not run inference or authorize a response. Time uses the policy&apos;s local operational clock.</p>
    <form onSubmit={preview} onChange={()=>setResult(null)} className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <label className="text-sm">Policy camera<select name="camera" required className="mt-2 block w-full rounded-md border border-border bg-background p-2">{data.cameras.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
      <label className="text-sm">Known activity<Input name="activity" maxLength={100} className="mt-2" /></label>
      <label className="text-sm">Operational role<Input name="worker_role" maxLength={100} className="mt-2" /></label>
      <label className="text-sm">Operational local time<Input name="time" type="time" className="mt-2" /></label>
      <Button type="submit" disabled={busy || !data.cameras.length}>{busy ? "Checking policy…" : "Preview requirements"}</Button>
    </form>
    {failure && <p role="alert" className="mt-3 text-sm text-amber-400">{failure}</p>}
    {result && <div role="status" className="mt-4 space-y-2 text-sm"><p>Required: {readable(result.required_ppe)}</p><p>Unknown context: {readable(result.context_unknown_ppe)}</p><p>Applied rules: {readable(result.applied_rules)}</p><p>Pending context: {readable(result.pending_rules)}</p></div>}
  </section>;
}
