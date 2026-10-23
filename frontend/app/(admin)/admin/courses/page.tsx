"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { errorMessage } from "@/lib/api-client";
import { adminApi } from "@/lib/endpoints";
import type { CourseStatus } from "@/lib/types";
import { cn, COURSE_STATUS_LABEL, formatDateTime } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorNote, PageHeader, Pagination, Spinner, StatusBadge } from "@/components/ui/misc";
import { Table, Td, Th } from "@/components/ui/table";

const FILTERS: (CourseStatus | undefined)[] = ["PENDING", "PUBLISHED", "REJECTED", "DRAFT", undefined];

export default function AdminCoursesPage() {
  const [status, setStatus] = React.useState<CourseStatus | undefined>("PENDING");
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [term, setTerm] = React.useState("");

  React.useEffect(() => {
    const t = setTimeout(() => {
      setTerm(search.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  const list = useQuery({
    queryKey: ["admin-courses", status, page, term],
    queryFn: () => adminApi.courses({ status, page, limit: 20, search: term || undefined }),
  });

  return (
    <>
      <PageHeader
        title="Kiểm duyệt khóa học"
        description="Xem nội dung khóa học giảng viên gửi lên, rồi xuất bản hoặc gửi lại nhận xét."
      />
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2" role="group" aria-label="Lọc theo trạng thái">
          {FILTERS.map((s) => (
            <button
              key={s ?? "all"}
              aria-pressed={status === s}
              onClick={() => {
                setStatus(s);
                setPage(1);
              }}
              className={cn(
                "rounded-sm border px-3 py-1 text-[13px] font-medium",
                status === s ? "border-blue bg-blue text-on-blue" : "border-line-strong hover:bg-paper-sunk",
              )}
            >
              {s ? COURSE_STATUS_LABEL[s] : "Tất cả"}
            </button>
          ))}
        </div>
        <Input
          placeholder="Tìm theo tên khóa học"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:max-w-xs"
          aria-label="Tìm khóa học"
        />
      </div>

      {list.isLoading ? (
        <Spinner />
      ) : list.error ? (
        <ErrorNote message={errorMessage(list.error)} />
      ) : list.data!.items.length === 0 ? (
        <EmptyState
          title={status === "PENDING" ? "Không có khóa học nào chờ duyệt" : "Không có khóa học phù hợp"}
          description={status === "PENDING" ? "Khi giảng viên gửi phê duyệt, khóa học sẽ xuất hiện ở đây." : undefined}
        />
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>Khóa học</Th>
                <Th>Giảng viên</Th>
                <Th>Danh mục</Th>
                <Th>Cập nhật</Th>
                <Th>Trạng thái</Th>
              </tr>
            </thead>
            <tbody>
              {list.data!.items.map((c) => (
                <tr key={c.id} className="hover:bg-blue-soft/40">
                  <Td>
                    <Link href={`/admin/courses/${c.id}`} className="font-medium text-blue hover:underline underline-offset-4">
                      {c.title}
                    </Link>
                  </Td>
                  <Td>{c.instructor?.full_name ?? "—"}</Td>
                  <Td className="text-ink-muted">{c.category?.name ?? "—"}</Td>
                  <Td className="text-ink-muted">{formatDateTime(c.updated_at)}</Td>
                  <Td>
                    <StatusBadge status={c.status} />
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
          <Pagination page={page} pages={list.data!.pages} onChange={setPage} />
        </>
      )}
    </>
  );
}
