"use client";

import { useCallback, useId, useRef, useState } from "react";
import { FileVideo, UploadCloud, X } from "lucide-react";
import { toast } from "sonner";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError } from "@/lib/api/client";
import { uploadVideo } from "@/lib/api";
import type { Camera } from "@/types";
import type { ApiVideoUploadResponse } from "@/lib/api/types";
import { cn } from "cn";

const ACCEPTED_EXTENSIONS = [".mp4", ".mov", ".webm"];
const ACCEPTED_MIME = ["video/mp4", "video/quicktime", "video/webm"];
const MAX_SIZE_MB = 100;

interface VideoUploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  cameras: Camera[];
  defaultCameraId?: string;
  defaultLocation?: string;
  defaultScenario?: "person_down" | "ppe_compliance";
  onUploaded: (response: ApiVideoUploadResponse) => void;
}

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function validateClientFile(file: File): string | null {
  const lower = file.name.toLowerCase();
  const hasExt = ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
  if (!hasExt) {
    return "Unsupported format. Use MP4, MOV, or WebM.";
  }
  if (file.type && !ACCEPTED_MIME.includes(file.type)) {
    return "Unsupported MIME type for the selected file.";
  }
  if (file.size <= 0) {
    return "The selected file is empty.";
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `File exceeds the ${MAX_SIZE_MB} MB upload limit.`;
  }
  return null;
}

