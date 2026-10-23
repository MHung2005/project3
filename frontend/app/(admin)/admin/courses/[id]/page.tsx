"use client";

import * as React from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ExternalLink, FileText, PlayCircle } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { adminApi, learnApi } from "@/lib/endpoints";
import type { Lesson } from "@/lib/types";
import { formatDateTime, formatDuration } from "@/lib/utils";
import { CourseCover } from "@/components/course/course-card";
import { Button } from "@/components/ui/button";
import { ConfirmDialog, Dialog, DialogClose, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { Field, Textarea } from "@/components/ui/input";
import { Avatar, ErrorNote, Spinner, StatusBadge } from "@/components/ui/misc";

export default function AdminCourseReviewPage({ params }: { params: { id: string } }) {
  const courseId = Number(params.id);
  const qc = useQueryClient();
  const course = useQuery({ queryKey: ["admin-course", courseId], queryFn: () => adminApi.course(courseId) });
  const [approveOpen, setApproveOpen] = React.useState(false);
  const [rejectOpen, setRejectOpen] = React.useState(false);
  const [reason, setReason] = React.useState("");
  const [preview, setPreview] = React.useState<Lesson | null>(null);

  const done = (message: string) => {
    toast.success(message);
    setApproveOpen(false);
    setRejectOpen(false);
    qc.invalidateQueries({ queryKey: ["admin-course", courseId] });
    qc.invalidateQueries({ queryKey: ["admin-courses"] });
  };

  const approve = useMutation({
    mutationFn: () => adminApi.approve(courseId),
    onSuccess: ({ message }) => done(message),
    onError: (e) => toast.error(errorMessage(e)),
  });
  const reject = useMutation({
    mutationFn: () => adminApi.reject(courseId, reason.trim()),
    onSuccess: ({ message }) => {
      setReason("");
      done(message);
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  if (course.isLoading) return <Spinner />;
  if (course.error) return <ErrorNote message={errorMessage(course.error)} />;
  const c = course.data!;
  const pending = c.status === "PENDING";

  return (
    <>
      <Link href="/admin/courses" className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-blue">
        <ChevronLeft className="size-4" aria-hidden /> Danh sách kiểm duyệt
      </Link>

      <div className="mt-4 grid gap-10 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl">{c.title}</h1>
            <StatusBadge status={c.status} />
          </div>
          <p className="mt-1 text-sm text-ink-muted">
            {c.category?.name}, cập nhật {formatDateTime(c.updated_at)}
          </p>
          {c.instructor && (
            <div className="mt-4 flex items-center gap-2 text-sm">
              <Avatar name={c.instructor.full_name} src={c.instructor.avatar_url} size={28} />
              {c.instructor.full_name}
            </div>
          )}

          {c.status === "REJECTED" && c.rejection_reason && (
            <p className="mt-6 text-sm text-ink-muted">
              Nhận xét lần trước: <span className="font-medium text-red">{c.rejection_reason}</span>
            </p>
          )}

          <section className="mt-8">
            <h2 className="text-lg">Mô tả</h2>
            <p className="mt-2 max-w-prose whitespace-pre-line text-sm leading-6">
              {c.description || <span className="text-ink-muted">Giảng viên chưa viết mô tả.</span>}
            </p>
          </section>

          <section className="mt-8">
            <h2 className="text-lg">
              Nội dung ({c.total_lessons} bài, {formatDuration(c.total_duration_seconds)} video, {c.quizzes.length} bài kiểm tra)
            </h2>
            <p className="mt-1 text-sm text-ink-muted">Bấm vào bài học để xem nội dung trước khi duyệt.</p>
            <ol className="mt-4 divide-y divide-line rounded-lg border border-line bg-paper-raised">
              {c.chapters.map((ch, i) => (
                <li key={ch.id} className="px-5 py-4">
                  <p className="font-medium">
                    <span className="mr-2 text-ink-muted">Chương {i + 1}.</span>
                    {ch.title}
                  </p>
                  <ul className="mt-2 space-y-1">
                    {ch.lessons.map((l) => (
                      <li key={l.id}>
                        <button
                          onClick={() => setPreview(l)}
                          className="flex w-full items-center gap-3 rounded px-2 py-1.5 text-left text-sm hover:bg-blue-soft"
                        >
                          {l.lesson_type === "VIDEO" ? (
                            <PlayCircle className="size-4 shrink-0 text-blue" aria-label="Video" />
                          ) : (
                            <FileText className="size-4 shrink-0 text-blue" aria-label="Tài liệu" />
                          )}
                          <span className="flex-1 truncate">{l.title}</span>
                          {l.is_free_preview && <span className="text-xs text-blue">Học thử</span>}
                          {l.duration_seconds > 0 && <span className="text-xs text-ink-muted">{formatDuration(l.duration_seconds)}</span>}
                        </button>
                      </li>
                    ))}
                    {ch.lessons.length === 0 && <li className="px-2 text-sm text-ink-muted">Chương trống</li>}
                  </ul>
                </li>
              ))}
            </ol>
          </section>
        </div>

        <aside className="lg:sticky lg:top-24 lg:self-start">
          <CourseCover course={c} />
          {pending ? (
            <div className="mt-5 space-y-2">
              <Button className="w-full" size="lg" onClick={() => setApproveOpen(true)}>
                Phê duyệt và xuất bản
              </Button>
              <Button className="w-full" variant="danger" onClick={() => setRejectOpen(true)}>
                Từ chối kèm nhận xét
              </Button>
            </div>
          ) : (
            <p className="mt-5 text-sm text-ink-muted">Chỉ khóa học ở trạng thái chờ duyệt mới phê duyệt hoặc từ chối được.</p>
          )}
          {c.status === "PUBLISHED" && (
            <Link href={`/courses/${c.id}`} className="mt-3 inline-flex items-center gap-1 text-sm text-blue hover:underline">
              Xem trang công khai <ExternalLink className="size-3.5" aria-hidden />
            </Link>
          )}
        </aside>
      </div>

      <ConfirmDialog
        open={approveOpen}
        onOpenChange={setApproveOpen}
        title="Xuất bản khóa học này?"
        description="Khóa học sẽ hiển thị công khai và học viên có thể đăng ký ngay."
        confirmLabel="Phê duyệt và xuất bản"
        destructive={false}
        loading={approve.isPending}
        onConfirm={() => approve.mutate()}
      />

      <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
        <DialogContent title="Từ chối khóa học" description="Giảng viên sẽ thấy nhận xét này và sửa khóa học theo đó.">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (reason.trim().length >= 5) reject.mutate();
            }}
          >
            <Field label="Nhận xét cho giảng viên" htmlFor="reject-reason" hint="Ít nhất 5 ký tự, tối đa 500.">
              <Textarea
                id="reject-reason"
                rows={4}
                maxLength={500}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Ví dụ: Cần bổ sung tài liệu bài tập cho chương 2"
                autoFocus
              />
            </Field>
            <DialogFooter>
              <DialogClose asChild>
                <Button type="button" variant="outline">
                  Hủy
                </Button>
              </DialogClose>
              <Button type="submit" variant="danger" loading={reject.isPending} disabled={reason.trim().length < 5}>
                Từ chối khóa học
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {preview && <LessonPreview lesson={preview} onClose={() => setPreview(null)} />}
    </>
  );
}

function LessonPreview({ lesson, onClose }: { lesson: Lesson; onClose: () => void }) {
  // Admins can open any lesson; this returns the presigned document URL
  const full = useQuery({ queryKey: ["lesson", lesson.id], queryFn: () => learnApi.lesson(lesson.id) });
  const l = full.data ?? lesson;
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent title={lesson.title} description={lesson.lesson_type === "VIDEO" ? "Video YouTube" : "Tài liệu"} className="max-w-3xl">
        {full.isLoading ? (
          <Spinner />
        ) : l.lesson_type === "VIDEO" && l.youtube_video_id ? (
          <div className="aspect-video overflow-hidden rounded-md bg-[#000]">
            <iframe
              className="size-full"
              src={`https://www.youtube-nocookie.com/embed/${l.youtube_video_id}?rel=0`}
              title={l.title}
              allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        ) : l.document_url ? (
          <Button asChild>
            <a href={l.document_url} target="_blank" rel="noreferrer">
              Mở tài liệu trong tab mới
            </a>
          </Button>
        ) : (
          <p className="text-sm text-ink-muted">Bài học chưa có nội dung.</p>
        )}
      </DialogContent>
    </Dialog>
  );
}
