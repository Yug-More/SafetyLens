"use client";
import Link from "next/link";
import { FormEvent, useCallback, useState } from "react";
import { platformRequest } from "@/lib/api/platform";
import { useApiResource } from "@/hooks/useApiResource";
import { useSession } from "@/components/AuthBoundary";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
interface Config {
  auth_enabled: boolean;
  cookie_secure: boolean;
  ai_provider: string;
  vision_model: string | null;
  planner_provider: string;
  evidence_retention_days: number;
  external_actions: string;
  installation_scope: string;
  detectors: Record<string, string>;
}
const emptyConfig = () => null;
export default function SettingsPage() {
  const session = useSession();
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const loader = useCallback(
    () => platformRequest<Config>("/api/platform/config"),
    [],
  );
  const { data, error, reload } = useApiResource({
    loader,
    fallback: emptyConfig,
    allowFallback: false,
  });
  async function createUser(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    const form = e.currentTarget;
    const values = new FormData(form);
    try {
      await platformRequest("/api/users", "POST", {
        username: values.get("username"),
        password: values.get("password"),
        role: values.get("role"),
      });
      form.reset();
      setMessage("User created.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "User creation failed");
    } finally {
      setBusy(false);
    }
  }
  async function retention(apply = false) {
    if (
      apply &&
      !window.confirm(
        "Permanently expire eligible resolved video and frame files? Metadata and audit records remain.",
      )
    )
      return;
    try {
      const result = await platformRequest<{
        candidate_asset_codes: string[];
        removed_files: number;
      }>("/api/retention", "POST", { apply, confirmed: apply });
      setMessage(
        `${result.candidate_asset_codes.length} eligible videos; ${result.removed_files} files removed.`,
      );
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Retention failed");
    }
  }
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="Platform settings"
        subtitle="Installation safeguards and operational configuration."
      />
      {error && (
        <p role="alert">
          {error}
          <Button onClick={reload}>Retry</Button>
        </p>
      )}
      <section className="rounded-xl border border-border bg-panel p-6">
        <h2 className="font-semibold">Runtime configuration</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Provider secrets and infrastructure settings are managed server-side.
          No keys are sent to this page.
        </p>
        <dl className="mt-5 divide-y divide-border">
          {data &&
            [
              [
                "Authentication",
                data.auth_enabled ? "Enabled" : "Local demo only",
              ],
              [
                "Secure cookies",
                data.cookie_secure ? "Enabled" : "Disabled (local HTTP)",
              ],
              [
                "Analysis provider",
                `${data.ai_provider}${data.vision_model ? ` / ${data.vision_model}` : ""}`,
              ],
              ["Planning", data.planner_provider],
              ["External actions", data.external_actions],
              [
                "Default evidence retention",
                `${data.evidence_retention_days} days`,
              ],
              ["Scope", data.installation_scope],
            ].map(([label, value]) => (
              <div key={label} className="grid gap-2 py-3 sm:grid-cols-2">
                <dt className="text-sm text-muted-foreground">{label}</dt>
                <dd className="text-sm">{value}</dd>
              </div>
            ))}
        </dl>
        <Link
          className="mt-4 inline-block text-sm text-blue-400"
          href="/cameras"
        >
          Configure camera thresholds, PPE, facilities, zones and recording
          windows →
        </Link>
      </section>
      <section className="rounded-xl border border-border bg-panel p-6">
        <h2 className="font-semibold">Detector capabilities</h2>
        {data &&
          Object.entries(data.detectors).map(([name, status]) => (
            <p className="mt-3 text-sm" key={name}>
              <span className="font-medium">{name.replaceAll("_", " ")}:</span>{" "}
              <span className="text-muted-foreground">{status}</span>
            </p>
          ))}
      </section>
      {session?.role === "administrator" && (
        <>
          <section className="rounded-xl border border-border bg-panel p-6">
            <h2 className="font-semibold">Create installation user</h2>
            <form
              onSubmit={createUser}
              className="mt-4 grid gap-4 sm:grid-cols-2"
            >
              <label className="text-sm">
                Username
                <Input
                  name="username"
                  required
                  maxLength={120}
                  autoComplete="off"
                />
              </label>
              <label className="text-sm">
                Initial password
                <Input
                  type="password"
                  name="password"
                  required
                  minLength={12}
                  maxLength={1024}
                  autoComplete="new-password"
                />
              </label>
              <label className="text-sm">
                Role
                <select
                  name="role"
                  className="block w-full rounded border border-border bg-panel p-2"
                >
                  {[
                    "viewer",
                    "safety_operator",
                    "safety_manager",
                    "administrator",
                  ].map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
              </label>
              <Button type="submit" disabled={busy}>
                {busy ? "Creating…" : "Create user"}
              </Button>
            </form>
          </section>
          <section className="rounded-xl border border-amber-500/20 bg-panel p-6">
            <h2 className="font-semibold">Evidence retention</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Only media for resolved incidents beyond its camera retention
              period can expire. Open and unlinked evidence is preserved.
            </p>
            <div className="mt-4 flex gap-3">
              <Button variant="outline" onClick={() => void retention()}>
                Preview expiration
              </Button>
              <Button variant="outline" onClick={() => void retention(true)}>
                Apply expiration
              </Button>
            </div>
          </section>
        </>
      )}
      <p role="status" className="text-sm">
        {message}
      </p>
    </div>
  );
}