export function VideoUploadDialog({
  open,
  onOpenChange,
  cameras,
  defaultCameraId = "cam-04",
  defaultLocation = "Loading Zone B",
  defaultScenario = "person_down",
  onUploaded,
}: VideoUploadDialogProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [location, setLocation] = useState(defaultLocation);
  const [cameraId, setCameraId] = useState(defaultCameraId);
  const [scenario, setScenario] = useState<"person_down" | "ppe_compliance">(
    defaultScenario
  );
  const [ppeObservation, setPpeObservation] = useState<
    | "hard_hat_not_visible"
    | "high_visibility_vest_not_visible"
    | "both_not_visible"
  >("hard_hat_not_visible");
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [formKey, setFormKey] = useState(0);

  const resetForm = useCallback(() => {
    setFile(null);
    setLocation(defaultLocation);
    setCameraId(defaultCameraId);
    setScenario(defaultScenario);
    setPpeObservation("hard_hat_not_visible");
    setError(null);
    setUploading(false);
    setDragOver(false);
    setFormKey((value) => value + 1);
  }, [defaultCameraId, defaultLocation, defaultScenario]);

  const handleOpenChange = (next: boolean) => {
    if (next) {
      resetForm();
    }
    onOpenChange(next);
  };

  const assignFile = useCallback((next: File | null) => {
    if (!next) {
      setFile(null);
      setError(null);
      return;
    }
    const validationError = validateClientFile(next);
    if (validationError) {
      setFile(null);
      setError(validationError);
      return;
    }
    setFile(next);
    setError(null);
  }, []);

  const handleUpload = async () => {
    if (!file || uploading) return;
    if (!location.trim()) {
      setError("Location is required.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const response = await uploadVideo({
        file,
        location: location.trim(),
        cameraId: cameraId || undefined,
        demoScenario: scenario,
        demoPpeObservation:
          scenario === "ppe_compliance" ? ppeObservation : undefined,
      });
      toast.success("Upload received. Preparing analysis…");
      onUploaded(response);
      onOpenChange(false);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Unable to upload video. Confirm the API is running.";
      setError(message);
      toast.error(message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg" key={formKey}>
        <DialogHeader>
          <DialogTitle>Upload and Prepare Analysis</DialogTitle>
          <DialogDescription>
            Upload a short workplace video. SafetyLens will extract metadata and
            evidence-candidate frames for Stage 4 AI verification.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div
            role="button"
            tabIndex={0}
            aria-label="Video drop zone"
            className={cn(
              "rounded-xl border border-dashed border-border bg-secondary/30 px-4 py-8 text-center transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              dragOver && "border-primary bg-primary/10"
            )}
            onDragOver={(event) => {
              event.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragOver(false);
              const dropped = event.dataTransfer.files?.[0] ?? null;
              assignFile(dropped);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                inputRef.current?.click();
              }
            }}
          >
            <UploadCloud className="mx-auto size-8 text-muted-foreground" aria-hidden="true" />
            <p className="mt-3 text-sm font-medium text-foreground">
              Drag and drop a video file
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              MP4, MOV, WebM · Max {MAX_SIZE_MB} MB · Prefer 10–30 seconds
            </p>
            <Button
              type="button"
              variant="outline"
              className="mt-4"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
            >
              Browse files
            </Button>
            <input
              id={inputId}
              ref={inputRef}
              type="file"
              accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
              className="sr-only"
              onChange={(event) => assignFile(event.target.files?.[0] ?? null)}
            />
          </div>

          {file ? (
            <div className="flex items-start gap-3 rounded-lg border border-border bg-panel px-3 py-2.5">
              <FileVideo className="mt-0.5 size-4 text-primary" aria-hidden="true" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{file.name}</p>
                <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
              </div>
              <Button
                type="button"
                size="icon-sm"
                variant="ghost"
                aria-label="Clear selected file"
                onClick={() => assignFile(null)}
                disabled={uploading}
              >
                <X className="size-3.5" />
              </Button>
            </div>
          ) : null}

          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Demo scenario
            </span>
            <Select
              value={scenario}
              onValueChange={(value) => {
                if (value === "person_down" || value === "ppe_compliance") {
                  setScenario(value);
                  if (value === "ppe_compliance") {
                    setCameraId("cam-04");
                    setLocation("Production Floor");
                  } else {
                    setCameraId("cam-03");
                    setLocation("Warehouse Aisle");
                  }
                }
              }}
              disabled={uploading}
            >
              <SelectTrigger className="w-full" aria-label="Select demo scenario">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="person_down">
                  Person-down demonstration
                </SelectItem>
                <SelectItem value="ppe_compliance">
                  PPE-compliance demonstration
                </SelectItem>
              </SelectContent>
            </Select>
          </label>

          {scenario === "ppe_compliance" ? (
            <label className="block space-y-1.5">
              <span className="text-xs font-medium text-muted-foreground">
                Configured PPE observation
              </span>
              <Select
                value={ppeObservation}
                onValueChange={(value) => {
                  if (
                    value === "hard_hat_not_visible" ||
                    value === "high_visibility_vest_not_visible" ||
                    value === "both_not_visible"
                  ) {
                    setPpeObservation(value);
                  }
                }}
                disabled={uploading}
              >
                <SelectTrigger className="w-full" aria-label="PPE observation">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hard_hat_not_visible">
                    Hard hat not visible
                  </SelectItem>
                  <SelectItem value="high_visibility_vest_not_visible">
                    High-visibility vest not visible
                  </SelectItem>
                  <SelectItem value="both_not_visible">
                    Both not visible
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-[11px] text-muted-foreground">
                Configured Demo Scenario — Demo AI does not independently discover missing PPE.
              </p>
            </label>
          ) : null}

          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">Location</span>
            <Input
              value={location}
              onChange={(event) => setLocation(event.target.value)}
              aria-label="Video location"
              disabled={uploading}
            />
          </label>

          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">Camera</span>
            <Select
              value={cameraId}
              onValueChange={(value) => {
                if (value) setCameraId(value);
              }}
              disabled={uploading}
            >
              <SelectTrigger className="w-full" aria-label="Select camera">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {cameras.map((camera) => (
                  <SelectItem key={camera.id} value={camera.id}>
                    {camera.name} — {camera.location}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>

          {error ? (
            <p className="text-sm text-red-300" role="alert">
              {error}
            </p>
          ) : null}

          {uploading ? (
            <p className="text-sm text-muted-foreground" aria-live="polite">
              Uploading… progress is indeterminate while the file transfers.
            </p>
          ) : null}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={uploading}
          >
            Cancel
          </Button>
          <Button onClick={() => void handleUpload()} disabled={!file || uploading}>
            {uploading ? "Uploading…" : "Upload and Prepare Analysis"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
