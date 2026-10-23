import * as React from "react";
import { Loader2 } from "lucide-react";
import { cn, COURSE_STATUS_LABEL, initials } from "@/lib/utils";
import type { CourseStatus } from "@/lib/types";

export function Spinner({ className, label = "Đang tải" }: { className?: string; label?: string }) {
  return (
    <div role="status" className={cn("flex items-center justify-center gap-2 py-12 text-sm text-ink-muted", className)}>
      <Loader2 className="size-4 animate-spin" aria-hidden />
      {label}
    </div>
  );
}

// Badge tones: neutral (draft), pending (amber), positive (blue), negative (red)
const STATUS_STYLE: Record<CourseStatus, string> = {
  DRAFT: "bg-paper-sunk text-ink-muted",
  PENDING: "bg-amber-soft text-amber-ink",
  PUBLISHED: "bg-blue-soft text-blue",
  REJECTED: "bg-red-soft text-red",
};

const badgeBase = "inline-flex items-center gap-1 whitespace-nowrap rounded-sm px-2 text-xs font-medium leading-5";

export function StatusBadge({ status, className }: { status: CourseStatus; className?: string }) {
  return <span className={cn(badgeBase, STATUS_STYLE[status], className)}>{COURSE_STATUS_LABEL[status]}</span>;
}

export function Tag({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn(badgeBase, "text-ink shadow-[inset_0_0_0_1px_rgb(var(--line-strong))]", className)}>{children}</span>;
}

/** Amber fill on a sunk track. `value` is 0–100; `threshold` draws an ink tick (e.g. the 80% rule). */
export function ProgressBar({
  value,
  className,
  label,
  threshold,
}: {
  value: number;
  className?: string;
  label?: string;
  threshold?: number;
}) {
  const v = Math.max(0, Math.min(100, value));
  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(v)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label ?? "Tiến độ"}
      className={cn(
        "relative h-1.5 w-full rounded-xs bg-paper-sunk shadow-[inset_0_0_0_1px_rgb(var(--line))]",
        className,
      )}
    >
      <div className="h-full rounded-xs bg-amber transition-[width] duration-200 ease-out" style={{ width: `${v}%` }} />
      {threshold != null && (
        <span className="absolute -bottom-[3px] -top-[3px] -ml-px w-0.5 rounded-xs bg-ink" style={{ left: `${threshold}%` }} />
      )}
    </div>
  );
}

export function Avatar({ name, src, size = 36 }: { name: string; src?: string | null; size?: number }) {
  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt=""
        width={size}
        height={size}
        className="shrink-0 rounded-full object-cover"
        style={{ width: size, height: size }}
      />
    );
  }
  return (
    <span
      aria-hidden
      className="inline-flex shrink-0 items-center justify-center rounded-full bg-blue-soft font-medium text-blue"
      style={{ width: size, height: size, fontSize: size * 0.38 }}
    >
      {initials(name)}
    </span>
  );
}

export function EmptyState({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-lg border border-dashed border-line px-6 py-12 text-center", className)}>
      <p className="font-serif text-xl">{title}</p>
      {description && <p className="mx-auto mt-1 max-w-md text-sm text-ink-muted">{description}</p>}
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  );
}

export function ErrorNote({ message, className }: { message: string; className?: string }) {
  return (
    <div role="alert" className={cn("rounded border border-red/40 bg-red-soft px-4 py-3 text-sm text-red", className)}>
      {message}
    </div>
  );
}

export function Pagination({ page, pages, onChange }: { page: number; pages: number; onChange: (page: number) => void }) {
  if (pages <= 1) return null;
  const btn =
    "rounded px-3 py-1.5 text-blue hover:bg-blue-soft disabled:pointer-events-none disabled:text-ink-muted/60";
  return (
    <nav aria-label="Phân trang" className="mt-8 flex items-center justify-between gap-4 text-sm">
      <button className={btn} disabled={page <= 1} onClick={() => onChange(page - 1)}>
        Trang trước
      </button>
      <span className="text-ink-muted">
        Trang {page} / {pages}
      </span>
      <button className={btn} disabled={page >= pages} onClick={() => onChange(page + 1)}>
        Trang sau
      </button>
    </nav>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-[28px] leading-[34px]">{title}</h1>
        {description && <p className="mt-1 max-w-prose text-ink-muted">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}
