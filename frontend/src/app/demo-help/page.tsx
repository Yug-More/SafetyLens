import Link from "next/link";
import {
  ArrowRight,
  BadgeCheck,
  CircleAlert,
  Clapperboard,
  ShieldCheck,
} from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { DemoRehearsalChecklist } from "@/components/demo-help/DemoRehearsalChecklist";

const demoSteps = [
  {
    number: "01",
    title: "Set the scene in Live Monitor",
    description:
      "Show Camera 04 and explain that SafetyLens starts with a short, consented demo recording rather than a real emergency feed.",
    href: "/monitor",
    label: "Open Live Monitor",
    state: "Available now",
  },
  {
    number: "02",
    title: "Upload and inspect evidence candidates",
    description:
      "Upload a short MP4, MOV, or WebM clip. The current pipeline stores the recording, extracts metadata, and samples frames for review.",
    href: "/monitor",
    label: "Review video workspace",
    state: "Available now",
  },
  {
    number: "03",
    title: "Show the procedure library",
    description:
      "Open the seeded safety procedures and explain that retrieval tied to the uploaded video is a later stage, not a live claim in this demo.",
    href: "/procedures",
    label: "Open Procedures",
    state: "Available now",
  },
  {
    number: "04",
    title: "Explain human review",
    description:
      "Use the Response Center to illustrate the intended approval workflow. Its incident, recommendation, and approval controls are demo data; no alert or action is sent.",
    href: "/response",
    label: "Open Response Center",
    state: "Demo interface",
  },
];

export default function DemoHelpPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Demo Guide"
        subtitle="A clear, honest walkthrough for rehearsing the current SafetyLens prototype."
        status={
          <span className="inline-flex items-center gap-1.5 rounded-md border border-primary/30 bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
            <Clapperboard className="size-3.5" aria-hidden="true" />
            Stage 3 rehearsal
          </span>
        }
      />

      <section className="grid gap-4 rounded-xl border border-primary/20 bg-primary/5 p-5 shadow-sm lg:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)] lg:items-center">
        <div>
          <p className="text-xs font-semibold tracking-wide text-primary uppercase">
            The judge-friendly version
          </p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight text-foreground">
            SafetyLens turns a safety recording into a review-ready evidence workspace.
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
            Today&apos;s prototype securely accepts a short video, prepares candidate frames, and
            keeps the proposed response behind a human review experience. The AI verification,
            video-driven procedure retrieval, notifications, and report generation are planned
            stages—not capabilities to claim during this rehearsal.
          </p>
        </div>
        <div className="rounded-lg border border-border bg-panel/80 p-4">
          <div className="flex items-start gap-3">
            <CircleAlert className="mt-0.5 size-5 shrink-0 text-warning" aria-hidden="true" />
            <div>
              <h3 className="text-sm font-semibold text-foreground">Say this out loud</h3>
              <p className="mt-1 text-sm leading-5 text-muted-foreground">
                “The assistant supports a supervisor&apos;s review. It does not replace emergency
                services or automatically execute critical actions.”
              </p>
            </div>
          </div>
        </div>
      </section>

      <section aria-labelledby="demo-sequence-heading">
        <div className="mb-3 flex items-center gap-2">
          <BadgeCheck className="size-4 text-emerald-300" aria-hidden="true" />
          <div>
            <h2 id="demo-sequence-heading" className="text-base font-semibold text-foreground">
              Four-step demo sequence
            </h2>
            <p className="text-sm text-muted-foreground">
              Keep the conversation anchored to what is visible in the prototype today.
            </p>
          </div>
        </div>

        <ol className="grid gap-4 md:grid-cols-2">
          {demoSteps.map((step) => (
            <li key={step.number} className="rounded-xl border border-border bg-panel p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <span className="font-mono text-xs font-semibold text-primary">{step.number}</span>
                <span
                  className={`rounded-md border px-2 py-0.5 text-[11px] font-medium ${
                    step.state === "Available now"
                      ? "border-emerald-400/25 bg-emerald-400/10 text-emerald-300"
                      : "border-warning/25 bg-warning/10 text-amber-200"
                  }`}
                >
                  {step.state}
                </span>
              </div>
              <h3 className="mt-3 text-base font-semibold text-foreground">{step.title}</h3>
              <p className="mt-2 min-h-20 text-sm leading-6 text-muted-foreground">
                {step.description}
              </p>
              <Link
                href={step.href}
                className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-primary transition-colors hover:text-primary/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                {step.label}
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </li>
          ))}
        </ol>
      </section>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <DemoRehearsalChecklist />

        <article className="rounded-xl border border-border bg-panel p-5 shadow-sm">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 size-5 shrink-0 text-emerald-300" aria-hidden="true" />
            <div>
              <h2 className="text-base font-semibold text-foreground">Demo integrity checks</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Protect trust by naming the boundary between the working workflow and the roadmap.
              </p>
            </div>
          </div>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-muted-foreground">
            <li className="rounded-lg border border-border/70 bg-secondary/25 px-3 py-2.5">
              Candidate frames are review aids, not confirmed proof of an incident.
            </li>
            <li className="rounded-lg border border-border/70 bg-secondary/25 px-3 py-2.5">
              The current Response Center uses seeded demo content and simulated approvals.
            </li>
            <li className="rounded-lg border border-border/70 bg-secondary/25 px-3 py-2.5">
              Do not state accuracy, cost savings, alerts sent, or emergency actions completed
              unless they have been measured or implemented.
            </li>
          </ul>
        </article>
      </section>
    </div>
  );
}
