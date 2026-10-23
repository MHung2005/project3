"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { errorMessage } from "@/lib/api-client";
import { learnApi } from "@/lib/endpoints";
import { useAuth } from "@/hooks/use-auth";
import { cn, formatDate, formatPercent } from "@/lib/utils";
import { CourseCover } from "@/components/course/course-card";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorNote, ProgressBar, Spinner } from "@/components/ui/misc";

type Tab = "IN_PROGRESS" | "COMPLETED";

export default function DashboardPage() {
  const user = useAuth((s) => s.user);
  const [tab, setTab] = React.useState<Tab>("IN_PROGRESS");
  const { data, isLoading, error } = useQuery({ queryKey: ["my-courses"], queryFn: () => learnApi.myCourses() });

  const items = (data ?? []).filter((m) => m.enrollment.status === tab);
  const counts = {
    IN_PROGRESS: data?.filter((m) => m.enrollment.status === "IN_PROGRESS").length ?? 0,
    COMPLETED: data?.filter((m) => m.enrollment.status === "COMPLETED").length ?? 0,
  };

  return (
    <div className="container py-10">
      <h1 className="text-2xl">Chào {user?.full_name.split(" ").pop()}, học tiếp nhé</h1>
      <p className="mt-1 text-ink-muted">Các khóa học bạn đã đăng ký và tiến độ của từng khóa.</p>

      <div role="tablist" aria-label="Trạng thái khóa học" className="mt-8 flex gap-1 border-b border-line">
        {(
          [
            ["IN_PROGRESS", "Đang học"],
            ["COMPLETED", "Đã hoàn thành"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            role="tab"
            aria-selected={tab === key}
            onClick={() => setTab(key)}
            className={cn(
              "-mb-px border-b-2 px-3 py-2.5 text-sm",
              tab === key ? "border-blue text-blue" : "border-transparent text-ink-muted hover:text-ink",
            )}
          >
            {label} <span className="text-ink-muted">({counts[key]})</span>
          </button>
        ))}
      </div>

      <div className="mt-6">
        {isLoading ? (
          <Spinner />
        ) : error ? (
          <ErrorNote message={errorMessage(error)} />
        ) : items.length === 0 ? (
          tab === "IN_PROGRESS" ? (
            <EmptyState
              title="Bạn chưa học khóa nào"
              description="Chọn một khóa học và bấm Đăng ký để bắt đầu. Tiến độ sẽ được ghi lại ở đây."
              action={
                <Button asChild>
                  <Link href="/courses">Tìm khóa học</Link>
                </Button>
              }
            />
          ) : (
            <EmptyState title="Chưa có khóa học hoàn thành" description="Hoàn thành mọi bài học và bài kiểm tra để kết thúc khóa." />
          )
        ) : (
          <ul className="divide-y divide-line">
            {items.map(({ enrollment, course }) => (
              <li key={enrollment.id} className="flex flex-col gap-4 py-5 sm:flex-row sm:items-center">
                <CourseCover course={course} className="w-full sm:w-44" />
                <div className="min-w-0 flex-1">
                  {course.category && <p className="text-xs text-ink-muted">{course.category.name}</p>}
                  <Link href={`/learn/${course.id}`} className="mt-0.5 block font-medium hover:text-blue">
                    {course.title}
                  </Link>
                  <div className="mt-3 flex items-center gap-3">
                    <ProgressBar value={enrollment.progress_percentage} className="max-w-xs" />
                    <span className="numeric text-[13px] text-amber-ink">{formatPercent(enrollment.progress_percentage)}</span>
                  </div>
                  <p className="mt-2 text-xs text-ink-muted">
                    {enrollment.status === "COMPLETED"
                      ? `Hoàn thành ngày ${formatDate(enrollment.completed_at)}`
                      : `Đăng ký ngày ${formatDate(enrollment.enrolled_at)}`}
                  </p>
                </div>
                <Button asChild variant={enrollment.status === "COMPLETED" ? "outline" : "primary"}>
                  <Link href={`/learn/${course.id}`}>
                    {enrollment.status === "COMPLETED" ? "Ôn lại" : enrollment.progress_percentage > 0 ? "Học tiếp" : "Bắt đầu học"}
                  </Link>
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
