"use client";

import { Suspense } from "react";
import { PageHeader } from "@/components/PageHeader";
import { PolicyResponseWorkspace } from "@/components/PolicyResponseWorkspace";
import { PanelSkeleton } from "@/components/ConnectionBanner";

export default function ResponsePage() {
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <PageHeader
        title="Incident Command Center"
        subtitle="Review AI-detected incidents, confirm findings, and approve simulated response actions"
      />
      <Suspense fallback={<PanelSkeleton className="min-h-96" />}>
        <PolicyResponseWorkspace />
      </Suspense>
    </div>
  );
}
