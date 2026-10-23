"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, PlayCircle } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { courseApi, learnApi } from "@/lib/endpoints";
import { useAuth } from "@/hooks/use-auth";
import type { Lesson } from "@/lib/types";
import { formatDuration } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";

/** Personalised call to action. The page itself is server-rendered without a token,
 *  so enrollment state is fetched again here with the signed-in user's token. */
export function EnrollPanel({ courseId, instructorId }: { courseId: number; instructorId: number }) {
  const { user, status } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();

  const detail = useQuery({
    queryKey: ["course", courseId, user?.id],
    queryFn: () => courseApi.detail(courseId),
    enabled: status === "authenticated",
  });

  const enroll = useMutation({
    mutationFn: () => courseApi.enroll(courseId),
    onSuccess: ({ message }) => {
      toast.success(message);
      qc.invalidateQueries({ queryKey: ["my-courses"] });
      router.push(`/learn/${courseId}`);
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const box = (children: React.ReactNode) => <div className="mt-5 space-y-3">{children}</div>;

  if (status === "loading" || (status === "authenticated" && detail.isLoading)) {
    return box(<div className="h-12 animate-pulse rounded bg-blue-soft" aria-hidden />);
  }

  if (!user) {
    return box(
      <>
        <Button asChild size="lg" className="w-full">
          <Link href={`/login?next=/courses/${courseId}`}>Đăng nhập để đăng ký</Link>
        </Button>
        <p className="text-sm text-ink-muted">Khóa học miễn phí. Bạn cần tài khoản để lưu tiến độ học.</p>
      </>,
    );
  }

  const ownsCourse = user.id === instructorId;
  if (ownsCourse || user.role === "ADMIN") {
    return box(
      <>
        <Button asChild size="lg" variant="outline" className="w-full">
          <Link href={user.role === "ADMIN" && !ownsCourse ? `/admin/courses/${courseId}` : `/instructor/courses/${courseId}`}>
            {ownsCourse ? "Quản lý khóa học" : "Xem trong trang quản trị"}
          </Link>
        </Button>
        {ownsCourse && <p className="text-sm text-ink-muted">Bạn là giảng viên của khóa học này.</p>}
      </>,
    );
  }

  if (detail.data?.is_enrolled) {
    return box(
      <Button asChild size="lg" className="w-full">
        <Link href={`/learn/${courseId}`}>Vào học</Link>
      </Button>,
    );
  }

  return box(
    <>
      <Button size="lg" className="w-full" loading={enroll.isPending} onClick={() => enroll.mutate()}>
        Đăng ký khóa học
      </Button>
      <p className="text-sm text-ink-muted">Miễn phí. Bắt đầu học ngay sau khi đăng ký.</p>
    </>,
  );
}

/** Learning materials sit in a private bucket; GET /lessons/{id} returns a short-lived presigned link. */
function PreviewDocument({ lessonId }: { lessonId: number }) {
  const { status } = useAuth();
  const lesson = useQuery({
    queryKey: ["lesson", lessonId],
    queryFn: () => learnApi.lesson(lessonId),
    enabled: status === "authenticated",
  });
  if (status !== "authenticated") {
    return (
      <p className="text-sm text-ink-muted">
        <Link href="/login" className="text-blue underline-offset-4 hover:underline">
          Đăng nhập
        </Link>{" "}
        để mở tài liệu học thử.
      </p>
    );
  }
  if (lesson.isLoading) return <p className="text-sm text-ink-muted">Đang lấy liên kết tài liệu…</p>;
  if (lesson.error || !lesson.data?.document_url) {
    return <p className="text-sm text-red">{errorMessage(lesson.error, "Tài liệu chưa sẵn sàng.")}</p>;
  }
  return (
    <Button asChild>
      <a href={lesson.data.document_url} target="_blank" rel="noreferrer">
        Mở tài liệu trong tab mới
      </a>
    </Button>
  );
}

/** Free-preview lessons open in a dialog without enrolling. */
export function FreePreviewList({ lessons }: { lessons: Lesson[] }) {
  const [active, setActive] = React.useState<Lesson | null>(null);
  return (
    <>
      <ul className="mt-3 divide-y divide-line rounded-lg border border-line bg-paper-raised">
        {lessons.map((l) => (
          <li key={l.id}>
            <button
              className="flex w-full items-center gap-3 px-5 py-3 text-left text-sm hover:text-blue"
              onClick={() => setActive(l)}
            >
              {l.lesson_type === "VIDEO" ? <PlayCircle className="size-4 text-blue" /> : <FileText className="size-4 text-blue" />}
              <span className="flex-1">{l.title}</span>
              {l.duration_seconds > 0 && <span className="text-xs text-ink-muted">{formatDuration(l.duration_seconds)}</span>}
            </button>
          </li>
        ))}
      </ul>
      <Dialog open={!!active} onOpenChange={(o) => !o && setActive(null)}>
        {active && (
          <DialogContent title={active.title} description="Bài học thử" className="max-w-3xl">
            {active.lesson_type === "VIDEO" && active.youtube_video_id ? (
              <div className="aspect-video overflow-hidden rounded-md bg-ink">
                <iframe
                  className="size-full"
                  src={`https://www.youtube-nocookie.com/embed/${active.youtube_video_id}?rel=0`}
                  title={active.title}
                  allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            ) : active.lesson_type === "DOCUMENT" ? (
              <PreviewDocument lessonId={active.id} />
            ) : (
              <p className="text-sm text-ink-muted">Bài học chưa có nội dung.</p>
            )}
          </DialogContent>
        )}
      </Dialog>
    </>
  );
}
