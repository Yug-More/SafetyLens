"use client";

import type { ReactNode } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { facilityInfo } from "@/data/mock";

interface SettingRowProps {
  label: string;
  description: string;
  children: ReactNode;
}

function SettingRow({ label, description, children }: SettingRowProps) {
  return (
    <div className="grid gap-3 py-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,16rem)] sm:items-center">
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
      <div>{children}</div>
    </div>
  );
}

export default function SettingsPage() {
  const saveMock = (section: string) => {
    toast.message(`${section} settings saved in demo mode only.`);
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Facility configuration and safety-operation preferences for the demo environment"
      />

      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm sm:p-6">
        <h2 className="text-base font-semibold text-foreground">Facility Information</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Core identity for the monitored workplace site
        </p>
        <Separator className="my-4" />
        <SettingRow
          label="Facility name"
          description="Displayed across the operations console"
        >
          <Input defaultValue={facilityInfo.name} aria-label="Facility name" />
        </SettingRow>
        <SettingRow
          label="Primary contact"
          description="Safety administrator for escalation"
        >
          <Input
            defaultValue={facilityInfo.currentUser}
            aria-label="Primary contact"
          />
        </SettingRow>
        <div className="flex justify-end pt-2">
          <Button onClick={() => saveMock("Facility")}>Save Facility</Button>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm sm:p-6">
        <h2 className="text-base font-semibold text-foreground">Camera Configuration</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Monitoring defaults for connected camera sources
        </p>
        <Separator className="my-4" />
        <SettingRow
          label="Default monitoring mode"
          description="Applied to newly connected cameras"
        >
          <Input defaultValue="Continuous edge detection" aria-label="Monitoring mode" />
        </SettingRow>
        <SettingRow
          label="Evidence buffer"
          description="Seconds retained before and after detection"
        >
          <Input defaultValue="20 seconds" aria-label="Evidence buffer" />
        </SettingRow>
        <div className="flex justify-end pt-2">
          <Button onClick={() => saveMock("Camera")}>Save Cameras</Button>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm sm:p-6">
        <h2 className="text-base font-semibold text-foreground">Alert Preferences</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Channels and thresholds for supervisor notifications
        </p>
        <Separator className="my-4" />
        <SettingRow
          label="High-severity alerts"
          description="Immediate notification destination"
        >
          <Input
            defaultValue="Safety Administrator + Floor Supervisor"
            aria-label="High-severity alerts"
          />
        </SettingRow>
        <SettingRow
          label="Medium-severity alerts"
          description="Standard notification destination"
        >
          <Input defaultValue="Floor Supervisor" aria-label="Medium-severity alerts" />
        </SettingRow>
        <div className="flex justify-end pt-2">
          <Button onClick={() => saveMock("Alert")}>Save Alerts</Button>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm sm:p-6">
        <h2 className="text-base font-semibold text-foreground">
          Human Approval Requirements
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Keep consequential actions behind supervisor confirmation
        </p>
        <Separator className="my-4" />
        <SettingRow
          label="Require approval for high severity"
          description="Critical actions stay human-gated"
        >
          <Input defaultValue="Required" aria-label="High severity approval" />
        </SettingRow>
        <SettingRow
          label="Auto-suggest low severity actions"
          description="Recommendations remain editable before execution"
        >
          <Input defaultValue="Enabled" aria-label="Low severity suggestions" />
        </SettingRow>
        <div className="flex justify-end pt-2">
          <Button onClick={() => saveMock("Approval")}>Save Approvals</Button>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm sm:p-6">
        <h2 className="text-base font-semibold text-foreground">Data Retention</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Evidence and audit retention policies for the facility
        </p>
        <Separator className="my-4" />
        <SettingRow
          label="Evidence clip retention"
          description="How long preserved clips remain available"
        >
          <Input defaultValue="90 days" aria-label="Evidence retention" />
        </SettingRow>
        <SettingRow
          label="Audit log retention"
          description="Decision and action history window"
        >
          <Input defaultValue="365 days" aria-label="Audit retention" />
        </SettingRow>
        <div className="flex justify-end pt-2">
          <Button onClick={() => saveMock("Retention")}>Save Retention</Button>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm sm:p-6">
        <h2 className="text-base font-semibold text-foreground">Integrations</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Future connections for ticketing, messaging, and storage
        </p>
        <Separator className="my-4" />
        <SettingRow
          label="Notification provider"
          description="Stage 2 placeholder"
        >
          <Input defaultValue="Not connected" aria-label="Notification provider" />
        </SettingRow>
        <SettingRow
          label="Incident ticketing"
          description="Stage 2 placeholder"
        >
          <Input defaultValue="Not connected" aria-label="Incident ticketing" />
        </SettingRow>
        <div className="flex justify-end pt-2">
          <Button onClick={() => saveMock("Integrations")}>Save Integrations</Button>
        </div>
      </section>
    </div>
  );
}
