/**
 * Component: Frontend -> lib -> Chat send/stream orchestration hook
 * Belongs to: used by the Prism Chat page (app/chat/page.tsx) and any "Ask AI" button
 * elsewhere that jumps into chat.
 * Purpose: the client-side counterpart to the backend's SSE pipeline — sends a
 * question, creates the user + placeholder assistant messages in the chat store, and
 * updates that assistant message live as status/plan/token/done SSE events arrive from
 * lib/api.ts's streamChat.
 */

"use client";

import * as React from "react";

import { streamChat } from "@/lib/api";
import { uid, useChatStore } from "@/lib/store";
import type { Citation } from "@/lib/types";

export function useChat() {
  const store = useChatStore();
  const [busy, setBusy] = React.useState(false);
  const [status, setStatus] = React.useState<string | null>(null);

  // Sends a question: ensures a thread exists (creating one if needed), titles a fresh
  // thread from the first question, appends the user message and a streaming placeholder
  // assistant message, then consumes the SSE stream — appending each token to the
  // placeholder's content and, on the final "done" event, attaching citations/agents and
  // clearing the streaming flag. On any failure, marks the message as an error instead
  // of leaving it stuck mid-stream.
  const send = React.useCallback(
    async (question: string, existingThreadId?: string) => {
      if (!question.trim() || busy) return;
      let threadId = existingThreadId ?? useChatStore.getState().currentId;
      if (!threadId) threadId = useChatStore.getState().newThread();

      const state = useChatStore.getState();
      const thread = state.threads.find((t) => t.id === threadId);
      if (thread && thread.messages.length === 0) {
        state.setTitle(threadId, question.slice(0, 48));
      }

      state.addMessage(threadId, { id: uid(), role: "user", content: question });
      const assistantId = uid();
      state.addMessage(threadId, {
        id: assistantId,
        role: "assistant",
        content: "",
        streaming: true,
      });

      setBusy(true);
      setStatus("Analyzing…");
      let content = "";
      try {
        await streamChat(question, null, (ev) => {
          const patch = useChatStore.getState().patchMessage;
          if (ev.type === "status") setStatus("Analyzing…");
          else if (ev.type === "plan") {
            const plan = ev.plan as { agents: string[]; reasoning?: string; source?: string };
            setStatus(`Running: ${plan.agents.join(", ") || "synthesizer"}`);
            patch(threadId!, assistantId, { plan });
          } else if (ev.type === "synthesis_start") {
            setStatus("Composing answer…");
          } else if (ev.type === "token") {
            content += (ev.content as string) ?? "";
            patch(threadId!, assistantId, { content });
          } else if (ev.type === "done") {
            patch(threadId!, assistantId, {
              streaming: false,
              citations: (ev.citations as Citation[]) ?? [],
              agents: (ev.agents as string[]) ?? [],
            });
          }
        });
      } catch {
        useChatStore
          .getState()
          .patchMessage(threadId, assistantId, {
            streaming: false,
            error: true,
            content: content || "Sorry — the request failed. Please try again.",
          });
      } finally {
        setBusy(false);
        setStatus(null);
      }
    },
    [busy]
  );

  return { send, busy, status, store };
}
