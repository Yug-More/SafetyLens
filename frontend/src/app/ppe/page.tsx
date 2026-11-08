import Link from "next/link";
import { Suspense } from "react";
import { IncidentHistory } from "@/components/IncidentHistory";
export default function PpePage() {
  return (
    <div className="space-y-5">
      <p className="rounded-xl border border-amber-500/20 p-4 text-sm text-muted-foreground">
        ONNX PPE inference is experimental. Configured demo observations remain
        labeled.{" "}
        <Link href="/cameras" className="text-blue-400">
          Manage camera-specific PPE requirements
        </Link>
        .
      </p>
      <Suspense fallback={<p>Loading PPE reviews…</p>}>
        <IncidentHistory ppeOnly />
      </Suspense>
    </div>
  );
}
