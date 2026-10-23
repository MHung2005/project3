import { FileText, ListChecks, Lock, PlayCircle } from "lucide-react";
import type { Chapter, QuizBrief } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

/** Read-only syllabus: chapters → lessons (+ chapter quizzes). Used on the course page and in admin review. */
export function CourseOutline({
  chapters,
  quizzes = [],
  showLocks = true,
}: {
  chapters: Chapter[];
  quizzes?: QuizBrief[];
  showLocks?: boolean;
}) {
  const finalQuizzes = quizzes.filter((q) => q.chapter_id === null);
  if (chapters.length === 0) {
    return <p className="text-sm text-ink-muted">Khóa học chưa có chương nào.</p>;
  }
  return (
    <ol className="divide-y divide-line rounded-lg border border-line bg-paper-raised">
      {chapters.map((ch, i) => {
        const chapterQuizzes = quizzes.filter((q) => q.chapter_id === ch.id);
        const duration = ch.lessons.reduce((s, l) => s + l.duration_seconds, 0);
        return (
          <li key={ch.id} className="px-5 py-4">
            <div className="flex items-baseline justify-between gap-4">
              <h3 className="text-base font-medium">
                <span className="mr-2 text-ink-muted">Chương {i + 1}.</span>
                {ch.title}
              </h3>
              <span className="shrink-0 text-xs text-ink-muted">
                {ch.lessons.length} bài{duration > 0 && `, ${formatDuration(duration)}`}
              </span>
            </div>
            {(ch.lessons.length > 0 || chapterQuizzes.length > 0) && (
              <ul className="mt-3 space-y-1.5">
                {ch.lessons.map((l) => (
                  <li key={l.id} className="flex items-center gap-3 text-sm">
                    {l.lesson_type === "VIDEO" ? (
                      <PlayCircle className="size-4 shrink-0 text-ink-muted" aria-label="Video" />
                    ) : (
                      <FileText className="size-4 shrink-0 text-ink-muted" aria-label="Tài liệu" />
                    )}
                    <span className="min-w-0 flex-1 truncate">{l.title}</span>
                    {l.is_free_preview && <span className="text-xs text-blue">Học thử</span>}
                    {showLocks && l.is_locked && <Lock className="size-3.5 text-ink-muted" aria-label="Cần đăng ký" />}
                    {l.duration_seconds > 0 && (
                      <span className="w-16 shrink-0 text-right text-xs text-ink-muted">
                        {formatDuration(l.duration_seconds)}
                      </span>
                    )}
                  </li>
                ))}
                {chapterQuizzes.map((q) => (
                  <li key={`q${q.id}`} className="flex items-center gap-3 text-sm">
                    <ListChecks className="size-4 shrink-0 text-ink-muted" aria-label="Bài kiểm tra" />
                    <span className="min-w-0 flex-1 truncate">{q.title}</span>
                    <span className="shrink-0 text-xs text-ink-muted">{q.duration_minutes} phút</span>
                  </li>
                ))}
              </ul>
            )}
          </li>
        );
      })}
      {finalQuizzes.map((q) => (
        <li key={`final${q.id}`} className="flex items-center gap-3 px-5 py-4 text-sm">
          <ListChecks className="size-4 shrink-0 text-blue" aria-hidden />
          <span className="flex-1 font-medium">{q.title}</span>
          <span className="text-xs text-ink-muted">
            Bài thi cuối khóa, {q.duration_minutes} phút
          </span>
        </li>
      ))}
    </ol>
  );
}
