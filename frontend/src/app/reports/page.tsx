"use client";

import { toast } from "sonner";
import { Download, FileBarChart } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PageHeader } from "@/components/PageHeader";
import { MetricCard } from "@/components/MetricCard";
import { Button } from "@/components/ui/button";
import {
  reportSummaries,
  resolutionBreakdown,
  severityBreakdown,
} from "@/data/mock";

export default function ReportsPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <PageHeader
        title="Reports"
        subtitle="Operational summaries and incident analytics for the demo environment"
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Incidents This Week"
          value={4}
          detail="Across all monitored zones"
          icon={FileBarChart}
          trendLabel="1 awaiting review"
          trendTone="attention"
        />
        <MetricCard
          title="Resolved"
          value={2}
          detail="Closed within SLA targets"
          icon={FileBarChart}
          trendLabel="50% of weekly volume"
          trendTone="positive"
        />
        <MetricCard
          title="Avg. Review Time"
          value="42 sec"
          detail="From detection to supervisor review"
          icon={FileBarChart}
          trendLabel="18% faster week over week"
          trendTone="positive"
        />
        <MetricCard
          title="Reports Ready"
          value={3}
          detail="Downloadable demo summaries"
          icon={FileBarChart}
          trendLabel="Mock exports only"
          trendTone="neutral"
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
          <h2 className="text-base font-semibold text-foreground">
            Severity Breakdown
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Distribution of mock incidents by severity
          </p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityBreakdown}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                >
                  {severityBreakdown.map((entry) => (
                    <Cell key={entry.name} fill={entry.fill} />
                  ))}
                </Pie>
                <RechartsTooltip
                  contentStyle={{
                    background: "#151e31",
                    border: "1px solid rgba(148,163,184,0.2)",
                    borderRadius: 8,
                    color: "#f8fafc",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
            {severityBreakdown.map((item) => (
              <span key={item.name} className="inline-flex items-center gap-1.5">
                <span
                  className="size-2 rounded-full"
                  style={{ backgroundColor: item.fill }}
                />
                {item.name}: {item.value}
              </span>
            ))}
          </div>
        </article>

        <article className="rounded-xl border border-border bg-panel p-4 shadow-sm">
          <h2 className="text-base font-semibold text-foreground">
            Resolution Status
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Current handling state across the incident set
          </p>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={resolutionBreakdown}>
                <CartesianGrid stroke="rgba(148,163,184,0.12)" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                />
                <RechartsTooltip
                  contentStyle={{
                    background: "#151e31",
                    border: "1px solid rgba(148,163,184,0.2)",
                    borderRadius: 8,
                    color: "#f8fafc",
                  }}
                />
                <Bar dataKey="value" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
      </section>

      <section className="rounded-xl border border-border bg-panel p-4 shadow-sm">
        <h2 className="text-base font-semibold text-foreground">Recent Reports</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Generated summaries available for mock download
        </p>
        <ul className="mt-4 space-y-2">
          {reportSummaries.map((report) => (
            <li
              key={report.id}
              className="flex flex-col gap-3 rounded-lg border border-border bg-secondary/30 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="font-medium text-foreground">{report.title}</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {report.period} · {report.incidentCount} incidents · Generated{" "}
                  {report.generatedAt}
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() =>
                  toast.message(
                    `Mock download started for “${report.title}”. File export arrives later.`
                  )
                }
              >
                <Download data-icon="inline-start" />
                Download
              </Button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
