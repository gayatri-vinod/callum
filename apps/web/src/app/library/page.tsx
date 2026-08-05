"use client";

import { useEffect, useState } from "react";
import { api, type Document } from "@/lib/api";
import { formatBytes } from "@/lib/utils";

export default function LibraryPage() {
  const [documents, setDocuments] = useState<Document[]>([]);

  useEffect(() => {
    api
      .documents("proj_sam_medical")
      .then(setDocuments)
      .catch(() => setDocuments([]));
  }, []);

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-10">
      <div className="mb-8">
        <div className="text-[11px] uppercase tracking-[0.16em] text-faint">library</div>
        <h1 className="mt-1 text-[28px] font-medium tracking-tight">all sources</h1>
        <p className="mt-2 text-[14px] text-mute">
          pdfs, notes, slides, audio, datasets — one multimodal corpus.
        </p>
      </div>

      <div className="overflow-hidden rounded-[16px] border border-border">
        <table className="w-full text-left text-[13px]">
          <thead className="bg-white/[0.03] text-[11px] uppercase tracking-[0.14em] text-faint">
            <tr>
              <th className="px-4 py-3 font-medium">title</th>
              <th className="px-4 py-3 font-medium">modality</th>
              <th className="px-4 py-3 font-medium">status</th>
              <th className="px-4 py-3 font-medium">size</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id} className="border-t border-border hover:bg-white/[0.02]">
                <td className="px-4 py-3 text-ink">{doc.title || doc.filename}</td>
                <td className="px-4 py-3 text-mute">{doc.modality}</td>
                <td className="px-4 py-3 text-mute">{doc.status}</td>
                <td className="px-4 py-3 text-mute">{formatBytes(doc.size_bytes)}</td>
              </tr>
            ))}
            {documents.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-faint">
                  no documents yet — open a workspace and upload
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
