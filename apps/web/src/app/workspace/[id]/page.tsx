"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Upload } from "lucide-react";
import { api, type Document, type Project } from "@/lib/api";
import { AgentPanel } from "@/components/workspace/AgentPanel";
import { LibraryRail } from "@/components/workspace/LibraryRail";
import { PaperViewer } from "@/components/workspace/PaperViewer";
import { useUiStore } from "@/lib/store";

export default function WorkspacePage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const { selectedDocId, setSelectedDocId } = useUiStore();
  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    Promise.all([api.project(projectId), api.documents(projectId)])
      .then(([p, docs]) => {
        setProject(p);
        setDocuments(docs);
        if (docs[0]) setSelectedDocId(docs[0].id);
      })
      .catch(() => {
        setProject({
          id: projectId,
          name: "sam for medical imaging",
          description: "offline demo project",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          document_count: 0,
          status: "active",
        });
      });
  }, [projectId, setSelectedDocId]);

  const selected = documents.find((d) => d.id === selectedDocId) ?? null;

  async function onUpload(fileList: FileList | null) {
    if (!fileList?.[0]) return;
    setUploading(true);
    try {
      const doc = await api.upload(projectId, fileList[0]);
      setDocuments((prev) => [doc, ...prev]);
      setSelectedDocId(doc.id);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-border px-5 py-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.16em] text-faint">workspace</div>
          <h1 className="text-[18px] font-medium tracking-tight">{project?.name ?? "loading…"}</h1>
        </div>
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-[11px] border border-border bg-white/[0.03] px-3 py-2 text-[12px] text-mute transition hover:bg-white/[0.06] hover:text-ink">
          <Upload className="h-3.5 w-3.5" />
          {uploading ? "uploading…" : "upload"}
          <input
            type="file"
            className="hidden"
            onChange={(e) => void onUpload(e.target.files)}
          />
        </label>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-[280px_minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <LibraryRail
          documents={documents}
          selectedId={selectedDocId}
          onSelect={setSelectedDocId}
        />
        <PaperViewer document={selected} />
        <AgentPanel projectId={projectId} />
      </div>
    </div>
  );
}
