"use client";

import { useState } from "react";
import { Search as SearchIcon } from "lucide-react";
import { api, type SearchHit } from "@/lib/api";

export default function SearchPage() {
  const [query, setQuery] = useState("medical segmentation");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);

  async function runSearch(e?: React.FormEvent) {
    e?.preventDefault();
    setLoading(true);
    try {
      const results = await api.search(query, "proj_sam_medical");
      setHits(results);
    } catch {
      setHits([
        {
          id: "offline-1",
          title: "MedSAM",
          snippet: "start the api to run hybrid dense + bm25 + rerank search.",
          score: 0.8,
          modality: "pdf",
          year: 2024,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col px-6 py-10">
      <div className="mb-8">
        <div className="text-[11px] uppercase tracking-[0.16em] text-faint">advanced search</div>
        <h1 className="mt-1 text-[28px] font-medium tracking-tight">find anything</h1>
        <p className="mt-2 text-[14px] text-mute">
          natural language, sections, tables, figures, authors, years — hybrid retrieval.
        </p>
      </div>

      <form onSubmit={runSearch} className="relative mb-8">
        <SearchIcon className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-faint" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="h-12 w-full rounded-[14px] border border-border bg-white/[0.03] pl-11 pr-28 text-[14px] outline-none placeholder:text-faint focus:border-white/20"
          placeholder="equations, figures, methods, datasets…"
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-[10px] bg-white px-3 py-1.5 text-[12px] font-medium text-black"
        >
          {loading ? "…" : "search"}
        </button>
      </form>

      <div className="space-y-3 overflow-auto pb-10">
        {hits.map((hit) => (
          <div
            key={hit.id}
            className="rounded-[14px] border border-border bg-white/[0.025] px-4 py-3 transition hover:bg-white/[0.04]"
          >
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-[15px] font-medium">{hit.title}</h3>
              <span className="text-[11px] text-faint">{(hit.score * 100).toFixed(0)}%</span>
            </div>
            <p className="mt-1 text-[13px] text-mute">{hit.snippet}</p>
            <div className="mt-2 text-[11px] text-faint">
              {hit.modality}
              {hit.year ? ` · ${hit.year}` : ""}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
