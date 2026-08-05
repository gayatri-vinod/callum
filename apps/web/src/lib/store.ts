"use client";

import { create } from "zustand";

type AgentMode = "research" | "review" | "gaps" | "experiment" | "novelty";

type UiState = {
  sidebarCollapsed: boolean;
  agentMode: AgentMode;
  selectedDocId: string | null;
  toggleSidebar: () => void;
  setAgentMode: (mode: AgentMode) => void;
  setSelectedDocId: (id: string | null) => void;
};

export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  agentMode: "research",
  selectedDocId: null,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setAgentMode: (agentMode) => set({ agentMode }),
  setSelectedDocId: (selectedDocId) => set({ selectedDocId }),
}));
