"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { instructorApi } from "@/lib/endpoints";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { ErrorNote, Spinner, StatusBadge } from "@/components/ui/misc";
import { CurriculumEditor } from "@/components/instructor/curriculum-editor";
import { CourseInfoForm } from "@/components/instructor/course-info-form";
import { QuizManager } from "@/components/instructor/quiz-manager";
import { StudentsPanel } from "@/components/instructor/students-panel";

const TABS = [
  { key: "content", label: "Nội dung" },
  { key: "info", label: "Thông tin" },
  { key: "quizzes", label: "Bài kiểm tra" },
  { key: "students", label: "Học viên" },
] as const;
type TabKey = (typeof TABS)[number]["key"];

export default function CourseEditorPage({ params }: { params: { id: string } }) {
  const courseId = Number(params.id);
  const router = useRouter();
  const qc = useQueryClient();
  const [tab, setTab] = React.useState<TabKey>("content");
  const [confirmSubmit, setConfirmSubmit] = React.useState(false);
  const [confirmDelete, setConfirmDelete] = React.useState(false);

  const course = useQuery({ queryKey: ["instructor-course", courseId], queryFn: () => instructorApi.course(courseId) });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["instructor-course", courseId] });
    qc.invalidateQueries({ queryKey: ["instructor-courses"] });
  };

  const submit = useMutation({
    mutationFn: () => instructorApi.submitReview(courseId),
    onSuccess: ({ message }) => {
      toast.success(message);
      setConfirmSubmit(false);
      invalidate();
    },
    onError: (e) => {
      setConfirmSubmit(false);
      toast.error(errorMessage(e));
    },
  });

  const remove = useMutation({
    mutationFn: () => instructorApi.deleteCourse(courseId),
    onSuccess: ({ message }) => {
      toast.success(message);
      qc.invalidateQueries({ queryKey: ["instructor-courses"] });
      router.replace("/instructor/courses");
    },
    onError: (e) => {
      setConfirmDelete(false);
      toast.error(errorMessage(e));
    },
  });

  if (course.isLoading) return <Spinner />;
  if (course.error) return <ErrorNote message={errorMessage(course.error)} />;
  const c = course.data!;
  const locked = c.status === "PENDING";
  const canSubmit = c.status === "DRAFT" || c.status === "REJECTED";

  return (
    <>
      <Link href="/instructor/courses" className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-blue">
        <ChevronLeft className="size-4" aria-hidden /> Khóa học của tôi
      </Link>
      <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl">{c.title}</h1>
            <StatusBadge status={c.status} />
          </div>
          <p className="mt-1 text-sm text-ink-muted">
            {c.total_lessons} bài học, {c.quizzes.length} bài kiểm tra, {c.enrollment_count} học viên
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {c.status === "PUBLISHED" && (
            <Button asChild variant="outline">
              <Link href={`/courses/${c.id}`}>Xem trang công khai</Link>
            </Button>
          )}
          {canSubmit && (
            <Button onClick={() => setConfirmSubmit(true)} disabled={c.total_lessons === 0}>
              Gửi phê duyệt
            </Button>
          )}
        </div>
      </div>

      {c.status === "REJECTED" && c.rejection_reason && (
        <div role="status" className="mt-6 rounded-lg border border-red/40 bg-red-soft px-5 py-4">
          <p className="text-sm text-ink">Bị từ chối · nhận xét của quản trị viên:</p>
          <p className="mt-2 font-medium text-red">{c.rejection_reason}</p>
          <p className="mt-3 text-sm text-ink">Chỉnh sửa theo nhận xét rồi gửi phê duyệt lại.</p>
        </div>
      )}
      {locked && (
        <p className="mt-6 rounded border border-amber/30 bg-amber-soft/5 px-4 py-3 text-sm text-amber-ink">
          Khóa học đang chờ quản trị viên duyệt nên nội dung tạm thời bị khóa chỉnh sửa.
        </p>
      )}
      {canSubmit && c.total_lessons === 0 && (
        <p className="mt-6 text-sm text-ink-muted">Thêm ít nhất 1 bài học để có thể gửi phê duyệt.</p>
      )}

      <div role="tablist" aria-label="Biên soạn khóa học" className="mt-8 flex gap-1 overflow-x-auto overflow-y-hidden border-b border-line">
        {TABS.map((t) => (
          <button
            key={t.key}
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "-mb-px whitespace-nowrap border-b-2 px-3 py-2.5 text-sm",
              tab === t.key ? "border-blue text-blue" : "border-transparent text-ink-muted hover:text-ink",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="mt-8">
        {tab === "content" && <CurriculumEditor course={c} locked={locked} onChanged={invalidate} />}
        {tab === "info" && (
          <>
            <CourseInfoForm course={c} locked={locked} onSaved={invalidate} />
            {(c.status === "DRAFT" || c.status === "REJECTED") && (
              <section className="mt-12 max-w-2xl border-t border-line pt-6">
                <h2 className="text-base">Xóa khóa học</h2>
                <p className="mt-1 text-sm text-ink-muted">
                  Chỉ xóa được khóa học nháp hoặc bị từ chối và chưa có học viên. Toàn bộ chương, bài học sẽ bị xóa.
                </p>
                <Button variant="danger" className="mt-4" onClick={() => setConfirmDelete(true)}>
                  Xóa khóa học
                </Button>
              </section>
            )}
          </>
        )}
        {tab === "quizzes" && <QuizManager course={c} onChanged={invalidate} />}
        {tab === "students" && <StudentsPanel courseId={c.id} canEnroll={c.status === "PUBLISHED"} />}
      </div>

      <ConfirmDialog
        open={confirmSubmit}
        onOpenChange={setConfirmSubmit}
        title="Gửi khóa học để phê duyệt?"
        description="Trong lúc chờ duyệt, bạn không thể chỉnh sửa nội dung. Quản trị viên sẽ xuất bản hoặc gửi lại nhận xét."
        confirmLabel="Gửi phê duyệt"
        destructive={false}
        loading={submit.isPending}
        onConfirm={() => submit.mutate()}
      />
      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title={`Xóa khóa học “${c.title}”?`}
        description="Hành động này không thể hoàn tác."
        confirmLabel="Xóa khóa học"
        loading={remove.isPending}
        onConfirm={() => remove.mutate()}
      />
    </>
  );
}
