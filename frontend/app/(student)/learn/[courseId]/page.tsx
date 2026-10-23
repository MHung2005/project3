"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ChevronLeft, ChevronRight, FileText, ListChecks, PanelLeft, PlayCircle } from "lucide-react";
import { toast } from "sonner";
import { errorMessage, errorStatus } from "@/lib/api-client";
import { courseApi, learnApi } from "@/lib/endpoints";
import { useUi } from "@/hooks/use-ui";
import type { CourseDetail, CourseProgress, Lesson } from "@/lib/types";
import { cn, formatDuration, formatPercent, formatScore } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorNote, ProgressBar, Spinner } from "@/components/ui/misc";
import { YouTubePlayer } from "@/components/player/youtube-player";
import { DocumentViewer } from "@/components/player/document-viewer";

function LearnWorkspace({ courseId }: { courseId: number }) {
  const router = useRouter();
  const params = useSearchParams();
  const qc = useQueryClient();
  const { sidebarExpanded, toggleSidebar } = useUi();

  const course = useQuery({ queryKey: ["learn-course", courseId], queryFn: () => courseApi.detail(courseId) });
  const progress = useQuery({
    queryKey: ["course-progress", courseId],
    queryFn: () => learnApi.courseProgress(courseId),
    retry: (count, e) => errorStatus(e) !== 403 && count < 1,
  });

  const lessons = React.useMemo(() => course.data?.chapters.flatMap((c) => c.lessons) ?? [], [course.data]);
  const doneIds = React.useMemo(
    () => new Set(progress.data?.lessons.filter((l) => l.is_completed).map((l) => l.lesson_id) ?? []),
    [progress.data],
  );

  // Selected lesson: ?lesson=… or the first one not yet completed
  const requested = Number(params.get("lesson")) || null;
  const current =
    lessons.find((l) => l.id === requested) ?? lessons.find((l) => !doneIds.has(l.id)) ?? lessons[0] ?? null;
  const index = current ? lessons.findIndex((l) => l.id === current.id) : -1;

  const go = (lesson: Lesson) => router.replace(`/learn/${courseId}?lesson=${lesson.id}`, { scroll: false });

  if (course.isLoading || progress.isLoading) return <Spinner className="py-24" />;
  if (course.error) return <div className="container py-10"><ErrorNote message={errorMessage(course.error)} /></div>;
  if (progress.error) {
    return (
      <div className="container py-16">
        <EmptyState
          title="Bạn chưa đăng ký khóa học này"
          description={errorStatus(progress.error) === 403 ? "Đăng ký khóa học để xem bài giảng và lưu tiến độ." : errorMessage(progress.error)}
          action={
            <Button asChild>
              <Link href={`/courses/${courseId}`}>Xem trang khóa học</Link>
            </Button>
          }
        />
      </div>
    );
  }

  const c = course.data!;
  const p = progress.data!;

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col lg:flex-row">
      <aside
        className={cn(
          "border-b border-line bg-paper-raised lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)] lg:w-80 lg:shrink-0 lg:overflow-y-auto lg:border-b-0 lg:border-r",
          !sidebarExpanded && "lg:hidden",
        )}
      >
        <Syllabus course={c} progress={p} currentId={current?.id ?? null} doneIds={doneIds} onSelect={go} />
      </aside>

      <section className="min-w-0 flex-1">
        <div className="mx-auto max-w-4xl px-4 py-6 sm:px-8">
          <div className="mb-4 flex items-center gap-2">
            <button
              onClick={toggleSidebar}
              className="hidden rounded p-1.5 text-ink-muted hover:bg-blue-soft hover:text-blue lg:inline-flex"
              aria-label={sidebarExpanded ? "Ẩn đề cương" : "Hiện đề cương"}
            >
              <PanelLeft className="size-4" />
            </button>
            <Link href={`/courses/${courseId}`} className="truncate text-sm text-ink-muted hover:text-blue">
              {c.title}
            </Link>
          </div>

          {!current ? (
            <EmptyState title="Khóa học chưa có bài học" description="Giảng viên chưa thêm nội dung cho khóa học này." />
          ) : (
            <>
              <h1 className="mb-5 text-xl">{current.title}</h1>
              <LessonContent
                key={current.id}
                lessonId={current.id}
                completed={doneIds.has(current.id)}
                onCompleted={(pct, finished) => {
                  qc.invalidateQueries({ queryKey: ["course-progress", courseId] });
                  qc.invalidateQueries({ queryKey: ["my-courses"] });
                  if (finished) toast.success("Bạn đã hoàn thành toàn bộ khóa học!");
                  else toast.success(`Đã ghi nhận bài học. Tiến độ khóa học: ${formatPercent(pct)}`);
                }}
              />
              <div className="mt-10 flex items-center justify-between gap-4 border-t border-line pt-5">
                {index > 0 ? (
                  <Button variant="ghost" onClick={() => go(lessons[index - 1])}>
                    <ChevronLeft /> Bài trước
                  </Button>
                ) : (
                  <span />
                )}
                {index < lessons.length - 1 && (
                  <Button variant="outline" onClick={() => go(lessons[index + 1])}>
                    Bài tiếp theo <ChevronRight />
                  </Button>
                )}
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function LessonContent({
  lessonId,
  completed,
  onCompleted,
}: {
  lessonId: number;
  completed: boolean;
  onCompleted: (pct: number, courseFinished: boolean) => void;
}) {
  const lesson = useQuery({ queryKey: ["lesson", lessonId], queryFn: () => learnApi.lesson(lessonId) });
  const position = useQuery({
    queryKey: ["lesson-progress", lessonId],
    queryFn: () => learnApi.lessonProgress(lessonId),
    staleTime: 0,
    gcTime: 0,
  });

  const complete = useMutation({
    mutationFn: (second: number) => learnApi.complete(lessonId, second),
    onSuccess: ({ data }) => onCompleted(data.course_progress_percentage, data.is_course_completed),
    onError: (e) => toast.error(errorMessage(e)),
  });

  const savePosition = React.useCallback(
    (second: number) => {
      // Fire-and-forget; a failed save only costs the resume position
      learnApi.savePosition(lessonId, second).catch(() => undefined);
    },
    [lessonId],
  );

  if (lesson.isLoading || position.isLoading) return <Spinner />;
  if (lesson.error) return <ErrorNote message={errorMessage(lesson.error)} />;
  const l = lesson.data!;

  if (l.lesson_type === "VIDEO") {
    const last = position.data?.last_watched_second ?? 0;
    // Rewatching a finished video starts from the beginning
    const startAt = l.duration_seconds > 0 && last >= l.duration_seconds - 5 ? 0 : last;
    return (
      <YouTubePlayer
        lesson={l}
        startAt={startAt}
        completed={completed}
        onSavePosition={completed ? () => undefined : savePosition}
        onComplete={(second) => complete.mutate(second)}
      />
    );
  }
  return (
    <DocumentViewer
      lesson={l}
      completed={completed || complete.isSuccess}
      completing={complete.isPending}
      onComplete={() => complete.mutate(0)}
    />
  );
}

function Syllabus({
  course,
  progress,
  currentId,
  doneIds,
  onSelect,
}: {
  course: CourseDetail;
  progress: CourseProgress;
  currentId: number | null;
  doneIds: Set<number>;
  onSelect: (l: Lesson) => void;
}) {
  const quizState = new Map(progress.quizzes.map((q) => [q.quiz_id, q]));
  const pct = progress.enrollment.progress_percentage;
  // Phones: the outline starts collapsed so the lesson is visible without scrolling
  const [openOnMobile, setOpenOnMobile] = React.useState(false);

  const QuizLink = ({ quizId, title }: { quizId: number; title: string }) => {
    const s = quizState.get(quizId);
    return (
      <li>
        <Link
          href={`/learn/${course.id}/quiz/${quizId}`}
          className="flex items-center gap-2.5 rounded px-2 py-2 text-sm hover:bg-paper-sunk"
        >
          {s?.is_passed ? (
            <CheckCircle2 className="size-4 shrink-0 text-blue" aria-label="Đã đạt" />
          ) : (
            <ListChecks className="size-4 shrink-0 text-ink-muted" aria-hidden />
          )}
          <span className="min-w-0 flex-1 truncate">{title}</span>
          {s?.best_score !== null && s?.best_score !== undefined && (
            <span className="numeric text-[13px] text-ink-muted">{formatScore(s.best_score)}/10</span>
          )}
        </Link>
      </li>
    );
  };

  return (
    <div className="p-4">
      <div className="px-2 pb-4">
        <div className="flex items-baseline justify-between text-sm">
          <span className="font-medium">Tiến độ khóa học</span>
          <span className="numeric text-[13px] text-amber-ink">{formatPercent(pct)}</span>
        </div>
        <ProgressBar value={pct} className="mt-2" />
        <p className="mt-2 text-xs text-ink-muted">
          {progress.completed_items}/{progress.total_items} mục đã xong ({progress.completed_lessons}/{progress.total_lessons} bài
          học)
        </p>
      </div>
      <button
        className="mb-2 w-full rounded border border-line-strong px-3 py-2 text-left text-sm text-blue lg:hidden"
        aria-expanded={openOnMobile}
        onClick={() => setOpenOnMobile((v) => !v)}
      >
        {openOnMobile ? "Ẩn đề cương" : `Xem đề cương (${progress.total_lessons} bài học)`}
      </button>
      <nav aria-label="Đề cương khóa học" className={cn(!openOnMobile && "hidden lg:block")} onClick={() => setOpenOnMobile(false)}>
        {course.chapters.map((ch, i) => (
          <div key={ch.id} className="border-t border-line py-3">
            <p className="px-2 pb-1.5 text-[13px] font-semibold text-ink">
              Chương {i + 1}. {ch.title}
            </p>
            <ul>
              {ch.lessons.map((l) => {
                const done = doneIds.has(l.id);
                const active = l.id === currentId;
                return (
                  <li key={l.id}>
                    <button
                      onClick={() => onSelect(l)}
                      aria-current={active ? "true" : undefined}
                      className={cn(
                        "flex w-full items-center gap-2.5 rounded px-2 py-2 text-left text-sm",
                        active ? "bg-blue-soft font-semibold text-ink" : "hover:bg-paper-sunk",
                      )}
                    >
                      {done ? (
                        <CheckCircle2 className="size-4 shrink-0 text-blue" aria-label="Đã hoàn thành" />
                      ) : l.lesson_type === "VIDEO" ? (
                        <PlayCircle className="size-4 shrink-0 text-ink-muted" aria-label="Video" />
                      ) : (
                        <FileText className="size-4 shrink-0 text-ink-muted" aria-label="Tài liệu" />
                      )}
                      <span className="min-w-0 flex-1 truncate">{l.title}</span>
                      {l.duration_seconds > 0 && (
                        <span className="shrink-0 text-xs text-ink-muted">{formatDuration(l.duration_seconds)}</span>
                      )}
                    </button>
                  </li>
                );
              })}
              {course.quizzes
                .filter((q) => q.chapter_id === ch.id)
                .map((q) => (
                  <QuizLink key={q.id} quizId={q.id} title={q.title} />
                ))}
            </ul>
          </div>
        ))}
        {course.quizzes.some((q) => q.chapter_id === null) && (
          <div className="border-t border-line py-3">
            <p className="px-2 pb-1.5 text-[13px] font-semibold text-ink">Bài thi cuối khóa</p>
            <ul>
              {course.quizzes
                .filter((q) => q.chapter_id === null)
                .map((q) => (
                  <QuizLink key={q.id} quizId={q.id} title={q.title} />
                ))}
            </ul>
          </div>
        )}
      </nav>
      {progress.enrollment.status === "COMPLETED" && (
        <p className="mt-4 inline-flex items-center gap-1 rounded-sm bg-blue-soft px-2 text-[13px] font-medium leading-6 text-blue">Đã hoàn thành khóa học</p>
      )}
    </div>
  );
}

export default function LearnPage({ params }: { params: { courseId: string } }) {
  const courseId = Number(params.courseId);
  return (
    <React.Suspense fallback={<Spinner className="py-24" />}>
      <LearnWorkspace courseId={courseId} />
    </React.Suspense>
  );
}
