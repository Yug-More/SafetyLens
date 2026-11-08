import { Suspense } from "react";
import { IncidentHistory } from "@/components/IncidentHistory";
export default function IncidentsPage(){return <Suspense fallback={<p>Loading incident filters…</p>}><IncidentHistory/></Suspense>;}
