"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Send, Sparkles } from "lucide-react";
import { api, type Citation } from "@/lib/api";
import { useUiStore } from "@/lib/store";
import { cn } from "@/lib/utils";

const modes = [
  { id: "research", label: "research" },
  { id: "review", label: "review" },
  { id: "gaps", label: "gaps" },
  { id: "experiment", label: "experiment" },
  { id: "novelty", label: "novelty" },
] as const;

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  status?: string;
};

export function AgentPanel({ projectId }: { projectId: string }) {
  const { agentMode, setAgentMode } = useUiStore();
  const [input, setInput] = useState("improve sam for medical imaging");
  const [messages, setMessages] = useState<Message[]>([]);
  const [running, setRunning] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const placeholder = useMemo(() => {
    if (agentMode === "gaps") return "find contradictions and open problems…";
    if (agentMode === "experiment") return "plan an experiment…";
    if (agentMode === "novelty") return "paste a proposal to score novelty…";
    if (agentMode === "review") return "synthesize a survey on…";
    return "ask callum to investigate…";
  }, [agentMode]);

  async function run() {
    if (!input.trim() || running) return;
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
    };
    const assistantId = crypto.randomUUID();
    setMessages((m) => [
      ...m,
      userMsg,
      { id: assistantId, role: "assistant", content: "", status: "planning" },
    ]);
    setInput("");
    setRunning(true);

    try {
      const res = await fetch(api.agentUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          message: userMsg.content,
          mode: agentMode,
          stream: true,
        }),
      });

      if (!res.ok || !res.body) throw new Error("agent stream failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let eventName = "message";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n");
        buffer = parts.pop() ?? "";

        for (const line of parts) {
          if (line.startsWith("event:")) {
            eventName = line.slice(6).trim();
            continue;
          }
          if (!line.startsWith("data:")) continue;
          const raw = line.slice(5).trim();
          if (!raw) continue;
          const data = JSON.parse(raw) as Record<string, unknown>;

          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id !== assistantId) return msg;
              if (eventName === "status") {
                return { ...msg, status: String((data as { detail?: string }).detail ?? "") };
              }
              if (eventName === "token") {
                return {
                  ...msg,
                  content: msg.content + String((data as { text?: string }).text ?? ""),
                  status: undefined,
                };
              }
              if (eventName === "citations") {
                return {
                  ...msg,
                  citations: (data as { citations?: Citation[] }).citations ?? [],
                };
              }
              if (eventName === "done") {
                return { ...msg, status: undefined };
              }
              return msg;
            })
          );
        }
      }
    } catch {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId
            ? {
                ...msg,
                content:
                  msg.content ||
                  "api offline — start the callum api on :8000 to stream live research.",
                status: undefined,
              }
            : msg
        )
      );
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="flex h-full min-w-0 flex-col border-l border-border bg-[#0a0a0c]/55">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-accent" />
          <span className="text-[13px] font-medium">agent</span>
        </div>
        <div className="flex gap-1 rounded-full bg-white/[0.03] p-1 ring-1 ring-border">
          {modes.map((mode) => (
            <button
              key={mode.id}
              onClick={() => setAgentMode(mode.id)}
              className={cn(
                "rounded-full px-2.5 py-1 text-[11px] transition",
                agentMode === mode.id
                  ? "bg-white/[0.08] text-ink"
                  : "text-faint hover:text-mute"
              )}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      <div ref={scroller} className="flex-1 space-y-4 overflow-auto px-4 py-4">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-[14px] border border-dashed border-border px-4 py-6 text-[13px] leading-relaxed text-mute"
          >
            callum will read your corpus, cite evidence with page anchors, and refuse
            weak claims instead of inventing sources.
          </motion.div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "rounded-[14px] px-3.5 py-3 text-[13px] leading-relaxed",
              msg.role === "user"
                ? "ml-8 bg-accent/15 text-ink"
                : "mr-2 border border-border bg-white/[0.025] text-ink"
            )}
          >
            {msg.status && (
              <div className="mb-2 flex items-center gap-2 text-[11px] text-accent">
                <Loader2 className="h-3 w-3 animate-spin" />
                {msg.status}
              </div>
            )}
            <div className="whitespace-pre-wrap">{msg.content}</div>
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-3 space-y-2 border-t border-border pt-3">
                <div className="text-[11px] uppercase tracking-[0.14em] text-faint">
                  citations
                </div>
                {msg.citations.map((c, i) => (
                  <div
                    key={`${c.title}-${i}`}
                    className="rounded-[10px] bg-black/20 px-3 py-2 text-[12px] text-mute"
                  >
                    <div className="text-ink">
                      {c.title}
                      {c.year ? ` (${c.year})` : ""}
                    </div>
                    <div className="mt-0.5">
                      {[c.paragraph, c.page != null ? `p.${c.page}` : null]
                        .filter(Boolean)
                        .join(" · ")}
                      {" · "}
                      confidence {(c.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="border-t border-border p-3">
        <div className="flex items-end gap-2 rounded-[14px] border border-border bg-white/[0.03] p-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void run();
              }
            }}
            rows={2}
            placeholder={placeholder}
            className="max-h-28 flex-1 resize-none bg-transparent px-2 py-1.5 text-[13px] outline-none placeholder:text-faint"
          />
          <button
            onClick={() => void run()}
            disabled={running}
            className="inline-flex h-9 w-9 items-center justify-center rounded-[10px] bg-white text-black transition hover:bg-white/90 disabled:opacity-50"
          >
            {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}
