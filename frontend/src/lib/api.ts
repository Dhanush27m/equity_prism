/**
 * Component: Frontend -> lib -> API client
 * Belongs to: imported by every hook in lib/hooks.ts and directly by lib/use-chat.ts.
 * Purpose: the single place that knows how to call the backend — builds the absolute
 * URL (NEXT_PUBLIC_API_BASE, since frontend and backend are on different origins),
 * attaches the X-Access-Key header from localStorage, and normalizes error handling
 * (including detecting a 401 and broadcasting a global "log out" event).
 */

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";
const ACCESS_KEY_STORAGE = "equity-prism-access-key";

// Turns a relative /api/... path into an absolute URL against the deployed backend.
export function apiUrl(path: string): string {
  return path.startsWith("/api") ? `${API_BASE}${path}` : path;
}

// Reads the access key the user entered at the gate (components/access-gate.tsx),
// stored in localStorage so it survives page reloads.
export function getAccessKey(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(ACCESS_KEY_STORAGE) ?? "";
}

// Sets or clears the stored access key.
export function setAccessKey(key: string): void {
  if (typeof window === "undefined") return;
  if (key) window.localStorage.setItem(ACCESS_KEY_STORAGE, key);
  else window.localStorage.removeItem(ACCESS_KEY_STORAGE);
}

// Attaches the X-Access-Key header (if one is stored) to a request's headers.
function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const key = getAccessKey();
  return key ? { ...extra, "X-Access-Key": key } : extra;
}

// Shared response handler: on 401 clears the stored key and fires a global event (the
// access gate listens for this to re-prompt), on any other non-OK status throws an
// ApiError with the backend's error detail, otherwise parses and returns the JSON body
// (or undefined for a 204 No Content).
async function handle<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    setAccessKey("");
    if (typeof window !== "undefined") window.dispatchEvent(new Event("equity-prism-unauthorized"));
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(apiUrl(path), { headers: authHeaders({ Accept: "application/json" }) });
  return handle<T>(res);
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return handle<T>(res);
}

export async function apiDelete<T>(path: string): Promise<T> {
  const res = await fetch(apiUrl(path), { method: "DELETE", headers: authHeaders() });
  return handle<T>(res);
}

// Multipart file upload (used for PDF documents) — no Content-Type header set so the
// browser fills in the correct multipart boundary itself.
export async function apiUpload<T>(path: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(apiUrl(path), { method: "POST", headers: authHeaders(), body: form });
  return handle<T>(res);
}

export type SSEEvent = Record<string, unknown> & { type: string };

// Drives the streaming chat request: POSTs the question, then reads the response body
// as a raw byte stream and manually parses Server-Sent-Events frames out of it
// (fetch's streaming body reader, not EventSource — needed since this is a POST with a
// body, which EventSource can't do), calling onEvent for each parsed event as it
// arrives. Buffers partial frames across chunk boundaries.
export async function streamChat(
  question: string,
  threadId: string | null,
  onEvent: (ev: SSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(apiUrl("/api/chat/stream"), {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ question, thread_id: threadId }),
    signal,
  });
  if (res.status === 401) {
    setAccessKey("");
    if (typeof window !== "undefined") window.dispatchEvent(new Event("equity-prism-unauthorized"));
  }
  if (!res.ok || !res.body) {
    throw new ApiError(res.status, "chat stream failed");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (!payload) continue;
      try {
        onEvent(JSON.parse(payload) as SSEEvent);
      } catch {
        /* ignore malformed */
      }
    }
  }
}
