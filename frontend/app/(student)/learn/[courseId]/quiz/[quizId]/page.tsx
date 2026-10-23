"use client";

import * as React from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { quizApi } from "@/lib/endpoints";
import type { QuizResult, QuizStart } from "@/lib/types";
import { cn, formatDateTime, formatScore, parseDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { EmptyState, ErrorNote, Spinner } from "@/components/ui/misc";
import { Table, Td, Th } from "@/components/ui/table";
import { QuestionItem } from "@/components/quiz/question-item";
import { QuizCountdown } from "@/components/quiz/quiz-countdown";
import { QuizResultSheet } from "@/components/quiz/quiz-result";

type Answers = Record<number, number[]>;

const draftKey = (attemptId: number) => `quiz-draft-${attemptId}`;

function loadDraft(attemptId: number): Answers {
  try {
    return JSON.parse(sessionStorage.getItem(draftKey(attemptId)) ?? "{}") as Answers;
  } catch {
    return {};
  }
}

function saveDraft(attemptId: number, answers: Answers) {
  try {
    sessionStorage.setItem(draftKey(attemptId), JSON.stringify(answers));
  } catch {
    // storage unavailable – answers still live in memory
  }
}

export default function QuizPage({ params }: { params: { courseId: string; quizId: string } }) {
  const courseId = Number(params.courseId);
  const quizId = Number(params.quizId);
  const qc = useQueryClient();

  const [session, setSession] = React.useState<QuizStart | null>(null);
  const [result, setResult] = React.useState<QuizResult | null>(null);

  const quizzes = useQuery({ queryKey: ["learner-quizzes", courseId], queryFn: () => quizApi.forCourse(courseId) });
  const attempts = useQuery({ queryKey: ["my-attempts", quizId], queryFn: () => quizApi.myAttempts(quizId) });
  const quiz = quizzes.data?.find((q) => q.id === quizId);

  const start = useMutation({
    mutationFn: () => quizApi.start(quizId),
    onSuccess: (data) => {
      setResult(null);
      setSession(data);
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const viewAttempt = useMutation({
    mutationFn: (attemptId: number) => quizApi.attempt(attemptId),
    onSuccess: (data) => {
      setResult(data);
      window.scrollTo({ top: 0 });
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["my-attempts", quizId] });
    qc.invalidateQueries({ queryKey: ["learner-quizzes", courseId] });
    qc.invalidateQueries({ queryKey: ["course-progress", courseId] });
    qc.invalidateQueries({ queryKey: ["my-courses"] });
  };

  const back = (
    <Link href={`/learn/${courseId}`} className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-blue">
      <ChevronLeft className="size-4" aria-hidden /> Quay lại bài học
    </Link>
  );

  if (quizzes.isLoading || attempts.isLoading) return <Spinner className="py-24" />;
  if (quizzes.error) {
    return (
      <div className="container max-w-3xl py-10">
        {back}
        <ErrorNote className="mt-6" message={errorMessage(quizzes.error)} />
      </div>
    );
  }
  if (!quiz) {
    return (
      <div className="container max-w-3xl py-10">
        {back}
        <EmptyState className="mt-6" title="Không tìm thấy bài kiểm tra" description="Bài kiểm tra có thể đã bị giảng viên xóa." />
      </div>
    );
  }

  if (session && !result) {
    return (
      <TakeQuiz
        title={quiz.title}
        session={session}
        onSubmitted={(r, message) => {
          setSession(null);
          setResult(r);
          refresh();
          if (r.status === "TIMEOUT") toast.error(message);
          else toast.success(message);
          window.scrollTo({ top: 0 });
        }}
      />
    );
  }

  const history = attempts.data ?? [];
  const inProgress = history.find((a) => a.status === "IN_PROGRESS");
  const finished = history.filter((a) => a.status !== "IN_PROGRESS").length;
  const exhausted = !inProgress && history.length >= quiz.max_attempts;

  return (
    <div className="container max-w-3xl py-10">
      {back}

      {result ? (
        <div className="mt-6">
          <QuizResultSheet result={result} title={quiz.title} />
          <div className="mt-6 flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => setResult(null)}>
              Xem lịch sử làm bài
            </Button>
            <Button asChild variant="ghost">
              <Link href={`/learn/${courseId}`}>Tiếp tục học</Link>
            </Button>
          </div>
        </div>
      ) : (
        <>
          <h1 className="mt-6 text-2xl">{quiz.title}</h1>
          {quiz.description && <p className="mt-2 max-w-prose whitespace-pre-line text-ink-muted">{quiz.description}</p>}
          <dl className="mt-6 grid grid-cols-2 gap-4 rounded-lg border border-line bg-paper-raised p-5 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-ink-muted">Số câu hỏi</dt>
              <dd className="mt-0.5 text-lg font-medium">{quiz.question_count}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Thời gian</dt>
              <dd className="mt-0.5 text-lg font-medium">{quiz.duration_minutes} phút</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Điểm đạt</dt>
              <dd className="mt-0.5 text-lg font-medium">{formatScore(quiz.passing_score)}/10</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Lượt đã dùng</dt>
              <dd className="mt-0.5 text-lg font-medium">
                {history.length}/{quiz.max_attempts}
              </dd>
            </div>
          </dl>

          {quiz.best_score !== null && (
            <p className="mt-6 text-sm">
              Điểm cao nhất của bạn: <span className="numeric">{formatScore(quiz.best_score)}/10</span>
              {quiz.is_passed && <span className="ml-2 text-blue">Đã đạt</span>}
            </p>
          )}

          <div className="mt-8">
            {exhausted ? (
              <p className="text-sm text-ink-muted">Bạn đã dùng hết {quiz.max_attempts} lượt làm bài này.</p>
            ) : (
              <>
                <Button size="lg" loading={start.isPending} onClick={() => start.mutate()}>
                  {inProgress ? "Tiếp tục lượt đang làm" : finished > 0 ? "Làm lại bài" : "Bắt đầu làm bài"}
                </Button>
                <p className="mt-2 text-xs text-ink-muted">
                  Đồng hồ bắt đầu chạy ngay khi bấm. Hết giờ, bài sẽ tự động được nộp.
                </p>
              </>
            )}
          </div>

          {finished > 0 && (
            <section className="mt-12">
              <h2 className="mb-4 text-lg">Lịch sử làm bài</h2>
              <Table>
                <thead>
                  <tr>
                    <Th>Lượt</Th>
                    <Th>Nộp lúc</Th>
                    <Th>Điểm</Th>
                    <Th>Kết quả</Th>
                    <Th />
                  </tr>
                </thead>
                <tbody>
                  {history
                    .filter((a) => a.status !== "IN_PROGRESS")
                    .map((a) => (
                      <tr key={a.id}>
                        <Td>Lần {a.attempt_number}</Td>
                        <Td>{formatDateTime(a.submitted_at)}</Td>
                        <Td>
                          <span className="numeric">{a.status === "TIMEOUT" ? "—" : formatScore(a.score)}</span>
                        </Td>
                        <Td>
                          {a.status === "TIMEOUT" ? (
                            <span className="text-ink-muted">Quá giờ</span>
                          ) : a.is_passed ? (
                            <span className="text-blue">Đạt</span>
                          ) : (
                            <span className="text-red">Chưa đạt</span>
                          )}
                        </Td>
                        <Td className="text-right">
                          <Button
                            variant="link"
                            size="sm"
                            disabled={viewAttempt.isPending}
                            onClick={() => viewAttempt.mutate(a.id)}
                          >
                            Xem bài làm
                          </Button>
                        </Td>
                      </tr>
                    ))}
                </tbody>
              </Table>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function TakeQuiz({
  title,
  session,
  onSubmitted,
}: {
  title: string;
  session: QuizStart;
  onSubmitted: (result: QuizResult, message: string) => void;
}) {
  const [answers, setAnswers] = React.useState<Answers>(() => loadDraft(session.attempt_id));
  const [confirmOpen, setConfirmOpen] = React.useState(false);
  const deadline = React.useMemo(() => parseDate(session.expires_at), [session.expires_at]);
  const answersRef = React.useRef(answers);
  answersRef.current = answers;

  const submit = useMutation({
    mutationFn: () =>
      quizApi.submit(
        session.attempt_id,
        session.questions.map((q) => ({ question_id: q.id, selected_option_ids: answersRef.current[q.id] ?? [] })),
      ),
    onSuccess: ({ data, message }) => {
      try {
        sessionStorage.removeItem(draftKey(session.attempt_id));
      } catch {
        // ignore
      }
      onSubmitted(data, message);
    },
    onError: (e) => {
      setConfirmOpen(false);
      toast.error(errorMessage(e));
    },
  });

  // Warn before leaving mid-attempt
  React.useEffect(() => {
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, []);

  const setAnswer = (qid: number, ids: number[]) => {
    setAnswers((prev) => {
      const next = { ...prev, [qid]: ids };
      saveDraft(session.attempt_id, next);
      return next;
    });
  };

  const answered = session.questions.filter((q) => (answers[q.id] ?? []).length > 0).length;
  const total = session.questions.length;

  return (
    <div>
      <div className="sticky top-16 z-30 border-b border-line bg-paper/95 backdrop-blur">
        <div className="container flex max-w-3xl items-center gap-4 py-3">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{title}</p>
            <p className="text-xs text-ink-muted">
              Lần làm thứ {session.attempt_number}, đã trả lời {answered}/{total} câu
            </p>
          </div>
          <QuizCountdown
            deadline={deadline}
            onExpire={() => {
              if (!submit.isPending && !submit.isSuccess) {
                toast.info("Hết giờ. Bài làm đang được nộp tự động.");
                submit.mutate();
              }
            }}
          />
          <Button size="sm" loading={submit.isPending} onClick={() => setConfirmOpen(true)}>
            Nộp bài
          </Button>
        </div>
      </div>

      <div className="container max-w-3xl py-8">
        <nav aria-label="Danh sách câu hỏi" className="mb-8 flex flex-wrap gap-1.5">
          {session.questions.map((q, i) => {
            const done = (answers[q.id] ?? []).length > 0;
            return (
              <a
                key={q.id}
                href={`#question-${q.id}`}
                className={cn(
                  "grid size-8 place-items-center rounded border text-xs numeric",
                  done ? "border-blue bg-blue text-on-blue" : "border-line bg-paper-raised text-ink-muted hover:border-blue",
                )}
                aria-label={`Câu ${i + 1}${done ? ", đã trả lời" : ", chưa trả lời"}`}
              >
                {i + 1}
              </a>
            );
          })}
        </nav>

        <div className="space-y-10">
          {session.questions.map((q, i) => (
            <QuestionItem
              key={q.id}
              index={i}
              question={q}
              selected={answers[q.id] ?? []}
              onChange={(ids) => setAnswer(q.id, ids)}
            />
          ))}
        </div>

        <div className="mt-12 border-t border-line pt-6">
          <Button size="lg" loading={submit.isPending} onClick={() => setConfirmOpen(true)}>
            Nộp bài
          </Button>
        </div>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Nộp bài kiểm tra?"
        description={
          answered < total
            ? `Bạn còn ${total - answered} câu chưa trả lời. Sau khi nộp, bạn không thể sửa đáp án của lượt này.`
            : "Sau khi nộp, bạn không thể sửa đáp án của lượt này."
        }
        confirmLabel="Nộp bài"
        destructive={false}
        loading={submit.isPending}
        onConfirm={() => submit.mutate()}
      />
    </div>
  );
}
