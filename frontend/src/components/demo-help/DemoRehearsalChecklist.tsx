"use client";

import { useMemo, useState } from "react";
import { Check, RotateCcw } from "lucide-react";

const rehearsalItems = [
  "Open the app and confirm the current API or Offline Demo Mode banner is understood.",
  "Choose a short, permitted demo video before the presentation begins.",
  "Export real fall-detector JSON and import it with the matching video.",
  "Call out scripted Demo AI, seeded SOPs, and simulated actions explicitly.",
  "Rehearse retrieval, plan approval, audit review, and PDF download end to end.",
];

export function DemoRehearsalChecklist() {
  const [checked, setChecked] = useState<boolean[]>(() => rehearsalItems.map(() => false));
  const completeCount = useMemo(() => checked.filter(Boolean).length, [checked]);

  const toggleItem = (index: number) => {
    setChecked((current) =>
      current.map((isChecked, itemIndex) =>
        itemIndex === index ? !isChecked : isChecked
      )
    );
  };

  return (
    <section
      className="rounded-xl border border-border bg-panel p-5 shadow-sm"
      aria-labelledby="rehearsal-checklist-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="rehearsal-checklist-heading" className="text-base font-semibold text-foreground">
            Rehearsal checklist
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            This is a local practice aid only. Checking an item does not approve, process, or
            change an incident.
          </p>
        </div>
        <span
          className="rounded-md border border-border bg-secondary/40 px-2.5 py-1 text-xs font-medium text-muted-foreground"
          aria-live="polite"
        >
          {completeCount} of {rehearsalItems.length} ready
        </span>
      </div>

      <ul className="mt-4 space-y-2">
        {rehearsalItems.map((item, index) => {
          const isChecked = checked[index];
          return (
            <li key={item}>
              <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border/70 bg-secondary/25 px-3 py-2.5 text-sm transition-colors hover:bg-secondary/45">
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleItem(index)}
                  className="sr-only"
                />
                <span
                  aria-hidden="true"
                  className={`mt-0.5 flex size-4 shrink-0 items-center justify-center rounded border ${
                    isChecked
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-muted-foreground/60 bg-background"
                  }`}
                >
                  {isChecked ? <Check className="size-3" strokeWidth={3} /> : null}
                </span>
                <span className={isChecked ? "text-foreground" : "text-muted-foreground"}>
                  {item}
                </span>
              </label>
            </li>
          );
        })}
      </ul>

      <button
        type="button"
        onClick={() => setChecked(rehearsalItems.map(() => false))}
        className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
      >
        <RotateCcw className="size-3.5" aria-hidden="true" />
        Reset rehearsal checks
      </button>
    </section>
  );
}
