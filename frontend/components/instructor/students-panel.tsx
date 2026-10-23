"use client";

import * as React from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { instructorApi } from "@/lib/endpoints";
import { formatDate, formatPercent } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, EmptyState, ErrorNote, ProgressBar, Spinner } from "@/components/ui/misc";
import { Table, Td, Th } from "@/components/ui/table";

/** Enrolled learners with their progress, plus "add a learner by email". */
export function StudentsPanel({ courseId, canEnroll }: { courseId: number; canEnroll: boolean }) {
  const students = useQuery({ queryKey: ["course-students", courseId], queryFn: () => instructorApi.students(courseId) });
  const [email, setEmail] = React.useState("");
  const [filter, setFilter] = React.useState("");

  const add = useMutation({
    mutationFn: () => instructorApi.enrollStudent(courseId, email.trim()),
    onSuccess: ({ message }) => {
      toast.success(message);
      setEmail("");
      students.refetch();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const rows = (students.data ?? []).filter(
    (s) => s.full_name.toLowerCase().includes(filter.toLowerCase()) || s.email.toLowerCase().includes(filter.toLowerCase()),
  );
  const avg = students.data?.length
    ? students.data.reduce((sum, s) => sum + s.progress_percentage, 0) / students.data.length
    : 0;
  const completed = students.data?.filter((s) => s.status === "COMPLETED").length ?? 0;

  return (
    <div className="max-w-5xl">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        {students.data && students.data.length > 0 ? (
          <dl className="flex gap-8 text-sm">
            <div>
              <dt className="text-ink-muted">Học viên</dt>
              <dd className="text-xl font-medium">{students.data.length}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Đã hoàn thành</dt>
              <dd className="text-xl font-medium">{completed}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Tiến độ trung bình</dt>
              <dd className="text-xl font-medium">{formatPercent(avg)}</dd>
            </div>
          </dl>
        ) : (
          <span />
        )}
        {canEnroll ? (
          <form
            className="flex w-full max-w-md gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (email.trim()) add.mutate();
            }}
          >
            <label htmlFor="enroll-email" className="sr-only">
              Email học viên
            </label>
            <Input
              id="enroll-email"
              type="email"
              placeholder="Email học viên cần thêm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button type="submit" loading={add.isPending} disabled={!email.trim()}>
              Thêm học viên
            </Button>
          </form>
        ) : (
          <p className="text-sm text-ink-muted">Thêm học viên trực tiếp được sau khi khóa học đã xuất bản.</p>
        )}
      </div>

      <div className="mt-6">
        {students.isLoading ? (
          <Spinner />
        ) : students.error ? (
          <ErrorNote message={errorMessage(students.error)} />
        ) : students.data!.length === 0 ? (
          <EmptyState title="Chưa có học viên" description="Học viên tự đăng ký trên trang khóa học, hoặc bạn thêm bằng email." />
        ) : (
          <>
            {students.data!.length > 8 && (
              <Input
                placeholder="Lọc theo tên hoặc email"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="mb-3 max-w-xs"
              />
            )}
            <Table>
              <thead>
                <tr>
                  <Th>Học viên</Th>
                  <Th>Đăng ký</Th>
                  <Th>Bài học</Th>
                  <Th className="w-56">Tiến độ</Th>
                  <Th>Trạng thái</Th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr key={s.user_id}>
                    <Td>
                      <div className="flex items-center gap-3">
                        <Avatar name={s.full_name} src={s.avatar_url} size={32} />
                        <div className="min-w-0">
                          <p className="truncate font-medium">{s.full_name}</p>
                          <p className="truncate text-xs text-ink-muted">{s.email}</p>
                        </div>
                      </div>
                    </Td>
                    <Td>{formatDate(s.enrolled_at)}</Td>
                    <Td className="numeric">
                      {s.completed_lessons}/{s.total_lessons}
                    </Td>
                    <Td>
                      <div className="flex items-center gap-3">
                        <ProgressBar value={s.progress_percentage} />
                        <span className="w-10 text-right text-xs numeric text-ink-muted">
                          {formatPercent(s.progress_percentage)}
                        </span>
                      </div>
                    </Td>
                    <Td>
                      {s.status === "COMPLETED" ? (
                        <span className="text-blue">Hoàn thành {formatDate(s.completed_at)}</span>
                      ) : (
                        <span className="text-ink-muted">Đang học</span>
                      )}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </>
        )}
      </div>
    </div>
  );
}
