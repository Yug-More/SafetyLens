"use client";

import { useSyncExternalStore } from "react";
import { format } from "date-fns";

interface LiveClockProps {
  className?: string;
  showSeconds?: boolean;
}

function subscribe(onStoreChange: () => void) {
  const interval = window.setInterval(onStoreChange, 1000);
  return () => window.clearInterval(interval);
}

function getSnapshot() {
  return Date.now();
}

function getServerSnapshot() {
  return 0;
}

export function LiveClock({ className, showSeconds = true }: LiveClockProps) {
  const timestamp = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  if (timestamp === 0) {
    return <span className={className}>—</span>;
  }

  const now = new Date(timestamp);
  const pattern = showSeconds ? "MMM d, yyyy · HH:mm:ss" : "MMM d, yyyy · HH:mm";

  return (
    <time dateTime={now.toISOString()} className={className}>
      {format(now, pattern)}
    </time>
  );
}
