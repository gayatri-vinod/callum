const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Project = {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  document_count: number;
  status: string;
};

export type Document = {
  id: string;
  project_id: string;
  filename: string;
  modality: string;
  size_bytes: number;
  status: string;
  title?: string | null;
  authors: string[];
  abstract?: string | null;
  meta: Record<string, unknown>;
};

export type SearchHit = {
  id: string;
  title: string;
  snippet: string;
  score: number;
  modality: string;
  year?: number | null;
};

export type GraphPayload = {
  project_id: string;
  nodes: { id: string; label: string; type: string; meta?: Record<string, unknown> }[];
  edges: { id: string; source: string; target: string; relation: string; weight: number }[];
};

export type Citation = {
  paper_id?: string | null;
  title: string;
  authors: string[];
  year?: number | null;
  page?: number | null;
  paragraph?: string | null;
  confidence: number;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  projects: () => request<Project[]>("/api/projects"),
  createProject: (name: string, description = "") =>
    request<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
  project: (id: string) => request<Project>(`/api/projects/${id}`),
  documents: (projectId: string) =>
    request<Document[]>(`/api/projects/${projectId}/documents`),
  search: (query: string, projectId?: string) =>
    request<SearchHit[]>("/api/search", {
      method: "POST",
      body: JSON.stringify({ query, project_id: projectId, limit: 20 }),
    }),
  graph: (projectId: string) => request<GraphPayload>(`/api/graph/${projectId}`),
  upload: async (projectId: string, file: File) => {
    const form = new FormData();
    form.append("project_id", projectId);
    form.append("file", file);
    return request<Document>("/api/upload", { method: "POST", body: form });
  },
  agentUrl: `${API_BASE}/api/agent/run`,
};
