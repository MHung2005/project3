"use client";

import * as React from "react";
import { FileText, PlayCircle } from "lucide-react";
import type { LessonInput } from "@/lib/endpoints";
import type { Lesson, LessonType } from "@/lib/types";
import { cn, extractYoutubeId } from "@/lib/utils";
import { fetchYouTubeDuration } from "@/hooks/use-youtube-tracker";
import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { FileUpload } from "@/components/ui/file-upload";
import { Checkbox, Field, Input } from "@/components/ui/input";

export function LessonDialog({
  lesson,
  saving,
  onClose,
  onSave,
}: {
  lesson?: Lesson;
  saving: boolean;
  onClose: () => void;
  onSave: (input: LessonInput) => void;
}) {
  const [title, setTitle] = React.useState(lesson?.title ?? "");
  const [type, setType] = React.useState<LessonType>(lesson?.lesson_type ?? "VIDEO");
  const [videoUrl, setVideoUrl] = React.useState(lesson?.video_url ?? "");
  const [documentUrl, setDocumentUrl] = React.useState(lesson?.document_url ?? "");
  const [minutes, setMinutes] = React.useState(lesson ? String(Math.floor(lesson.duration_seconds / 60)) : "");
  const [seconds, setSeconds] = React.useState(lesson ? String(lesson.duration_seconds % 60) : "");
  const [preview, setPreview] = React.useState(lesson?.is_free_preview ?? false);
  const [detecting, setDetecting] = React.useState(false);
  const [durationNote, setDurationNote] = React.useState<string | null>(null);

  const videoId = videoUrl ? extractYoutubeId(videoUrl) : null;
  const duration = (Number(minutes) || 0) * 60 + (Number(seconds) || 0);

  async function detect(id: string) {
    setDetecting(true);
    setDurationNote(null);
    try {
      const d = await fetchYouTubeDuration(id);
      setMinutes(String(Math.floor(d / 60)));
      setSeconds(String(d % 60));
      setDurationNote("Đã lấy thời lượng từ YouTube.");
    } catch {
      setDurationNote("Không đọc được thời lượng. Hãy nhập tay.");
    } finally {
      setDetecting(false);
    }
  }

  const videoError = type === "VIDEO" && videoUrl && !videoId ? "Đường dẫn không phải video YouTube hợp lệ." : null;
  const valid =
    title.trim().length >= 2 && (type === "VIDEO" ? !!videoId : !!documentUrl);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!valid) return;
    onSave({
      title: title.trim(),
      lesson_type: type,
      video_url: type === "VIDEO" ? videoUrl.trim() : null,
      document_url: type === "DOCUMENT" ? documentUrl : null,
      duration_seconds: type === "VIDEO" ? duration : 0,
      is_free_preview: preview,
    });
  }

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent title={lesson ? "Sửa bài học" : "Thêm bài học"} className="max-w-xl">
        <form onSubmit={submit} className="space-y-5">
          <Field label="Tên bài học" htmlFor="l-title">
            <Input id="l-title" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
          </Field>

          <fieldset>
            <legend className="field-label">Loại bài học</legend>
            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  ["VIDEO", "Video YouTube", PlayCircle],
                  ["DOCUMENT", "Tài liệu", FileText],
                ] as const
              ).map(([value, label, Icon]) => (
                <label
                  key={value}
                  className={cn(
                    "flex cursor-pointer items-center gap-2 rounded border px-3 py-2.5 text-sm",
                    type === value ? "border-blue bg-blue-soft text-blue" : "border-line hover:border-blue/50",
                  )}
                >
                  <input
                    type="radio"
                    name="lesson-type"
                    className="sr-only"
                    checked={type === value}
                    onChange={() => setType(value)}
                  />
                  <Icon className="size-4" aria-hidden /> {label}
                </label>
              ))}
            </div>
          </fieldset>

          {type === "VIDEO" ? (
            <>
              <Field label="Đường dẫn YouTube" htmlFor="l-video" error={videoError}>
                <Input
                  id="l-video"
                  placeholder="https://www.youtube.com/watch?v=…"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  onBlur={() => videoId && !duration && detect(videoId)}
                />
              </Field>
              <div>
                <p className="field-label">Thời lượng</p>
                <div className="flex flex-wrap items-center gap-2">
                  <Input
                    aria-label="Phút"
                    inputMode="numeric"
                    className="w-20"
                    value={minutes}
                    onChange={(e) => setMinutes(e.target.value.replace(/\D/g, ""))}
                  />
                  <span className="text-sm text-ink-muted">phút</span>
                  <Input
                    aria-label="Giây"
                    inputMode="numeric"
                    className="w-20"
                    value={seconds}
                    onChange={(e) => setSeconds(e.target.value.replace(/\D/g, "").slice(0, 2))}
                  />
                  <span className="text-sm text-ink-muted">giây</span>
                  <Button type="button" variant="ghost" size="sm" disabled={!videoId} loading={detecting} onClick={() => videoId && detect(videoId)}>
                    Lấy từ YouTube
                  </Button>
                </div>
                <p className="mt-1.5 text-xs text-ink-muted">
                  {durationNote ?? "Học viên cần xem 80% thời lượng này để hoàn thành bài."}
                </p>
              </div>
            </>
          ) : (
            <div>
              <p className="field-label">Tệp tài liệu</p>
              <FileUpload
                bucket="materials"
                accept=".pdf,.doc,.docx,.ppt,.pptx,.zip"
                label={documentUrl ? "Thay tệp khác" : "Chọn tệp"}
                onUploaded={(f) => setDocumentUrl(f.file_url)}
              />
              <p className="mt-1.5 text-xs text-ink-muted">
                {documentUrl ? "Đã có tệp đính kèm." : "PDF, DOCX, PPTX hoặc ZIP, tối đa 50 MB."}
              </p>
            </div>
          )}

          <Checkbox
            label="Cho phép học thử (không cần đăng ký)"
            checked={preview}
            onChange={(e) => setPreview(e.target.checked)}
          />

          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Hủy
              </Button>
            </DialogClose>
            <Button type="submit" loading={saving} disabled={!valid}>
              {lesson ? "Lưu bài học" : "Thêm bài học"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
