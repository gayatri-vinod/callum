"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { api, type GraphPayload } from "@/lib/api";

const DEMO_PROJECT = "proj_sam_medical";

const typeColor: Record<string, string> = {
  paper: "#3b9eff",
  author: "#a78bfa",
  method: "#34c759",
  dataset: "#ff9f0a",
  model: "#64d2ff",
  institution: "#ff6482",
  task: "#ffd60a",
};

export default function GraphPage() {
  const [graph, setGraph] = useState<GraphPayload | null>(null);

  useEffect(() => {
    api
      .graph(DEMO_PROJECT)
      .then(setGraph)
      .catch(() =>
        setGraph({
          project_id: DEMO_PROJECT,
          nodes: [
            { id: "p_sam", label: "Segment Anything", type: "paper" },
            { id: "p_medsam", label: "MedSAM", type: "paper" },
            { id: "m_sam", label: "SAM", type: "model" },
            { id: "d_kits", label: "KiTS19", type: "dataset" },
          ],
          edges: [
            { id: "e1", source: "p_medsam", target: "p_sam", relation: "extends", weight: 1 },
            { id: "e2", source: "p_sam", target: "m_sam", relation: "introduced", weight: 1 },
            { id: "e3", source: "p_medsam", target: "d_kits", relation: "evaluated_on", weight: 1 },
          ],
        })
      );
  }, []);

  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [] as Node[], edges: [] as Edge[] };
    const nodes: Node[] = graph.nodes.map((n, i) => ({
      id: n.id,
      position: {
        x: 120 + (i % 4) * 220,
        y: 80 + Math.floor(i / 4) * 160,
      },
      data: { label: n.label },
      style: {
        background: "#121214",
        color: "#f4f4f5",
        border: `1px solid ${typeColor[n.type] ?? "#3b9eff"}55`,
        borderRadius: 12,
        fontSize: 12,
        padding: "8px 12px",
        boxShadow: `0 0 24px ${typeColor[n.type] ?? "#3b9eff"}22`,
      },
    }));
    const edges: Edge[] = graph.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.relation.replaceAll("_", " "),
      style: { stroke: "rgba(255,255,255,0.25)" },
      labelStyle: { fill: "#8b8b93", fontSize: 10 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "rgba(255,255,255,0.35)" },
    }));
    return { nodes, edges };
  }, [graph]);

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-border px-6 py-4">
        <div className="text-[11px] uppercase tracking-[0.16em] text-faint">knowledge graph</div>
        <h1 className="text-[22px] font-medium tracking-tight">research topology</h1>
        <p className="mt-1 text-[13px] text-mute">
          papers, methods, datasets, and influence edges — explore evolution visually.
        </p>
      </header>
      <div className="min-h-0 flex-1">
        <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
          <Background color="#2a2a2e" gap={22} size={1} />
          <MiniMap
            pannable
            zoomable
            maskColor="rgba(0,0,0,0.7)"
            nodeColor="#3b9eff"
            style={{ background: "#0e0e10", borderRadius: 12 }}
          />
          <Controls
            showInteractive={false}
            style={{ borderRadius: 12, overflow: "hidden", border: "1px solid rgba(255,255,255,0.08)" }}
          />
        </ReactFlow>
      </div>
    </div>
  );
}
