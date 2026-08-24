"use client";

import { useEffect, useState } from "react";
import { FileSearch, Loader2 } from "lucide-react";
import { api, type Document, type DocumentExtraction } from "@/lib/api";

export function PaperViewer({ document }: { document: Document | null }) {
  const [extraction, setExtraction] = useState<DocumentExtraction | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setExtraction(null);
    if (!document || document.status !== "ready") return;
    setLoading(true);
    api
      .extraction(document.project_id, document.id)
      .then(setExtraction)
      .catch(() => setExtraction(null))
      .finally(() => setLoading(false));
  }, [document]);

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

            <div className="mt-8 grid gap-3 sm:grid-cols-4">
              {[
                ["pages", extraction?.pages.length],
                ["chunks", extraction?.chunks.length],
                ["figures", extraction?.assets.filter((asset) => asset.kind === "figure").length],
                ["references", extraction?.references.length],
              ].map(([item, count]) => (
                <div
                  key={String(item)}
                  className="rounded-[12px] border border-border bg-black/20 px-3 py-4 text-center"
                >
                  <div className="text-[18px] font-medium text-ink">
                    {loading ? "…" : (count ?? "—")}
                  </div>
                  <div className="mt-1 text-[11px] text-faint">{item}</div>
                </div>
              ))}
            </div>

            {loading && (
              <div className="mt-8 flex items-center justify-center gap-2 rounded-[12px] border border-dashed border-border px-4 py-8 text-[12px] text-faint">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                loading extraction
              </div>
            )}

            {!loading && extraction?.pages.length === 0 && (
              <div className="mt-8 flex items-center justify-center gap-2 rounded-[12px] border border-dashed border-border px-4 py-8 text-center text-[12px] text-faint">
                <FileSearch className="h-4 w-4" />
                no extraction yet — re-ingest this source to create page anchors
              </div>
            )}

            {extraction?.assets.length ? (
              <div className="mt-8">
                <div className="mb-3 text-[11px] uppercase tracking-[0.16em] text-faint">
                  extracted figures
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {extraction.assets.slice(0, 4).map((asset) => (
                    <figure
                      key={asset.id}
                      className="overflow-hidden rounded-[12px] border border-border bg-white"
                    >
                      {/* API URL is trusted local object content. */}
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={api.assetContentUrl(asset.id)}
                        alt={`figure from page ${asset.page_number ?? "unknown"}`}
                        className="h-32 w-full object-contain"
                      />
                      <figcaption className="bg-black px-2 py-1 text-[10px] text-faint">
                        page {asset.page_number ?? "—"}
                      </figcaption>
                    </figure>
                  ))}
                </div>
              </div>
            ) : null}

            {extraction?.pages.map((page) => (
              <section key={page.id} className="mt-8 border-t border-border pt-6">
                <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-faint">
                  <span>page {page.page_number}</span>
                  <span>{String(page.meta.word_count ?? 0)} words</span>
                </div>
                <p className="whitespace-pre-wrap text-[13px] leading-6 text-mute">
                  {page.text || "no extractable text"}
                </p>
              </section>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
