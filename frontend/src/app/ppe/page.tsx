import Link from "next/link";
import { PpeContextPreview } from "@/components/PpeContextPreview";
import { PpeCapabilities } from "@/components/PpeCapabilities";
import { Suspense } from "react";
import { IncidentHistory } from "@/components/IncidentHistory";
export default function PpePage() {
  return (
    <div className="space-y-5">
      <p className="rounded-xl border border-amber-500/20 p-4 text-sm text-muted-foreground">
        Local PPE deployment is disabled: no validated, license-cleared model is available. Offline inference evaluation and historical reviews remain available. Configured demo observations remain
        labeled.{" "}
        <Link href="/cameras" className="text-blue-400">
          Manage camera-specific PPE requirements
        </Link>
        .
      </p>
      <PpeCapabilities />
      <PpeContextPreview />
      <Suspense fallback={<p>Loading PPE reviews…</p>}>
        <IncidentHistory ppeOnly />
      </Suspense>
    </div>
  );
}
