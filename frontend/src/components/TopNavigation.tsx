"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Play, Search } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { MobileNavigation } from "@/components/MobileNavigation";
import { LiveClock } from "@/components/LiveClock";
import { getPageTitle } from "@/lib/navigation";
import { facilityInfo } from "@/data/mock";

export function TopNavigation() {
  const pathname = usePathname();
  const pageTitle = getPageTitle(pathname);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-background/90 px-4 backdrop-blur-md sm:px-6">
      <MobileNavigation />

      <div className="min-w-0 flex-1">
        <h1 className="truncate text-sm font-semibold text-foreground sm:text-base">
          {pageTitle}
        </h1>
        <LiveClock className="hidden text-xs text-muted-foreground sm:block" />
      </div>

      <div className="flex items-center gap-1.5 sm:gap-2">
        <Tooltip>
          <TooltipTrigger
            render={
              <Button
                variant="ghost"
                size="icon"
                aria-label="Search"
                onClick={() =>
                  toast.message("Search will be available in a later stage.")
                }
              />
            }
          >
            <Search className="size-4" />
          </TooltipTrigger>
          <TooltipContent>Search</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger
            render={
              <Button
                variant="ghost"
                size="icon"
                className="relative"
                aria-label="Notifications, 1 unread"
                onClick={() =>
                  toast.message(
                    "1 unread notification: Possible Worker Fall awaiting review."
                  )
                }
              />
            }
          >
            <Bell className="size-4" />
            <span className="absolute top-1.5 right-1.5 size-1.5 rounded-full bg-destructive" />
          </TooltipTrigger>
          <TooltipContent>Notifications</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger
            render={
              <button
                type="button"
                className="rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label={`${facilityInfo.currentUser}, ${facilityInfo.role}`}
                onClick={() =>
                  toast.message(`${facilityInfo.currentUser} · ${facilityInfo.role}`)
                }
              />
            }
          >
            <Avatar className="size-8 border border-border">
              <AvatarFallback className="bg-secondary text-xs font-medium text-foreground">
                YM
              </AvatarFallback>
            </Avatar>
          </TooltipTrigger>
          <TooltipContent>Yug More</TooltipContent>
        </Tooltip>

        <Button
          className="ml-1"
          nativeButton={false}
          render={<Link href="/response" />}
          onClick={() =>
            toast.message(
              "Demo mode active. Review the open worker-fall incident in Response Center."
            )
          }
        >
          <Play data-icon="inline-start" className="size-3.5" />
          <span className="hidden sm:inline">Start Demo</span>
          <span className="sm:hidden">Demo</span>
        </Button>
      </div>
    </header>
  );
}
