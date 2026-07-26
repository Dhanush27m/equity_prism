import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Citation } from "./types";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  agents?: string[];
  plan?: { agents: string[]; reasoning?: string; source?: string };
  streaming?: boolean;
  error?: boolean;
}

export interface ChatThread {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
}

interface ChatState {
  threads: ChatThread[];
  currentId: string | null;
  newThread: () => string;
  setCurrent: (id: string) => void;
  deleteThread: (id: string) => void;
  addMessage: (threadId: string, msg: ChatMessage) => void;
  patchMessage: (threadId: string, msgId: string, patch: Partial<ChatMessage>) => void;
  setTitle: (threadId: string, title: string) => void;
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10);
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      threads: [],
      currentId: null,
      newThread: () => {
        const id = uid();
        const thread: ChatThread = { id, title: "New chat", messages: [], createdAt: Date.now() };
        set((s) => ({ threads: [thread, ...s.threads], currentId: id }));
        return id;
      },
      setCurrent: (id) => set({ currentId: id }),
      deleteThread: (id) =>
        set((s) => {
          const threads = s.threads.filter((t) => t.id !== id);
          const currentId = s.currentId === id ? (threads[0]?.id ?? null) : s.currentId;
          return { threads, currentId };
        }),
      addMessage: (threadId, msg) =>
        set((s) => ({
          threads: s.threads.map((t) =>
            t.id === threadId ? { ...t, messages: [...t.messages, msg] } : t
          ),
        })),
      patchMessage: (threadId, msgId, patch) =>
        set((s) => ({
          threads: s.threads.map((t) =>
            t.id === threadId
              ? {
                  ...t,
                  messages: t.messages.map((m) => (m.id === msgId ? { ...m, ...patch } : m)),
                }
              : t
          ),
        })),
      setTitle: (threadId, title) =>
        set((s) => ({
          threads: s.threads.map((t) => (t.id === threadId ? { ...t, title } : t)),
        })),
    }),
    { name: "equity-prism-chat" }
  )
);

export { uid };
