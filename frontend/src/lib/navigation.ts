import {
  LayoutDashboard,
  Monitor,
  AlertTriangle,
  FileText,
  BarChart3,
  Settings,
  Clapperboard,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
}

export const navigationItems: NavItem[] = [
  { title: "Overview", href: "/", icon: LayoutDashboard },
  { title: "Live Monitor", href: "/monitor", icon: Monitor },
  { title: "Incidents", href: "/incidents", icon: AlertTriangle },
  { title: "Procedures", href: "/procedures", icon: FileText },
  { title: "Reports", href: "/reports", icon: BarChart3 },
  { title: "Demo Guide", href: "/demo-help", icon: Clapperboard },
  { title: "Settings", href: "/settings", icon: Settings },
];

export function getPageTitle(pathname: string): string {
  if (pathname === "/") {
    return "Overview";
  }
  if (pathname.startsWith("/response")) {
    return "Incident Command";
  }

  const match = navigationItems.find((item) => item.href === pathname);
  return match?.title ?? "SafetyLens";
}
