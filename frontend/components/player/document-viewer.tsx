"use client";

import { CheckCircle2, Download } from "lucide-react";
import type { Lesson } from "@/lib/types";
import { Button } from "@/components/ui/button";

function extensionOf(url: string): string {
  try {
    return new URL(url).pathname.split(".").pop()?.toLowerCase() ?? "";
  } catch {
    return "";
  }
}

/** PDFs render inline; other formats (DOCX, PPTX, ZIP) are offered as a download. */
export function DocumentViewer({
  lesson,
  completed,
  completing,
  onComplete,
}: {
  lesson: Lesson;
  completed: boolean;
  completing: boolean;
  onComplete: () => void;
}) {
  if (!lesson.document_url) {
    return <p className="rounded-md border border-line p-6 text-sm text-ink-muted">Bài học chưa có tài liệu.</p>;
  }
  const ext = extensionOf(lesson.document_url);
  return (
    <div>
      {ext === "pdf" ? (
        <iframe
          src={lesson.document_url}
          title={lesson.title}
          className="h-[70vh] w-full rounded-md border border-line bg-paper-raised"
        />
      ) : (
        <div className="flex min-h-64 flex-col items-start justify-end gap-3 rounded-md border border-line bg-paper-sunk p-6">
          <p className="font-serif text-xl text-ink">Tài liệu {ext.toUpperCase()}</p>
          <p className="text-sm text-ink-muted">Tải về để đọc, sau đó quay lại đánh dấu hoàn thành.</p>
        </div>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button asChild variant="outline">
          <a href={lesson.document_url} target="_blank" rel="noreferrer">
            <Download /> Tải tài liệu
          </a>
        </Button>
        {completed ? (
          <span className="inline-flex items-center gap-1.5 text-sm text-blue">
            <CheckCircle2 className="size-4" aria-hidden /> Đã đọc xong
          </span>
        ) : (
          <Button loading={completing} onClick={onComplete}>
            Đánh dấu đã đọc xong
          </Button>
        )}
      </div>
      <p className="mt-2 text-xs text-ink-muted">Liên kết tài liệu có hiệu lực trong 60 phút. Tải lại trang nếu liên kết hết hạn.</p>
    </div>
  );
}
