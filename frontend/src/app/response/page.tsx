"use client";

import { PageHeader } from "@/components/PageHeader";
import { PolicyResponseWorkspace } from "@/components/PolicyResponseWorkspace";

export default function ResponsePage() {
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <PageHeader
        title="Response Center"
        subtitle="Review the selected uploaded-video analysis, retrieve verified procedures, and approve simulated actions"
      />
      <PolicyResponseWorkspace />
    </div>
  );
}
