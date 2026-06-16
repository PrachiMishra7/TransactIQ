"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Upload, History, Settings, Scissors,
  ChevronRight, Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/history", label: "History", icon: History },
  { href: "/chunking", label: "CSV Chunking", icon: Scissors },
  { href: "/rules", label: "Validation Rules", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col bg-slate-900 text-slate-300">
      <div className="flex items-center gap-3 border-b border-slate-800 px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600">
          <Zap className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white">TransactIQ</h1>
          <p className="text-xs text-slate-400">Data Quality Platform</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active ? "bg-indigo-600 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
              {active && <ChevronRight className="ml-auto h-4 w-4" />}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-800 p-4">
        <div className="rounded-lg bg-slate-800 p-3">
          <p className="text-xs font-medium text-slate-300">Enterprise Edition</p>
          <p className="mt-1 text-xs text-slate-500">AI-assisted validation & analytics</p>
        </div>
      </div>
    </aside>
  );
}

export function DashboardLayout({ children, title, description }: {
  children: React.ReactNode;
  title?: string;
  description?: string;
}) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <main className="ml-64 min-h-screen">
        {(title || description) && (
          <header className="border-b border-slate-200 bg-white px-8 py-6">
            {title && <h1 className="text-2xl font-bold text-slate-900">{title}</h1>}
            {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
          </header>
        )}
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
