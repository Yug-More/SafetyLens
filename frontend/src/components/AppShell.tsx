"use client";

import type { ReactNode } from "react";
import { AppSidebar } from "@/components/AppSidebar";
import { TopNavigation } from "@/components/TopNavigation";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <div className="hidden lg:block">
        <div className="sticky top-0 h-screen">
          <AppSidebar />
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <TopNavigation />
        <main className="flex-1 overflow-x-hidden px-4 py-5 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
