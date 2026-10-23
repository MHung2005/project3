"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, FileText, Pencil, PlayCircle, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { instructorApi } from "@/lib/endpoints";
import type { Chapter, CourseDetail, Lesson } from "@/lib/types";
import { formatDuration } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ConfirmDialog, Dialog, DialogClose, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { Field, Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/misc";
import { LessonDialog } from "./lesson-dialog";

type Pending =
  | { kind: "chapter"; chapter?: Chapter }
  | { kind: "lesson"; chapterId: number; lesson?: Lesson }
  | { kind: "delete-chapter"; chapter: Chapter }
  | { kind: "delete-lesson"; lesson: Lesson }
  | null;

/** Chapters → lessons editor with add / rename / reorder / delete. */
export function CurriculumEditor({
  course,
  locked,
  onChanged,
}: {
  course: CourseDetail;
  locked: boolean;
  onChanged: () => void;
}) {
  const [pending, setPending] = React.useState<Pending>(null);
  const close = () => setPending(null);

  const run = useMutation({
    mutationFn: (fn: () => Promise<{ message: string }>) => fn(),
    onSuccess: ({ message }) => {
      toast.success(message);
      onChanged();
      close();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  // Move one item and renumber the list 1..n, updating only rows whose index changed
  const reorder = useMutation({
    mutationFn: async (args: { items: { id: number; order_index: number }[]; from: number; to: number; type: "chapter" | "lesson" }) => {
      const update = args.type === "chapter" ? instructorApi.updateChapter : instructorApi.updateLesson;
      const next = [...args.items];
      const [moved] = next.splice(args.from, 1);
      next.splice(args.to, 0, moved);
      for (const [i, item] of next.entries()) {
        if (item.order_index !== i + 1) await update(item.id, { order_index: i + 1 });
      }
    },
    onSuccess: onChanged,
    onError: (e) => toast.error(errorMessage(e)),
  });

  const chapters = course.chapters;

  return (
    <div className="max-w-4xl">
      {chapters.length === 0 ? (
        <EmptyState
          title="Khóa học chưa có chương nào"
          description="Chia khóa học thành các chương, mỗi chương gồm bài học video hoặc tài liệu."
          action={!locked && <Button onClick={() => setPending({ kind: "chapter" })}>Thêm chương đầu tiên</Button>}
        />
      ) : (
        <ol className="space-y-6">
          {chapters.map((ch, ci) => (
            <li key={ch.id} className="rounded-lg border border-line bg-paper-raised">
              <div className="flex items-center gap-2 border-b border-line px-4 py-3">
                <h3 className="min-w-0 flex-1 truncate text-base font-medium">
                  <span className="mr-2 text-ink-muted">Chương {ci + 1}.</span>
                  {ch.title}
                </h3>
                {!locked && (
                  <div className="flex shrink-0 items-center">
                    <IconBtn
                      label="Chuyển chương lên"
                      disabled={ci === 0 || reorder.isPending}
                      onClick={() => reorder.mutate({ items: chapters, from: ci, to: ci - 1, type: "chapter" })}
                    >
                      <ArrowUp />
                    </IconBtn>
                    <IconBtn
                      label="Chuyển chương xuống"
                      disabled={ci === chapters.length - 1 || reorder.isPending}
                      onClick={() => reorder.mutate({ items: chapters, from: ci, to: ci + 1, type: "chapter" })}
                    >
                      <ArrowDown />
                    </IconBtn>
                    <IconBtn label="Đổi tên chương" onClick={() => setPending({ kind: "chapter", chapter: ch })}>
                      <Pencil />
                    </IconBtn>
                    <IconBtn label="Xóa chương" danger onClick={() => setPending({ kind: "delete-chapter", chapter: ch })}>
                      <Trash2 />
                    </IconBtn>
                  </div>
                )}
              </div>
              {ch.lessons.length === 0 ? (
                <p className="px-4 py-4 text-sm text-ink-muted">Chương chưa có bài học.</p>
              ) : (
                <ul className="divide-y divide-line/70">
                  {ch.lessons.map((l, li) => (
                    <li key={l.id} className="flex items-center gap-3 px-4 py-2.5 text-sm">
                      {l.lesson_type === "VIDEO" ? (
                        <PlayCircle className="size-4 shrink-0 text-blue" aria-label="Video" />
                      ) : (
                        <FileText className="size-4 shrink-0 text-blue" aria-label="Tài liệu" />
                      )}
                      <span className="min-w-0 flex-1 truncate">{l.title}</span>
                      {l.is_free_preview && <span className="text-xs text-blue">Học thử</span>}
                      <span className="w-20 shrink-0 text-right text-xs text-ink-muted">
                        {l.lesson_type === "VIDEO" ? formatDuration(l.duration_seconds) : "Tài liệu"}
                      </span>
                      {!locked && (
                        <div className="flex shrink-0 items-center">
                          <IconBtn
                            label="Chuyển bài lên"
                            disabled={li === 0 || reorder.isPending}
                            onClick={() => reorder.mutate({ items: ch.lessons, from: li, to: li - 1, type: "lesson" })}
                          >
                            <ArrowUp />
                          </IconBtn>
                          <IconBtn
                            label="Chuyển bài xuống"
                            disabled={li === ch.lessons.length - 1 || reorder.isPending}
                            onClick={() => reorder.mutate({ items: ch.lessons, from: li, to: li + 1, type: "lesson" })}
                          >
                            <ArrowDown />
                          </IconBtn>
                          <IconBtn label="Sửa bài học" onClick={() => setPending({ kind: "lesson", chapterId: ch.id, lesson: l })}>
                            <Pencil />
                          </IconBtn>
                          <IconBtn label="Xóa bài học" danger onClick={() => setPending({ kind: "delete-lesson", lesson: l })}>
                            <Trash2 />
                          </IconBtn>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              {!locked && (
                <div className="border-t border-line px-4 py-2">
                  <Button variant="ghost" size="sm" onClick={() => setPending({ kind: "lesson", chapterId: ch.id })}>
                    <Plus /> Thêm bài học
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ol>
      )}

      {!locked && chapters.length > 0 && (
        <Button variant="outline" className="mt-6" onClick={() => setPending({ kind: "chapter" })}>
          <Plus /> Thêm chương
        </Button>
      )}

      <ChapterDialog
        open={pending?.kind === "chapter"}
        chapter={pending?.kind === "chapter" ? pending.chapter : undefined}
        saving={run.isPending}
        onClose={close}
        onSave={(title) => {
          const ch = pending?.kind === "chapter" ? pending.chapter : undefined;
          run.mutate(() => (ch ? instructorApi.updateChapter(ch.id, { title }) : instructorApi.createChapter(course.id, { title })));
        }}
      />

      {pending?.kind === "lesson" && (
        <LessonDialog
          lesson={pending.lesson}
          saving={run.isPending}
          onClose={close}
          onSave={(input) => {
            const { lesson, chapterId } = pending;
            run.mutate(() => (lesson ? instructorApi.updateLesson(lesson.id, input) : instructorApi.createLesson(chapterId, input)));
          }}
        />
      )}

      <ConfirmDialog
        open={pending?.kind === "delete-chapter"}
        onOpenChange={(o) => !o && close()}
        title={pending?.kind === "delete-chapter" ? `Xóa chương “${pending.chapter.title}”?` : ""}
        description="Mọi bài học trong chương và tiến độ học của học viên với các bài đó sẽ bị xóa."
        confirmLabel="Xóa chương"
        loading={run.isPending}
        onConfirm={() => pending?.kind === "delete-chapter" && run.mutate(() => instructorApi.deleteChapter(pending.chapter.id))}
      />
      <ConfirmDialog
        open={pending?.kind === "delete-lesson"}
        onOpenChange={(o) => !o && close()}
        title={pending?.kind === "delete-lesson" ? `Xóa bài học “${pending.lesson.title}”?` : ""}
        description="Tiến độ của học viên với bài học này sẽ bị xóa và tiến độ khóa học được tính lại."
        confirmLabel="Xóa bài học"
        loading={run.isPending}
        onConfirm={() => pending?.kind === "delete-lesson" && run.mutate(() => instructorApi.deleteLesson(pending.lesson.id))}
      />
    </div>
  );
}

function IconBtn({
  label,
  onClick,
  disabled,
  danger,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  danger?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
      className={`rounded p-1.5 text-ink-muted disabled:opacity-30 [&_svg]:size-4 ${danger ? "hover:bg-red/10 hover:text-red" : "hover:bg-blue-soft hover:text-blue"}`}
    >
      {children}
    </button>
  );
}

function ChapterDialog({
  open,
  chapter,
  saving,
  onClose,
  onSave,
}: {
  open: boolean;
  chapter?: Chapter;
  saving: boolean;
  onClose: () => void;
  onSave: (title: string) => void;
}) {
  const [title, setTitle] = React.useState("");
  React.useEffect(() => {
    if (open) setTitle(chapter?.title ?? "");
  }, [open, chapter]);
  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent title={chapter ? "Đổi tên chương" : "Thêm chương"}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSave(title.trim());
          }}
        >
          <Field label="Tên chương" htmlFor="ch-title">
            <Input id="ch-title" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
          </Field>
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Hủy
              </Button>
            </DialogClose>
            <Button type="submit" loading={saving} disabled={title.trim().length < 2}>
              {chapter ? "Lưu tên chương" : "Thêm chương"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
