"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { categoryApi, instructorApi } from "@/lib/endpoints";
import type { CourseStatus } from "@/lib/types";
import { cn, COURSE_STATUS_LABEL, formatDate } from "@/lib/utils";
import { CourseCover } from "@/components/course/course-card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogClose, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { Field, Input, Select, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorNote, PageHeader, Pagination, Spinner, StatusBadge } from "@/components/ui/misc";

const FILTERS: (CourseStatus | undefined)[] = [undefined, "DRAFT", "PENDING", "PUBLISHED", "REJECTED"];

export default function InstructorCoursesPage() {
  const [status, setStatus] = React.useState<CourseStatus | undefined>();
  const [page, setPage] = React.useState(1);
  const [createOpen, setCreateOpen] = React.useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["instructor-courses", status, page],
    queryFn: () => instructorApi.courses({ status, page, limit: 12 }),
  });

  return (
    <>
      <PageHeader
        title="Khóa học của tôi"
        description="Soạn nội dung ở bản nháp, rồi gửi phê duyệt để khóa học được xuất bản."
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus /> Tạo khóa học
          </Button>
        }
      />

      <div className="mb-6 flex flex-wrap gap-2" role="group" aria-label="Lọc theo trạng thái">
        {FILTERS.map((s) => (
          <button
            key={s ?? "all"}
            onClick={() => {
              setStatus(s);
              setPage(1);
            }}
            aria-pressed={status === s}
            className={cn(
              "rounded-sm border px-3 py-1 text-[13px] font-medium",
              status === s ? "border-blue bg-blue text-on-blue" : "border-line-strong hover:bg-paper-sunk",
            )}
          >
            {s ? COURSE_STATUS_LABEL[s] : "Tất cả"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <Spinner />
      ) : error ? (
        <ErrorNote message={errorMessage(error)} />
      ) : data!.items.length === 0 ? (
        <EmptyState
          title={status ? `Không có khóa học ở trạng thái “${COURSE_STATUS_LABEL[status]}”` : "Bạn chưa có khóa học nào"}
          description="Tạo khóa học, thêm chương và bài học, rồi gửi phê duyệt."
          action={!status && <Button onClick={() => setCreateOpen(true)}>Tạo khóa học</Button>}
        />
      ) : (
        <>
          <ul className="divide-y divide-line border-y border-line">
            {data!.items.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/instructor/courses/${c.id}`}
                  className="flex flex-col gap-4 py-4 hover:bg-blue-soft/40 sm:flex-row sm:items-center sm:px-2"
                >
                  <CourseCover course={c} className="w-full sm:w-36" />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{c.title}</p>
                    <p className="mt-1 text-sm text-ink-muted">
                      {c.category?.name}, cập nhật {formatDate(c.updated_at)}
                    </p>
                    {c.status === "REJECTED" && c.rejection_reason && (
                      <p className="mt-2 rounded-sm bg-red-soft px-3 py-2 text-sm text-red">{c.rejection_reason}</p>
                    )}
                  </div>
                  <StatusBadge status={c.status} />
                </Link>
              </li>
            ))}
          </ul>
          <Pagination page={page} pages={data!.pages} onChange={setPage} />
        </>
      )}

      <CreateCourseDialog open={createOpen} onOpenChange={setCreateOpen} />
    </>
  );
}

function CreateCourseDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const router = useRouter();
  const categories = useQuery({ queryKey: ["categories"], queryFn: categoryApi.list, enabled: open });
  const [title, setTitle] = React.useState("");
  const [categoryId, setCategoryId] = React.useState("");
  const [description, setDescription] = React.useState("");

  const create = useMutation({
    mutationFn: () =>
      instructorApi.createCourse({
        title: title.trim(),
        category_id: Number(categoryId),
        description: description.trim() || null,
      }),
    onSuccess: ({ data, message }) => {
      toast.success(message);
      onOpenChange(false);
      router.push(`/instructor/courses/${data.id}`);
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title="Tạo khóa học" description="Khóa học mới được lưu ở trạng thái bản nháp.">
        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <Field label="Tên khóa học" htmlFor="c-title">
            <Input id="c-title" value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
          </Field>
          <Field
            label="Danh mục"
            htmlFor="c-cat"
            hint={categories.data?.length === 0 ? "Chưa có danh mục nào. Nhờ quản trị viên tạo danh mục trước." : undefined}
          >
            <Select id="c-cat" value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              <option value="">Chọn danh mục</option>
              {categories.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Mô tả ngắn" htmlFor="c-desc" hint="Có thể bổ sung sau.">
            <Textarea id="c-desc" value={description} onChange={(e) => setDescription(e.target.value)} />
          </Field>
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Hủy
              </Button>
            </DialogClose>
            <Button type="submit" loading={create.isPending} disabled={title.trim().length < 2 || !categoryId}>
              Tạo khóa học
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
