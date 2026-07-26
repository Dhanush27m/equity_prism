"use client";

import { FileText, Send, Sparkles, Trash2, Upload } from "lucide-react";
import * as React from "react";

import { Citations } from "@/components/citations";
import { Markdown } from "@/components/markdown";
import { EmptyState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { streamChat, type SSEEvent } from "@/lib/api";
import { useDeleteDocument, useDocuments, useUploadDocument } from "@/lib/hooks";
import type { Citation, DocumentItem } from "@/lib/types";
import { cn, formatRelativeTime } from "@/lib/utils";

function statusBadge(status: DocumentItem["status"]) {
  switch (status) {
    case "ready":
      return <Badge variant="positive">Ready</Badge>;
    case "failed":
      return <Badge variant="negative">Failed</Badge>;
    case "processing":
      return (
        <Badge variant="warning">
          <Spinner className="h-3 w-3" /> Processing
        </Badge>
      );
    default:
      return <Badge variant="neutral">Pending</Badge>;
  }
}

function Dropzone() {
  const upload = useUploadDocument();
  const [drag, setDrag] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  function handleFiles(files: FileList | null) {
    if (!files?.length) return;
    const file = files[0];
    if (!file.name.toLowerCase().endsWith(".pdf")) return;
    upload.mutate(file);
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors",
        drag ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      {upload.isPending ? (
        <>
          <Spinner className="h-6 w-6" />
          <div className="text-sm">Uploading…</div>
        </>
      ) : (
        <>
          <Upload className="h-6 w-6 text-muted-foreground" />
          <div className="text-sm font-medium">Drop a PDF here or click to upload</div>
          <div className="text-xs text-muted-foreground">Annual reports, filings, research notes</div>
        </>
      )}
      {upload.isError && (
        <div className="text-xs text-negative">Upload failed. PDF only, up to 30 MB.</div>
      )}
    </div>
  );
}

function DocQA({ ready }: { ready: boolean }) {
  const [input, setInput] = React.useState("");
  const [answer, setAnswer] = React.useState("");
  const [citations, setCitations] = React.useState<Citation[]>([]);
  const [busy, setBusy] = React.useState(false);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || busy) return;
    const q = input;
    setInput("");
    setBusy(true);
    setAnswer("");
    setCitations([]);
    let content = "";
    try {
      await streamChat(q, null, (ev: SSEEvent) => {
        if (ev.type === "token") {
          content += (ev.content as string) ?? "";
          setAnswer(content);
        } else if (ev.type === "done") {
          setCitations((ev.citations as Citation[]) ?? []);
        }
      });
    } catch {
      setAnswer("Query failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" /> Ask your documents
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <form onSubmit={ask} className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!ready || busy}
            placeholder={
              ready ? "e.g. What were the key risks in the annual report?" : "Upload a document first…"
            }
            className="h-9 flex-1 rounded-md border border-input bg-card px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
          />
          <Button type="submit" size="md" disabled={!ready || busy || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
        {(answer || busy) && (
          <div className="rounded-md border border-border bg-muted/30 p-3">
            {answer ? (
              <Markdown>{answer}</Markdown>
            ) : (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className="h-2 w-2 animate-pulse rounded-full bg-primary" /> Searching documents…
              </div>
            )}
            {citations.length > 0 && <Citations citations={citations} />}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function DocumentsPage() {
  const { data } = useDocuments(true);
  const del = useDeleteDocument();
  const docs = data?.documents ?? [];
  const anyReady = docs.some((d) => d.status === "ready");

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Documents</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Upload PDFs and ask questions answered with citations (RAG)
        </p>
      </div>

      <Dropzone />

      <Card>
        <CardHeader>
          <CardTitle>Your documents</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {docs.length === 0 ? (
            <EmptyState title="No documents yet" hint="Upload a PDF to get started." icon={<FileText className="h-8 w-8" />} />
          ) : (
            <div className="space-y-2">
              {docs.map((d) => (
                <div
                  key={d.id}
                  className="flex items-center gap-3 rounded-md border border-border p-3"
                >
                  <FileText className="h-5 w-5 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{d.filename}</div>
                    <div className="text-xs text-muted-foreground">
                      {d.status === "ready" && `${d.num_pages ?? 0} pages · ${d.num_chunks} chunks · `}
                      {d.status === "failed" && d.error ? `${d.error} · ` : ""}
                      {formatRelativeTime(d.created_at)}
                    </div>
                  </div>
                  {statusBadge(d.status)}
                  <button
                    onClick={() => del.mutate(d.id)}
                    className="text-muted-foreground hover:text-negative"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <DocQA ready={anyReady} />
    </div>
  );
}
