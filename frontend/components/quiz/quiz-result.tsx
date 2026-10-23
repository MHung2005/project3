"use client";

import { Check, X } from "lucide-react";
import type { QuizResult } from "@/lib/types";
import { cn, formatDateTime, formatScore } from "@/lib/utils";

const LETTERS = "ABCDEFGHIJ";

/** Graded quiz: score beside the passing score and a worded verdict, then every question reviewed. */
export function QuizResultSheet({ result, title }: { result: QuizResult; title: string }) {
  const correct = result.review.filter((r) => r.is_correct).length;
  const timeout = result.status === "TIMEOUT";
  const passed = !timeout && result.is_passed;

  return (
    <article className="overflow-hidden rounded-lg border border-line bg-paper-raised">
      <header className="flex flex-col gap-6 border-b border-line p-6 sm:flex-row sm:items-start sm:gap-8">
        <div className="flex shrink-0 flex-col gap-2 sm:border-r sm:border-line sm:pr-8">
          <span className="numeric text-[40px] leading-[44px] tracking-tight" aria-label={`Điểm ${formatScore(result.score)} trên 10`}>
            {timeout ? "0" : formatScore(result.score)}/10
          </span>
          <span className={cn("inline-flex items-center gap-1 text-[13px] font-semibold", passed ? "text-blue" : "text-red")}>
            {passed ? <Check className="size-4" aria-hidden /> : <X className="size-4" aria-hidden />}
            {timeout ? "Nộp quá giờ" : passed ? "Đạt" : "Chưa đạt"}
          </span>
        </div>
        <div className="min-w-0">
          <h2 className="text-xl leading-[26px]">{title}</h2>
          <p className="numeric mt-1 text-[13px] text-ink-muted">Điểm đạt: {formatScore(result.passing_score)}/10</p>
          <p className="mt-3">
            Đúng <strong>{correct}</strong>/{result.review.length} câu.{" "}
            {timeout ? "Bài nộp sau khi hết giờ nên không được tính điểm." : passed ? "Bạn đã vượt qua bài kiểm tra." : "Xem lại các câu sai bên dưới rồi làm lại."}
          </p>
          <p className="mt-1 text-[13px] text-ink-muted">Nộp lúc {formatDateTime(result.submitted_at)}</p>
        </div>
      </header>

      <ol className="space-y-8 p-6">
        {result.review.map((r, i) => (
          <li key={r.question_id}>
            <div className="flex gap-3">
              <span className="w-6 shrink-0 pt-0.5" aria-hidden>
                {r.is_correct ? <Check className="size-5 text-blue" strokeWidth={2.5} /> : <X className="size-5 text-red" strokeWidth={2.5} />}
              </span>
              <p className="font-medium leading-7">
                <span className="mr-2 text-ink-muted">Câu {i + 1}.</span>
                <span className="whitespace-pre-line">{r.content}</span>
                <span className="sr-only">{r.is_correct ? " (đúng)" : " (sai)"}</span>
              </p>
            </div>
            <ul className="ml-9 mt-3 max-w-[560px] space-y-2">
              {[...r.options]
                .sort((a, b) => a.order_index - b.order_index)
                .map((opt, j) => {
                  const picked = r.user_selected.includes(opt.id);
                  const right = r.correct_options.includes(opt.id);
                  const wrongPick = picked && !right;
                  return (
                    <li
                      key={opt.id}
                      className={cn(
                        "flex items-start gap-3 rounded-sm border px-4 py-2.5 text-sm",
                        right && "border-blue ring-1 ring-inset ring-blue",
                        wrongPick && "border-red bg-red-soft ring-1 ring-inset ring-red",
                        !right && !wrongPick && "border-line-strong",
                      )}
                    >
                      <span
                        className={cn(
                          "numeric inline-flex size-6 shrink-0 items-center justify-center rounded-sm text-[13px]",
                          right ? "bg-blue text-on-blue" : wrongPick ? "bg-red text-on-red" : "text-ink-muted shadow-[inset_0_0_0_1px_rgb(var(--line-strong))]",
                        )}
                      >
                        {LETTERS[j]}
                      </span>
                      <span className="flex-1 pt-0.5">{opt.content}</span>
                      {right && (
                        <span className="inline-flex shrink-0 items-center gap-1 pt-0.5 text-[13px] font-medium text-blue">
                          <Check className="size-4" aria-hidden /> {picked ? "Bạn chọn đúng" : "Đáp án đúng"}
                        </span>
                      )}
                      {wrongPick && (
                        <span className="inline-flex shrink-0 items-center gap-1 pt-0.5 text-[13px] font-medium text-red">
                          <X className="size-4" aria-hidden /> Bạn chọn
                        </span>
                      )}
                    </li>
                  );
                })}
            </ul>
            {r.explanation && (
              <p className="ml-9 mt-3 max-w-prose rounded-sm bg-paper-sunk px-4 py-3 text-sm">
                <span className="font-medium">Giải thích: </span>
                {r.explanation}
              </p>
            )}
          </li>
        ))}
      </ol>
    </article>
  );
}
