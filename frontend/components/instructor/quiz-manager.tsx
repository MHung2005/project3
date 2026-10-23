"use client";

import * as React from "react";
import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { instructorApi } from "@/lib/endpoints";
import type { CourseDetail, Quiz, QuizInput } from "@/lib/types";
import { formatDateTime, formatScore } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ConfirmDialog, Dialog, DialogClose, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorNote, Spinner } from "@/components/ui/misc";
import { Table, Td, Th } from "@/components/ui/table";

type Mode = { kind: "edit"; quiz?: Quiz } | { kind: "results"; quiz: Quiz } | { kind: "delete"; quiz: Quiz } | null;

export function QuizManager({ course, onChanged }: { course: CourseDetail; onChanged: () => void }) {
  const [mode, setMode] = React.useState<Mode>(null);
  const quizzes = useQuery({ queryKey: ["instructor-quizzes", course.id], queryFn: () => instructorApi.quizzes(course.id) });

  const chapterName = (id: number | null) => {
    if (id === null) return "Bài thi cuối khóa";
    const i = course.chapters.findIndex((c) => c.id === id);
    return i >= 0 ? `Chương ${i + 1}. ${course.chapters[i].title}` : "Chương đã xóa";
  };

  const done = () => {
    quizzes.refetch();
    onChanged();
    setMode(null);
  };

  const remove = useMutation({
    mutationFn: (id: number) => instructorApi.deleteQuiz(id),
    onSuccess: ({ message }) => {
      toast.success(message);
      done();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  return (
    <div className="max-w-4xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-prose text-sm text-ink-muted">
          Bài kiểm tra lấy câu hỏi từ{" "}
          <Link href="/instructor/questions" className="text-blue underline-offset-4 hover:underline">
            ngân hàng câu hỏi
          </Link>{" "}
          của bạn. Học viên cần đạt bài kiểm tra để hoàn thành khóa học.
        </p>
        <Button onClick={() => setMode({ kind: "edit" })}>
          <Plus /> Tạo bài kiểm tra
        </Button>
      </div>

      {quizzes.isLoading ? (
        <Spinner />
      ) : quizzes.error ? (
        <ErrorNote message={errorMessage(quizzes.error)} />
      ) : quizzes.data!.length === 0 ? (
        <EmptyState title="Chưa có bài kiểm tra" description="Tạo bài kiểm tra cho từng chương hoặc một bài thi cuối khóa." />
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Bài kiểm tra</Th>
              <Th>Thuộc</Th>
              <Th>Thời gian</Th>
              <Th>Điểm đạt</Th>
              <Th>Số lượt</Th>
              <Th />
            </tr>
          </thead>
          <tbody>
            {quizzes.data!.map((q) => (
              <tr key={q.id}>
                <Td className="font-medium">{q.title}</Td>
                <Td className="text-ink-muted">{chapterName(q.chapter_id)}</Td>
                <Td>{q.duration_minutes} phút</Td>
                <Td>{formatScore(q.passing_score)}/10</Td>
                <Td>{q.max_attempts}</Td>
                <Td className="whitespace-nowrap text-right">
                  <Button variant="link" size="sm" onClick={() => setMode({ kind: "results", quiz: q })}>
                    Kết quả
                  </Button>
                  <Button variant="link" size="sm" className="ml-3" onClick={() => setMode({ kind: "edit", quiz: q })}>
                    Sửa
                  </Button>
                  <Button variant="link" size="sm" className="ml-3 text-red" onClick={() => setMode({ kind: "delete", quiz: q })}>
                    Xóa
                  </Button>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {mode?.kind === "edit" && <QuizDialog course={course} quiz={mode.quiz} onClose={() => setMode(null)} onSaved={done} />}
      {mode?.kind === "results" && <ResultsDialog quiz={mode.quiz} onClose={() => setMode(null)} />}
      <ConfirmDialog
        open={mode?.kind === "delete"}
        onOpenChange={(o) => !o && setMode(null)}
        title={mode?.kind === "delete" ? `Xóa “${mode.quiz.title}”?` : ""}
        description="Lịch sử làm bài của học viên với bài kiểm tra này cũng bị xóa."
        confirmLabel="Xóa bài kiểm tra"
        loading={remove.isPending}
        onConfirm={() => mode?.kind === "delete" && remove.mutate(mode.quiz.id)}
      />
    </div>
  );
}

function QuizDialog({
  course,
  quiz,
  onClose,
  onSaved,
}: {
  course: CourseDetail;
  quiz?: Quiz;
  onClose: () => void;
  onSaved: () => void;
}) {
  const detail = useQuery({ queryKey: ["instructor-quiz", quiz?.id], queryFn: () => instructorApi.quiz(quiz!.id), enabled: !!quiz });
  const bank = useQuery({ queryKey: ["question-bank-all"], queryFn: () => instructorApi.questions({ limit: 100 }) });

  const [form, setForm] = React.useState({
    title: quiz?.title ?? "",
    description: quiz?.description ?? "",
    chapter_id: quiz?.chapter_id ? String(quiz.chapter_id) : "",
    duration_minutes: String(quiz?.duration_minutes ?? 15),
    max_attempts: String(quiz?.max_attempts ?? 3),
    passing_score: String(quiz?.passing_score ?? 8),
  });
  const [selected, setSelected] = React.useState<number[]>([]);
  const [filter, setFilter] = React.useState("");

  React.useEffect(() => {
    if (detail.data) setSelected(detail.data.questions.map((q) => q.question.id));
  }, [detail.data]);

  const save = useMutation({
    mutationFn: () => {
      const body: QuizInput = {
        course_id: course.id,
        chapter_id: form.chapter_id ? Number(form.chapter_id) : null,
        title: form.title.trim(),
        description: form.description.trim() || null,
        duration_minutes: Number(form.duration_minutes),
        max_attempts: Number(form.max_attempts),
        passing_score: Number(form.passing_score.replace(",", ".")),
        question_ids: selected,
      };
      return quiz ? instructorApi.updateQuiz(quiz.id, body) : instructorApi.createQuiz(body);
    },
    onSuccess: ({ message }) => {
      toast.success(message);
      onSaved();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const questions = (bank.data?.items ?? []).filter((q) => q.content.toLowerCase().includes(filter.toLowerCase()));
  const score = Number(form.passing_score.replace(",", "."));
  const valid =
    form.title.trim().length >= 2 &&
    selected.length > 0 &&
    Number(form.duration_minutes) >= 1 &&
    Number(form.max_attempts) >= 1 &&
    score >= 0 &&
    score <= 10;

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent title={quiz ? "Sửa bài kiểm tra" : "Tạo bài kiểm tra"} className="max-w-2xl">
        {quiz && detail.isLoading ? (
          <Spinner />
        ) : (
          <form
            className="space-y-5"
            onSubmit={(e) => {
              e.preventDefault();
              if (valid) save.mutate();
            }}
          >
            <Field label="Tên bài kiểm tra" htmlFor="qz-title">
              <Input id="qz-title" value={form.title} onChange={set("title")} />
            </Field>
            <Field label="Hướng dẫn làm bài" htmlFor="qz-desc">
              <Textarea id="qz-desc" rows={3} value={form.description} onChange={set("description")} />
            </Field>
            <Field label="Thuộc" htmlFor="qz-chapter">
              <Select id="qz-chapter" value={form.chapter_id} onChange={set("chapter_id")}>
                <option value="">Bài thi cuối khóa</option>
                {course.chapters.map((c, i) => (
                  <option key={c.id} value={c.id}>
                    Chương {i + 1}. {c.title}
                  </option>
                ))}
              </Select>
            </Field>
            <div className="grid grid-cols-3 gap-3">
              <Field label="Thời gian (phút)" htmlFor="qz-dur">
                <Input id="qz-dur" inputMode="numeric" value={form.duration_minutes} onChange={set("duration_minutes")} />
              </Field>
              <Field label="Số lượt tối đa" htmlFor="qz-att">
                <Input id="qz-att" inputMode="numeric" value={form.max_attempts} onChange={set("max_attempts")} />
              </Field>
              <Field label="Điểm đạt (/10)" htmlFor="qz-pass">
                <Input id="qz-pass" inputMode="decimal" value={form.passing_score} onChange={set("passing_score")} />
              </Field>
            </div>

            <div>
              <div className="mb-2 flex items-baseline justify-between">
                <p className="field-label mb-0">Câu hỏi ({selected.length} đã chọn)</p>
                <Link href="/instructor/questions" className="text-xs text-blue hover:underline" target="_blank">
                  Mở ngân hàng câu hỏi
                </Link>
              </div>
              <Input placeholder="Lọc câu hỏi" value={filter} onChange={(e) => setFilter(e.target.value)} className="mb-2" />
              <div className="max-h-64 overflow-y-auto rounded border border-line">
                {bank.isLoading ? (
                  <Spinner className="py-6" />
                ) : questions.length === 0 ? (
                  <p className="p-4 text-sm text-ink-muted">
                    {bank.data?.items.length ? "Không có câu hỏi khớp bộ lọc." : "Ngân hàng câu hỏi đang trống. Tạo câu hỏi trước."}
                  </p>
                ) : (
                  <ul className="divide-y divide-line">
                    {questions.map((q) => (
                      <li key={q.id}>
                        <label className="flex cursor-pointer items-start gap-3 px-3 py-2.5 text-sm hover:bg-blue-soft/50">
                          <input
                            type="checkbox"
                            className="mt-0.5 size-4 accent-[rgb(var(--blue))]"
                            checked={selected.includes(q.id)}
                            onChange={(e) =>
                              setSelected((s) => (e.target.checked ? [...s, q.id] : s.filter((x) => x !== q.id)))
                            }
                          />
                          <span className="line-clamp-2 flex-1">{q.content}</span>
                          <span className="shrink-0 text-xs text-ink-muted">
                            {q.question_type === "MULTIPLE_CHOICE" ? "Nhiều đáp án" : "Một đáp án"}
                          </span>
                        </label>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button type="button" variant="outline">
                  Hủy
                </Button>
              </DialogClose>
              <Button type="submit" loading={save.isPending} disabled={!valid}>
                {quiz ? "Lưu bài kiểm tra" : "Tạo bài kiểm tra"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

function ResultsDialog({ quiz, onClose }: { quiz: Quiz; onClose: () => void }) {
  const attempts = useQuery({ queryKey: ["quiz-attempts", quiz.id], queryFn: () => instructorApi.quizAttempts(quiz.id) });
  const rows = attempts.data ?? [];
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent title={`Kết quả: ${quiz.title}`} className="max-w-3xl">
        {attempts.isLoading ? (
          <Spinner />
        ) : attempts.error ? (
          <ErrorNote message={errorMessage(attempts.error)} />
        ) : rows.length === 0 ? (
          <p className="text-sm text-ink-muted">Chưa có học viên nào làm bài này.</p>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Học viên</Th>
                <Th>Lượt</Th>
                <Th>Nộp lúc</Th>
                <Th>Điểm</Th>
                <Th>Kết quả</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.id}>
                  <Td>
                    <p className="font-medium">{a.full_name}</p>
                    <p className="text-xs text-ink-muted">{a.email}</p>
                  </Td>
                  <Td>{a.attempt_number}</Td>
                  <Td>{a.status === "IN_PROGRESS" ? "Đang làm" : formatDateTime(a.submitted_at)}</Td>
                  <Td className="numeric">{a.status === "SUBMITTED" ? formatScore(a.score) : "—"}</Td>
                  <Td>
                    {a.status === "TIMEOUT" ? (
                      <span className="text-ink-muted">Quá giờ</span>
                    ) : a.status === "IN_PROGRESS" ? (
                      <span className="text-ink-muted">—</span>
                    ) : a.is_passed ? (
                      <span className="text-blue">Đạt</span>
                    ) : (
                      <span className="text-red">Chưa đạt</span>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </DialogContent>
    </Dialog>
  );
}
