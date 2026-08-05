export default function SettingsPage() {
  return (
    <div className="mx-auto w-full max-w-2xl px-6 py-10">
      <div className="mb-8">
        <div className="text-[11px] uppercase tracking-[0.16em] text-faint">settings</div>
        <h1 className="mt-1 text-[28px] font-medium tracking-tight">preferences</h1>
      </div>

      <div className="space-y-3">
        {[
          ["theme", "dark (macOS minimal)"],
          ["models", "openai / anthropic / ollama"],
          ["retrieval", "hybrid dense + bm25 + rerank"],
          ["citations", "require page-level evidence"],
          ["local-first", "ollama optional"],
        ].map(([label, value]) => (
          <div
            key={label}
            className="flex items-center justify-between rounded-[14px] border border-border bg-white/[0.025] px-4 py-3"
          >
            <span className="text-[13px] text-mute">{label}</span>
            <span className="text-[13px] text-ink">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
