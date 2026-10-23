"use client";

import * as React from "react";
import { Upload } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { storageApi } from "@/lib/endpoints";
import type { UploadedFile } from "@/lib/types";
import { formatBytes } from "@/lib/utils";
import { Button } from "./button";

const MAX_BYTES = 50 * 1024 * 1024;

/** Uploads one file to MinIO via POST /storage/upload and reports the resulting URL. */
export function FileUpload({
  bucket,
  accept,
  label,
  onUploaded,
}: {
  bucket: "materials" | "thumbnails";
  accept: string;
  label: string;
  onUploaded: (file: UploadedFile) => void;
}) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [busy, setBusy] = React.useState(false);
  const [last, setLast] = React.useState<UploadedFile | null>(null);

  async function handle(file: File) {
    if (file.size > MAX_BYTES) {
      toast.error("Tệp vượt quá 50 MB. Hãy chọn tệp nhỏ hơn.");
      return;
    }
    setBusy(true);
    try {
      const uploaded = await storageApi.upload(file, bucket);
      setLast(uploaded);
      onUploaded(uploaded);
      toast.success("Đã tải tệp lên");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="sr-only"
        tabIndex={-1}
        onChange={(e) => e.target.files?.[0] && handle(e.target.files[0])}
      />
      <Button type="button" variant="outline" size="sm" loading={busy} onClick={() => inputRef.current?.click()}>
        {!busy && <Upload />}
        {label}
      </Button>
      {last && (
        <span className="text-xs text-ink-muted">
          {last.filename}, {formatBytes(last.file_size)}
        </span>
      )}
    </div>
  );
}
