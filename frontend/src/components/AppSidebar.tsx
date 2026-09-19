"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield } from "lucide-react";
import { cn } from "cn";
import { navigationItems } from "@/lib/navigation";
import { facilityInfo } from "@/data/mock";

interface AppSidebarProps {
  className?: string;
  onNavigate?: () => void;
}

export function AppSidebar({ className, onNavigate }: AppSidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex h-full w-64 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground",
        className
      )}
    >
      <div className="flex items-center gap-3 border-b border-sidebar-border px-5 py-5">
        <div className="flex size-9 items-center justify-center rounded-lg border border-primary/30 bg-primary/15 text-primary">
          <Shield className="size-4" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-tight text-foreground">
            SafetyLens
          </p>
          <p className="text-[11px] text-muted-foreground">See danger. Trigger action.</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Primary">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
                isActive
                  ? "bg-sidebar-accent text-foreground shadow-sm ring-1 ring-primary/25"
                  : "text-muted-foreground hover:bg-sidebar-accent/70 hover:text-foreground"
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <span
                className={cn(
                  "h-5 w-0.5 rounded-full transition",
                  isActive ? "bg-primary" : "bg-transparent"
                )}
                aria-hidden="true"
              />
              <Icon className="size-4 shrink-0" aria-hidden="true" />
              {item.title}
            </Link>
          );
        })}
      </nav>

      <div className="space-y-3 border-t border-sidebar-border p-4 text-xs">
        <div>
          <p className="text-muted-foreground">Facility</p>
          <p className="mt-0.5 font-medium text-foreground">{facilityInfo.name}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Operational status</p>
          <p className="mt-0.5 inline-flex items-center gap-1.5 font-medium text-emerald-300">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            {facilityInfo.operationalStatus}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-secondary/40 p-3">
          <p className="text-muted-foreground">Current user</p>
          <p className="mt-0.5 font-medium text-foreground">{facilityInfo.currentUser}</p>
          <p className="mt-2 text-muted-foreground">Role</p>
          <p className="mt-0.5 font-medium text-foreground">{facilityInfo.role}</p>
        </div>
      </div>
    </aside>
  );
}
