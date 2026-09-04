/**
 * Component: Frontend -> app -> Prism Chat page (route "/chat")
 * Belongs to: the primary UI for the multi-agent chatbot — consumes lib/use-chat.ts and
 * lib/store.ts, and renders each assistant message with agent badges (from the
 * router's plan), streamed markdown, and expandable citations.
 * Purpose: a ChatGPT-style thread UI — a sidebar of past threads, a message list that
 * grows as SSE tokens arrive, starter suggestions on a fresh chat, and support for
 * arriving with a pre-filled question via ?q= (used by the Dashboard's quick-ask box
 * and other pages' "Ask AI" buttons).
 */

"use client";

import { MessageSquarePlus, Plus, Send, Sparkles, Trash2 } from "lucide-react";
import { useSearchParams } from "next/navigation";
import * as React from "react";

import { Citations } from "@/components/citations";
import { Markdown } from "@/components/markdown";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/lib/store";
import { useChat } from "@/lib/use-chat";
import { cn } from "@/lib/utils";

// Shown as clickable starter prompts on a fresh, empty chat.
const SUGGESTIONS = [
  "Analyze Reliance Industries as an investment",
  "Compare TCS and Infosys on profitability and valuation",
  "What's the latest news sentiment on HDFC Bank?",
  "Review my portfolio and flag concentration risk",
];

// Wrapped in Suspense below because useSearchParams() requires it under the App Router.
function ChatInner() {
  const params = useSearchParams();
  const { send, busy, status } = useChat();
  const threads = useChatStore((s) => s.threads);
  const currentId = useChatStore((s) => s.currentId);
  const setCurrent = useChatStore((s) => s.setCurrent);
  const newThread = useChatStore((s) => s.newThread);
  const deleteThread = useChatStore((s) => s.deleteThread);

  const [input, setInput] = React.useState("");
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const sentInitial = React.useRef(false);

  const current = threads.find((t) => t.id === currentId) ?? null;
  const messages = current?.messages ?? [];

  // Auto-sends a question arriving via ?q= (from the Dashboard's quick-ask or an "Ask
  // AI" button elsewhere) exactly once per page load.
  React.useEffect(() => {
    const q = params.get("q");
    if (q && !sentInitial.current) {
      sentInitial.current = true;
      send(q);
    }
  }, [params, send]);

  // Keeps the message list scrolled to the bottom as new content streams in.
  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || busy) return;
    const q = input;
    setInput("");
    send(q);
  }

  return (
    <div className="flex h-[calc(100dvh-6.5rem)] gap-4">
      <aside className="hidden w-56 shrink-0 flex-col md:flex">
        <Button size="sm" variant="outline" className="mb-3 w-full" onClick={() => newThread()}>
          <Plus className="h-4 w-4" /> New chat
        </Button>
        <div className="flex-1 space-y-1 overflow-y-auto">
          {threads.length === 0 && (
            <div className="px-2 py-4 text-center text-xs text-muted-foreground">
              No conversations yet
            </div>
          )}
          {threads.map((t) => (
            <button
              key={t.id}
              onClick={() => setCurrent(t.id)}
              className={cn(
                "group flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-xs",
                t.id === currentId ? "bg-muted" : "hover:bg-muted/50"
              )}
            >
              <MessageSquarePlus className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <span className="truncate">{t.title}</span>
              <Trash2
                className="ml-auto hidden h-3.5 w-3.5 shrink-0 text-muted-foreground hover:text-negative group-hover:block"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteThread(t.id);
                }}
              />
            </button>
          ))}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col rounded-lg border border-border bg-card">
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                <Sparkles className="h-6 w-6 text-primary" />
              </div>
              <div>
                <div className="text-lg font-semibold">Ask Prism anything</div>
                <div className="text-sm text-muted-foreground">
                  Multi-agent research across stocks, news, your portfolio, and documents.
                </div>
              </div>
              <div className="grid w-full max-w-lg gap-2 sm:grid-cols-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="rounded-lg border border-border bg-background p-3 text-left text-xs hover:border-primary/50 hover:bg-muted/50"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => (
              <div key={m.id} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
                <div
                  className={cn(
                    "max-w-[85%] rounded-lg px-4 py-2.5",
                    m.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted/50"
                  )}
                >
                  {m.role === "user" ? (
                    <div className="text-sm">{m.content}</div>
                  ) : (
                    <>
                      {/* Agent badges: which specialists the router selected for this turn. */}
                      {m.plan?.agents?.length ? (
                        <div className="mb-2 flex flex-wrap gap-1">
                          {m.plan.agents.map((a) => (
                            <Badge key={a} variant="outline" className="capitalize">
                              {a.replace(/_/g, " ")}
                            </Badge>
                          ))}
                        </div>
                      ) : null}
                      {m.content ? (
                        <Markdown>{m.content}</Markdown>
                      ) : (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                          {status ?? "Thinking…"}
                        </div>
                      )}
                      {m.streaming && m.content && (
                        <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-primary align-middle" />
                      )}
                      {m.citations && m.citations.length > 0 && <Citations citations={m.citations} />}
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        <form onSubmit={submit} className="border-t border-border p-3">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a stock, comparison, your portfolio, or documents…"
              disabled={busy}
              className="h-10 flex-1 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
            />
            <Button type="submit" size="lg" disabled={busy || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <React.Suspense fallback={<div className="p-6 text-sm text-muted-foreground">Loading…</div>}>
      <ChatInner />
    </React.Suspense>
  );
}
