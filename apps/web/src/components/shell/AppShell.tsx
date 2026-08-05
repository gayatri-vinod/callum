"use client";

import { Sidebar } from "@/components/shell/Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex h-dvh overflow-hidden bg-bg text-ink">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-24 top-[-10%] h-[48vh] w-[48vh] rounded-full bg-[radial-gradient(circle,rgba(59,158,255,0.14),transparent_65%)] blur-2xl" />
        <div className="absolute bottom-[-20%] right-[-10%] h-[55vh] w-[55vh] rounded-full bg-[radial-gradient(circle,rgba(255,255,255,0.05),transparent_60%)] blur-2xl" />
        <div className="noise absolute inset-0" />
      </div>
      <Sidebar />
      <main className="relative z-10 flex min-w-0 flex-1 flex-col">{children}</main>
    </div>
  );
}
