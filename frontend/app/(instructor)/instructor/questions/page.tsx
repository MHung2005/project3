"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { instructorApi } from "@/lib/endpoints";
import type { Question, QuestionInput, QuestionType } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ConfirmDialog, Dialog, DialogClose, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { Field, Input, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorNote, PageHeader, Pagination, Spinner } from "@/components/ui/misc";

const LETTERS = "ABCDEFGHIJ";

export default function QuestionBankPage() {
  const qc = useQueryClient();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [term, setTerm] = React.useState("");
  const [editing, setEditing] = React.useState<Question | "new" | null>(null);
  const [deleting, setDeleting] = React.useState<Question | null>(null);

  React.useEffect(() => {
    const t = setTimeout(() => {
      setTerm(search.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  const list = useQuery({
    queryKey: ["questions", page, term],
    queryFn: () => instructorApi.questions({ page, limit: 20, search: term || undefined }),
  });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["questions"] });
    qc.invalidateQueries({ queryKey: ["question-bank-all"] });
  };

  const remove = useMutation({
    mutationFn: (id: number) => instructorApi.deleteQuestion(id),
    onSuccess: ({ message }) => {
      toast.success(message);
      setDeleting(null);
      refresh();
    },
    onError: (e) => {
      setDeleting(null);
      toast.error(errorMessage(e));
    },
  });

  return (
    <>
      <PageHeader
        title="Ngân hàng câu hỏi"
        description="Câu hỏi trắc nghiệm dùng chung cho mọi bài kiểm tra của bạn."
        actions={
          <Button onClick={() => setEditing("new")}>
            <Plus /> Tạo câu hỏi
          </Button>
        }
      />
      <Input
        placeholder="Tìm theo nội dung câu hỏi"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-6 max-w-sm"
        aria-label="Tìm câu hỏi"
      />

      {list.isLoading ? (
        <Spinner />
      ) : list.error ? (
        <ErrorNote message={errorMessage(list.error)} />
      ) : list.data!.items.length === 0 ? (
        <EmptyState
          title={term ? "Không có câu hỏi khớp từ khóa" : "Ngân hàng câu hỏi đang trống"}
          description="Mỗi câu hỏi có từ 2 đến 10 phương án, một hoặc nhiều đáp án đúng."
          action={!term && <Button onClick={() => setEditing("new")}>Tạo câu hỏi đầu tiên</Button>}
        />
      ) : (
        <>
          <p className="mb-3 text-sm text-ink-muted">{list.data!.total} câu hỏi</p>
          <ul className="divide-y divide-line border-y border-line">
            {list.data!.items.map((q) => (
              <li key={q.id} className="flex flex-col gap-3 py-4 sm:flex-row">
                <div className="min-w-0 flex-1">
                  <p className="whitespace-pre-line font-medium">{q.content}</p>
                  <ul className="mt-2 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
                    {[...q.options]
                      .sort((a, b) => a.order_index - b.order_index)
                      .map((o, i) => (
                        <li key={o.id} className={cn(o.is_correct ? "text-blue" : "text-ink-muted")}>
                          {LETTERS[i]}. {o.content}
                          {o.is_correct && <span className="sr-only"> (đáp án đúng)</span>}
                        </li>
                      ))}
                  </ul>
                  <p className="mt-2 text-xs text-ink-muted">
                    {q.question_type === "MULTIPLE_CHOICE" ? "Nhiều đáp án đúng" : "Một đáp án đúng"}, tạo ngày{" "}
                    {formatDate(q.created_at)}
                  </p>
                </div>
                <div className="flex shrink-0 items-start gap-1">
                  <Button variant="outline" size="sm" onClick={() => setEditing(q)}>
                    Sửa
                  </Button>
                  <Button variant="ghost" size="sm" aria-label="Xóa câu hỏi" onClick={() => setDeleting(q)}>
                    <Trash2 />
                  </Button>
                </div>
              </li>
            ))}
          </ul>
          <Pagination page={page} pages={list.data!.pages} onChange={setPage} />
        </>
      )}

      {editing && (
        <QuestionDialog
          question={editing === "new" ? undefined : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            refresh();
          }}
        />
      )}
      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(o) => !o && setDeleting(null)}
        title="Xóa câu hỏi này?"
        description="Không xóa được câu hỏi đang nằm trong một bài kiểm tra."
        confirmLabel="Xóa câu hỏi"
        loading={remove.isPending}
        onConfirm={() => deleting && remove.mutate(deleting.id)}
      />
    </>
  );
}

interface OptionDraft {
  key: number;
  content: string;
  is_correct: boolean;
}

