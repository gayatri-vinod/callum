"use client";

import type { Document } from "@/lib/api";

export function PaperViewer({ document }: { document: Document | null }) {
  if (!document) {
    return (
      <div className="flex h-full items-center justify-center text-[13px] text-faint">
        select a document
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border px-6 py-4">
        <div className="text-[11px] uppercase tracking-[0.16em] text-faint">
          {document.modality} · {document.status}
        </div>
        <h2 className="mt-1 text-[22px] font-medium tracking-tight text-ink">
          {document.title || document.filename}
        </h2>
        <p className="mt-1 text-[13px] text-mute">
          {document.authors?.length ? document.authors.join(", ") : "authors pending extraction"}
          {document.meta?.year ? ` · ${String(document.meta.year)}` : ""}
        </p>
      </div>

      <div className="flex-1 overflow-auto px-6 py-6">
        <div className="mx-auto max-w-2xl">
          <div className="rounded-[16px] border border-border bg-white/[0.02] p-6 shadow-soft">
            <div className="mb-4 text-[11px] uppercase tracking-[0.16em] text-faint">abstract</div>
            <p className="text-[14px] leading-7 text-mute">
              {document.abstract ||
                "multimodal parse pending — figures, tables, equations, and references will land here."}
            </p>

            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              {["figures", "tables", "equations"].map((item) => (
                <div
                  key={item}
                  className="rounded-[12px] border border-border bg-black/20 px-3 py-4 text-center"
                >
                  <div className="text-[18px] font-medium text-ink">—</div>
                  <div className="mt-1 text-[11px] text-faint">{item}</div>
                </div>
              ))}
            </div>

            <div className="mt-8 rounded-[12px] border border-dashed border-border px-4 py-8 text-center text-[12px] text-faint">
              split-screen pdf canvas · highlights · citation anchors
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
