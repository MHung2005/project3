"use client";

import type { SafeQuestion } from "@/lib/types";
import { cn } from "@/lib/utils";

const LETTERS = "ABCDEFGHIJ";

/** One question while taking a quiz. Options never carry correctness (SDD §4.4). */
export function QuestionItem({
  index,
  question,
  selected,
  onChange,
}: {
  index: number;
  question: SafeQuestion;
  selected: number[];
  onChange: (ids: number[]) => void;
}) {
  const multiple = question.question_type === "MULTIPLE_CHOICE";
  const name = `q-${question.id}`;

  const toggle = (id: number) => {
    if (!multiple) return onChange([id]);
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  };

  return (
    <fieldset id={`question-${question.id}`} className="scroll-mt-28">
      <legend className="flex gap-3 text-base font-medium leading-7">
        <span className="shrink-0 text-ink-muted">Câu {index + 1}.</span>
        <span className="whitespace-pre-line">{question.content}</span>
      </legend>
      {multiple && <p className="ml-14 mt-1 text-xs text-ink-muted">Chọn tất cả đáp án đúng</p>}
      <div className="ml-0 mt-3 space-y-2 sm:ml-14">
        {[...question.options]
          .sort((a, b) => a.order_index - b.order_index)
          .map((opt, i) => {
            const checked = selected.includes(opt.id);
            return (
              <label
                key={opt.id}
                className={cn(
                  "flex max-w-[560px] cursor-pointer items-start gap-3 rounded-sm border px-4 py-2.5 text-[15px] transition-colors has-[:focus-visible]:shadow-[0_0_0_2px_rgb(var(--paper)),0_0_0_4px_rgb(var(--blue))]",
                  checked ? "border-blue bg-blue-soft ring-1 ring-inset ring-blue" : "border-line-strong bg-paper-raised hover:bg-paper-sunk",
                )}
              >
                <input
                  type={multiple ? "checkbox" : "radio"}
                  name={name}
                  checked={checked}
                  onChange={() => toggle(opt.id)}
                  className="sr-only"
                />
                <span
                  className={cn(
                    "numeric inline-flex size-6 shrink-0 items-center justify-center text-[13px]",
                    multiple ? "rounded-xs" : "rounded-sm",
                    checked ? "bg-blue text-on-blue" : "text-ink-muted shadow-[inset_0_0_0_1px_rgb(var(--line-strong))]",
                  )}
                  aria-hidden
                >
                  {LETTERS[i]}
                </span>
                <span className="whitespace-pre-line pt-0.5">{opt.content}</span>
              </label>
            );
          })}
      </div>
    </fieldset>
  );
}