function QuestionDialog({
  question,
  onClose,
  onSaved,
}: {
  question?: Question;
  onClose: () => void;
  onSaved: () => void;
}) {
  const keyRef = React.useRef(0);
  const newKey = () => ++keyRef.current;
  const [content, setContent] = React.useState(question?.content ?? "");
  const [type, setType] = React.useState<QuestionType>(question?.question_type ?? "SINGLE_CHOICE");
  const [explanation, setExplanation] = React.useState(question?.explanation ?? "");
  const [options, setOptions] = React.useState<OptionDraft[]>(() =>
    question
      ? [...question.options]
          .sort((a, b) => a.order_index - b.order_index)
          .map((o) => ({ key: newKey(), content: o.content, is_correct: o.is_correct }))
      : [0, 1, 2, 3].map(() => ({ key: newKey(), content: "", is_correct: false })),
  );

  const save = useMutation({
    mutationFn: () => {
      const body: QuestionInput = {
        content: content.trim(),
        question_type: type,
        explanation: explanation.trim() || null,
        options: options
          .filter((o) => o.content.trim())
          .map((o, i) => ({ content: o.content.trim(), is_correct: o.is_correct, order_index: i + 1 })),
      };
      return question ? instructorApi.updateQuestion(question.id, body) : instructorApi.createQuestion(body);
    },
    onSuccess: ({ message }) => {
      toast.success(message);
      onSaved();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const filled = options.filter((o) => o.content.trim());
  const correct = filled.filter((o) => o.is_correct).length;
  const problem =
    content.trim().length < 5
      ? "Nội dung câu hỏi cần ít nhất 5 ký tự."
      : filled.length < 2
        ? "Cần ít nhất 2 phương án."
        : correct === 0
          ? "Đánh dấu ít nhất 1 đáp án đúng."
          : type === "SINGLE_CHOICE" && correct !== 1
            ? "Câu một đáp án chỉ được có đúng 1 đáp án đúng."
            : null;

  const markCorrect = (key: number, checked: boolean) =>
    setOptions((opts) =>
      opts.map((o) =>
        type === "SINGLE_CHOICE" ? { ...o, is_correct: o.key === key } : o.key === key ? { ...o, is_correct: checked } : o,
      ),
    );

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent title={question ? "Sửa câu hỏi" : "Tạo câu hỏi"} className="max-w-2xl">
        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            if (!problem) save.mutate();
          }}
        >
          <Field label="Nội dung câu hỏi" htmlFor="qs-content">
            <Textarea id="qs-content" rows={3} value={content} onChange={(e) => setContent(e.target.value)} autoFocus />
          </Field>
          <fieldset>
            <legend className="field-label">Kiểu câu hỏi</legend>
            <div className="flex gap-2">
              {(
                [
                  ["SINGLE_CHOICE", "Một đáp án đúng"],
                  ["MULTIPLE_CHOICE", "Nhiều đáp án đúng"],
                ] as const
              ).map(([value, label]) => (
                <label
                  key={value}
                  className={cn(
                    "cursor-pointer rounded border px-3 py-2 text-sm",
                    type === value ? "border-blue bg-blue-soft text-blue" : "border-line hover:border-blue/50",
                  )}
                >
                  <input
                    type="radio"
                    className="sr-only"
                    checked={type === value}
                    onChange={() => {
                      setType(value);
                      if (value === "SINGLE_CHOICE" && correct > 1) {
                        const first = options.find((o) => o.is_correct)?.key;
                        setOptions((opts) => opts.map((o) => ({ ...o, is_correct: o.key === first })));
                      }
                    }}
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="field-label">Phương án (đánh dấu đáp án đúng)</legend>
            <ul className="space-y-2">
              {options.map((o, i) => (
                <li key={o.key} className="flex items-center gap-2">
                  <input
                    type={type === "SINGLE_CHOICE" ? "radio" : "checkbox"}
                    name="correct-option"
                    aria-label={`Phương án ${LETTERS[i]} là đáp án đúng`}
                    checked={o.is_correct}
                    onChange={(e) => markCorrect(o.key, e.target.checked)}
                    className="size-4 shrink-0 accent-[rgb(var(--blue))]"
                  />
                  <span className="w-5 shrink-0 text-sm font-medium text-blue">{LETTERS[i]}.</span>
                  <Input
                    aria-label={`Nội dung phương án ${LETTERS[i]}`}
                    value={o.content}
                    onChange={(e) =>
                      setOptions((opts) => opts.map((x) => (x.key === o.key ? { ...x, content: e.target.value } : x)))
                    }
                  />
                  <button
                    type="button"
                    aria-label={`Xóa phương án ${LETTERS[i]}`}
                    disabled={options.length <= 2}
                    onClick={() => setOptions((opts) => opts.filter((x) => x.key !== o.key))}
                    className="rounded p-2 text-ink-muted hover:bg-red/10 hover:text-red disabled:opacity-30"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </li>
              ))}
            </ul>
            {options.length < 10 && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="mt-2"
                onClick={() => setOptions((opts) => [...opts, { key: newKey(), content: "", is_correct: false }])}
              >
                <Plus /> Thêm phương án
              </Button>
            )}
          </fieldset>

          <Field label="Lời giải thích" htmlFor="qs-expl" hint="Học viên thấy lời giải sau khi nộp bài.">
            <Textarea id="qs-expl" rows={2} value={explanation} onChange={(e) => setExplanation(e.target.value)} />
          </Field>

          {problem && <p className="text-sm text-ink-muted">{problem}</p>}

          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Hủy
              </Button>
            </DialogClose>
            <Button type="submit" loading={save.isPending} disabled={!!problem}>
              {question ? "Lưu câu hỏi" : "Tạo câu hỏi"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
