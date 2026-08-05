"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUpRight, Plus, Sparkles } from "lucide-react";
import { api, type Project } from "@/lib/api";

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .projects()
      .then(setProjects)
      .catch(() =>
        setProjects([
          {
            id: "proj_sam_medical",
            name: "sam for medical imaging",
            description: "improve segment anything for clinical ct / mri workflows",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            document_count: 6,
            status: "active",
          },
        ])
      )
      .finally(() => setLoading(false));
  }, []);

  async function createProject(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const project = await api.createProject(name.trim());
      setProjects((prev) => [project, ...prev]);
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "could not create project");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <section className="relative flex min-h-[46vh] flex-col justify-end overflow-hidden border-b border-border px-8 pb-10 pt-16">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_20%_0%,rgba(59,158,255,0.16),transparent_50%),radial-gradient(ellipse_at_90%_40%,rgba(255,255,255,0.04),transparent_45%)]" />
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-10 max-w-2xl"
        >
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-white/[0.03] px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-mute">
            <Sparkles className="h-3 w-3 text-accent" />
            research operating system
          </div>
          <h1 className="text-[56px] font-medium leading-[0.95] tracking-[-0.04em] text-ink">
            callum
          </h1>
          <p className="mt-4 max-w-xl text-[16px] leading-relaxed text-mute">
            read, connect, critique, and extend scientific literature — not another
            chatbot.
          </p>
          <form onSubmit={createProject} className="mt-8 flex max-w-lg gap-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="new project name"
              className="h-11 flex-1 rounded-[12px] border border-border bg-white/[0.03] px-4 text-[14px] text-ink outline-none placeholder:text-faint focus:border-white/20"
            />
            <button
              type="submit"
              disabled={creating}
              className="inline-flex h-11 items-center gap-2 rounded-[12px] bg-white px-4 text-[13px] font-medium text-black transition hover:bg-white/90 disabled:opacity-60"
            >
              <Plus className="h-4 w-4" />
              create
            </button>
          </form>
          {error && <p className="mt-3 text-[12px] text-[var(--danger)]">{error}</p>}
        </motion.div>
      </section>

      <section className="flex-1 overflow-auto px-8 py-8">
        <div className="mb-4 flex items-end justify-between">
          <div>
            <h2 className="text-[13px] uppercase tracking-[0.16em] text-faint">projects</h2>
            <p className="mt-1 text-[14px] text-mute">pick up a research thread</p>
          </div>
        </div>

        {loading ? (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-36 animate-pulse rounded-[16px] bg-white/[0.03]" />
            ))}
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {projects.map((project, index) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * index, duration: 0.4 }}
              >
                <Link
                  href={`/workspace/${project.id}`}
                  className="group flex h-full flex-col rounded-[16px] border border-border bg-white/[0.025] p-5 transition hover:border-white/15 hover:bg-white/[0.04]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-[16px] font-medium tracking-tight text-ink">
                      {project.name}
                    </h3>
                    <ArrowUpRight className="h-4 w-4 text-faint transition group-hover:text-ink" />
                  </div>
                  <p className="mt-2 line-clamp-2 text-[13px] leading-relaxed text-mute">
                    {project.description || "no description yet"}
                  </p>
                  <div className="mt-auto flex items-center justify-between pt-6 text-[12px] text-faint">
                    <span>{project.document_count} documents</span>
                    <span>{project.status}</span>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
