"use client";

import { useState } from "react";
import { FileText, Upload } from "lucide-react";
import { toast } from "sonner";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ApiError } from "@/lib/api/client";
import { fetchProcedureChunks, uploadProcedure } from "@/lib/api";
import type { ApiProcedureChunk } from "@/lib/api/types";
import type { SafetyProcedure } from "@/types";

interface ProcedureCardProps {
  procedure: SafetyProcedure;
  className?: string;
  compact?: boolean;
}

export function ProcedureCard({
  procedure,
  className,
  compact = false,
}: ProcedureCardProps) {
  const [open, setOpen] = useState(false);
  const [chunks, setChunks] = useState<ApiProcedureChunk[]>([]);
  const [chunkError, setChunkError] = useState<string | null>(null);
  const [loadingChunks, setLoadingChunks] = useState(false);

  async function openDetail() {
    setOpen(true);
    setLoadingChunks(true);
    setChunkError(null);
    try {
      const response = await fetchProcedureChunks(
        procedure.procedureCode ?? procedure.id
      );
      setChunks(response.data);
    } catch (err) {
      setChunkError(
        err instanceof Error ? err.message : "Unable to load procedure chunks."
      );
    } finally {
      setLoadingChunks(false);
    }
  }

  return (
    <>
      <article
        className={cn(
          "flex h-full flex-col rounded-xl border border-border bg-panel p-4 shadow-sm transition hover:border-border/80 hover:bg-panel-elevated",
          className
        )}
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="rounded-lg border border-border bg-secondary p-2.5 text-primary">
            <FileText className="size-4" aria-hidden="true" />
          </div>
          <span className="rounded-md border border-border bg-secondary px-2 py-1 text-[11px] text-muted-foreground">
            {procedure.category}
          </span>
        </div>

        <h3 className="text-base font-semibold text-foreground">{procedure.title}</h3>
        <p className="mt-1 text-xs font-medium text-primary">{procedure.section}</p>
        <p className="mt-2 text-sm text-muted-foreground">{procedure.description}</p>
        {procedure.isSample ? (
          <p className="mt-2 text-[11px] text-amber-100/90">
            Sample company procedure — not legal advice.
          </p>
        ) : null}

        {!compact ? (
          <ol className="mt-4 space-y-1.5 text-sm text-slate-300">
            {procedure.steps.slice(0, 3).map((step, index) => (
              <li key={`${procedure.id}-${index}`} className="flex gap-2">
                <span className="text-muted-foreground">{index + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
            {procedure.steps.length > 3 ? (
              <li className="text-xs text-muted-foreground">
                +{procedure.steps.length - 3} more steps
              </li>
            ) : null}
          </ol>
        ) : null}

        <div className="mt-auto flex items-center justify-between gap-3 pt-4 text-xs text-muted-foreground">
          <span>
            {procedure.sourceFormat ?? "library"} · {procedure.chunkCount ?? 0} chunks
          </span>
          <Button size="sm" variant="ghost" onClick={() => void openDetail()}>
            Open
          </Button>
        </div>
      </article>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{procedure.title}</DialogTitle>
            <DialogDescription>
              {procedure.section}
              {procedure.sourceFilename ? ` · source ${procedure.sourceFilename}` : ""}
            </DialogDescription>
          </DialogHeader>
          {loadingChunks ? (
            <p className="text-sm text-muted-foreground">Loading stored chunks…</p>
          ) : null}
          {chunkError ? (
            <p className="text-sm text-red-300" role="alert">
              {chunkError}
            </p>
          ) : null}
          {!loadingChunks && !chunkError ? (
            <ul className="space-y-3">
              {chunks.map((chunk) => (
                <li
                  key={chunk.id}
                  className="rounded-lg border border-border bg-secondary/30 p-3 text-sm"
                >
                  <div className="mb-1 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                    <span>{chunk.chunk_code}</span>
                    {chunk.section_heading ? <span>{chunk.section_heading}</span> : null}
                    {chunk.page_number != null ? <span>p.{chunk.page_number}</span> : null}
                  </div>
                  <p className="whitespace-pre-wrap text-slate-200">{chunk.content}</p>
                </li>
              ))}
              {chunks.length === 0 ? (
                <li className="text-sm text-muted-foreground">No stored chunks.</li>
              ) : null}
            </ul>
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
}

interface ProcedureUploadButtonProps {
  className?: string;
  onUploaded?: () => void;
}

export function ProcedureUploadButton({
  className,
  onUploaded,
}: ProcedureUploadButtonProps) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [procedureCode, setProcedureCode] = useState("");
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("Emergency Response");
  const [version, setVersion] = useState("1.0");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload() {
    if (!file || !procedureCode.trim() || !title.trim()) {
      setError("File, procedure code, and title are required.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const result = await uploadProcedure({
        file,
        procedureCode: procedureCode.trim(),
        title: title.trim(),
        category: category.trim() || "General",
        version: version.trim() || "1.0",
        isSample: true,
      });
      toast.success(result.message);
      setOpen(false);
      setFile(null);
      setProcedureCode("");
      setTitle("");
      onUploaded?.();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Upload failed."
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <>
      <Button className={className} onClick={() => setOpen(true)}>
        <Upload data-icon="inline-start" />
        Upload Procedure
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Upload company procedure</DialogTitle>
            <DialogDescription>
              Supported: PDF, TXT, Markdown. Max size configured on the API
              (default 10 MB). Sample uploads are labeled as demonstration text.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <label className="block space-y-1 text-xs text-muted-foreground">
              File
              <Input
                type="file"
                accept=".pdf,.txt,.md,.markdown,text/plain,text/markdown,application/pdf"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>
            <label className="block space-y-1 text-xs text-muted-foreground">
              Procedure code
              <Input
                value={procedureCode}
                onChange={(event) => setProcedureCode(event.target.value)}
                placeholder="SOP-EXAMPLE-1.0"
              />
            </label>
            <label className="block space-y-1 text-xs text-muted-foreground">
              Title
              <Input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Procedure title"
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block space-y-1 text-xs text-muted-foreground">
                Category
                <Input
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                />
              </label>
              <label className="block space-y-1 text-xs text-muted-foreground">
                Version
                <Input
                  value={version}
                  onChange={(event) => setVersion(event.target.value)}
                />
              </label>
            </div>
            {error ? (
              <p className="text-xs text-red-300" role="alert">
                {error}
              </p>
            ) : null}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)} disabled={uploading}>
              Cancel
            </Button>
            <Button onClick={() => void handleUpload()} disabled={uploading}>
              {uploading ? "Uploading…" : "Upload"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
