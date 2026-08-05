"use client";

import { FileText, Image as ImageIcon, Mic, Table2 } from "lucide-react";
import type { Document } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";

function modalityIcon(modality: string) {
  if (modality === "image") return ImageIcon;
  if (modality === "audio" || modality === "video") return Mic;
  if (modality === "dataset") return Table2;
  return FileText;
}

export function LibraryRail({
  documents,
  selectedId,
  onSelect,
}: {
  documents: Document[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex h-full w-[280px] shrink-0 flex-col border-r border-border bg-[#0a0a0c]/40">
      <div className="border-b border-border px-4 py-3">
        <div className="text-[13px] font-medium">corpus</div>
        <div className="text-[11px] text-faint">{documents.length} sources</div>
      </div>
      <div className="flex-1 space-y-1 overflow-auto p-2">
        {documents.map((doc) => {
          const Icon = modalityIcon(doc.modality);
          const active = selectedId === doc.id;
          return (
            <button
              key={doc.id}
              onClick={() => onSelect(doc.id)}
              className={cn(
                "flex w-full items-start gap-3 rounded-[12px] px-3 py-2.5 text-left transition",
                active ? "bg-white/[0.07]" : "hover:bg-white/[0.04]"
              )}
            >
              <Icon className="mt-0.5 h-4 w-4 shrink-0 text-mute" strokeWidth={1.6} />
              <div className="min-w-0">
                <div className="truncate text-[13px] text-ink">{doc.title || doc.filename}</div>
                <div className="mt-0.5 truncate text-[11px] text-faint">
                  {doc.authors?.[0] || doc.modality} · {formatBytes(doc.size_bytes)}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
