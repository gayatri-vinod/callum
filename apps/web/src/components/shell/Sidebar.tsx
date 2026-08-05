"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FolderKanban,
  GitBranch,
  Library,
  Search,
  Settings,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "workspace", icon: FolderKanban },
  { href: "/library", label: "library", icon: Library },
  { href: "/graph", label: "graph", icon: GitBranch },
  { href: "/search", label: "search", icon: Search },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-[220px] shrink-0 flex-col border-r border-border bg-[#0a0a0c]/80 px-3 py-4 backdrop-blur-xl">
      <Link href="/" className="group mb-8 flex items-center gap-2.5 px-2">
        <span className="relative flex h-7 w-7 items-center justify-center rounded-[9px] bg-white/[0.06] ring-1 ring-white/10">
          <Sparkles className="h-3.5 w-3.5 text-accent" strokeWidth={1.75} />
          <span className="absolute inset-0 rounded-[9px] bg-accent/20 opacity-0 blur-md transition group-hover:opacity-100" />
        </span>
        <div className="leading-tight">
          <div className="text-[15px] font-medium tracking-tight text-ink">callum</div>
          <div className="text-[11px] text-faint">research os</div>
        </div>
      </Link>

      <nav className="flex flex-1 flex-col gap-0.5">
        {nav.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/" || pathname.startsWith("/workspace")
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2.5 rounded-[10px] px-2.5 py-2 text-[13px] transition",
                active
                  ? "bg-white/[0.07] text-ink"
                  : "text-mute hover:bg-white/[0.04] hover:text-ink"
              )}
            >
              <Icon className="h-4 w-4 opacity-80" strokeWidth={1.6} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <Link
        href="/settings"
        className="mt-auto flex items-center gap-2.5 rounded-[10px] px-2.5 py-2 text-[13px] text-mute transition hover:bg-white/[0.04] hover:text-ink"
      >
        <Settings className="h-4 w-4" strokeWidth={1.6} />
        settings
      </Link>
    </aside>
  );
}
