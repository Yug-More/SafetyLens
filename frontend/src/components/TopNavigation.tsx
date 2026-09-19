"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { Bell, Play, Search, X } from "lucide-react";
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
import {
  dismissOperatorNotification,
  fetchOperatorNotifications,
} from "@/lib/api";
import type { ApiOperatorNotification } from "@/lib/api/types";
import { buildResponseHref } from "@/lib/incident-context";

const POLL_INTERVAL_MS = 8000;

export function TopNavigation() {
  const pathname = usePathname();
  const pageTitle = getPageTitle(pathname);
  const [notifications, setNotifications] = useState<ApiOperatorNotification[]>(
    []
  );
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => !n.dismissed).length;

  const loadNotifications = useCallback(async () => {
    try {
      const response = await fetchOperatorNotifications(false);
      setNotifications(response.data);
    } catch {
      // Keep last known notifications on transient failures.
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadNotifications();
    }, 0);
    const interval = window.setInterval(() => {
      void loadNotifications();
    }, POLL_INTERVAL_MS);
    return () => {
      window.clearTimeout(timer);
      window.clearInterval(interval);
    };
  }, [loadNotifications]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [dropdownOpen]);

  async function handleDismiss(
    notification: ApiOperatorNotification,
    event: React.MouseEvent
  ) {
    event.preventDefault();
    event.stopPropagation();
    try {
      await dismissOperatorNotification(notification.notification_code);
      setNotifications((current) =>
        current.filter((item) => item.id !== notification.id)
      );
      toast.message("Notification dismissed.");
    } catch {
      toast.error("Unable to dismiss notification.");
    }
  }

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

        <div className="relative" ref={dropdownRef}>
          <Tooltip>
            <TooltipTrigger
              render={
                <Button
                  variant="ghost"
                  size="icon"
                  className="relative"
                  aria-label={
                    unreadCount > 0
                      ? `Notifications, ${unreadCount} unread`
                      : "Notifications"
                  }
                  aria-expanded={dropdownOpen}
                  onClick={() => setDropdownOpen((open) => !open)}
                />
              }
            >
              <Bell className="size-4" />
              {unreadCount > 0 ? (
                <span className="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-medium text-white">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              ) : null}
            </TooltipTrigger>
            <TooltipContent>Notifications</TooltipContent>
          </Tooltip>

          {dropdownOpen ? (
            <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-border bg-panel shadow-lg">
              <div className="border-b border-border px-3 py-2">
                <p className="text-sm font-semibold text-foreground">
                  Operator alerts
                </p>
                <p className="text-xs text-muted-foreground">
                  {unreadCount > 0
                    ? `${unreadCount} awaiting review`
                    : "No pending alerts"}
                </p>
              </div>
              <ul className="max-h-72 overflow-y-auto">
                {notifications.length === 0 ? (
                  <li className="px-3 py-4 text-sm text-muted-foreground">
                    No notifications yet.
                  </li>
                ) : (
                  notifications.map((notification) => (
                    <li
                      key={notification.id}
                      className="border-b border-border/60 last:border-b-0"
                    >
                      <div className="flex items-start gap-2 px-3 py-2.5">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-foreground">
                            {notification.title}
                          </p>
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {notification.camera_name ?? "Camera"} ·{" "}
                            {notification.location}
                          </p>
                          <p className="mt-1 text-xs text-slate-300">
                            {notification.message}
                          </p>
                          <Link
                            href={buildResponseHref({
                              video_id: notification.video_code,
                              analysis_id: notification.analysis_code,
                            })}
                            className="mt-2 inline-flex text-xs font-medium text-primary hover:underline"
                            onClick={() => setDropdownOpen(false)}
                          >
                            Review Incident
                          </Link>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label="Dismiss notification"
                          onClick={(event) => void handleDismiss(notification, event)}
                        >
                          <X className="size-3.5" />
                        </Button>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </div>
          ) : null}
        </div>

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
          render={<Link href="/monitor" />}
        >
          <Play data-icon="inline-start" className="size-3.5" />
          <span className="hidden sm:inline">Start Demo</span>
          <span className="sm:hidden">Demo</span>
        </Button>
      </div>
    </header>
  );
}
