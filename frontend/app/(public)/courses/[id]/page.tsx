import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { serverApi, ServerApiError } from "@/lib/server-api";
import type { CourseDetail } from "@/lib/types";
import { formatDate, formatDuration } from "@/lib/utils";
import { CourseCover } from "@/components/course/course-card";
import { CourseOutline } from "@/components/course/course-outline";
import { EnrollPanel, FreePreviewList } from "@/components/course/enroll-panel";
import { Avatar, ErrorNote } from "@/components/ui/misc";

export const dynamic = "force-dynamic";

async function load(id: number): Promise<CourseDetail | null> {
  try {
    return await serverApi.course(id);
  } catch (e) {
    if (e instanceof ServerApiError && e.status === 404) notFound();
    return null;
  }
}

export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  const id = Number(params.id);
  if (!id) return {};
  try {
    const c = await serverApi.course(id);
    return { title: c.title, description: c.description?.slice(0, 160) ?? undefined };
  } catch {
    return { title: "Khóa học" };
  }
}

export default async function CourseDetailPage({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  if (!id) notFound();
  const course = await load(id);
  if (!course) {
    return (
      <div className="container py-12">
        <ErrorNote message="Chưa tải được khóa học. Kiểm tra backend đang chạy rồi tải lại trang." />
      </div>
    );
  }

  const previews = course.chapters.flatMap((c) => c.lessons).filter((l) => l.is_free_preview && !l.is_locked);

  return (
    <div className="container py-12">
      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0">
          {course.category && <p className="text-sm text-ink-muted">{course.category.name}</p>}
          <h1 className="mt-2 text-3xl">{course.title}</h1>
          <dl className="mt-5 flex flex-wrap gap-x-8 gap-y-2 text-sm">
            <div>
              <dt className="text-ink-muted">Bài học</dt>
              <dd className="font-medium">{course.total_lessons}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Thời lượng video</dt>
              <dd className="font-medium">{formatDuration(course.total_duration_seconds)}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Bài kiểm tra</dt>
              <dd className="font-medium">{course.quizzes.length}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Học viên</dt>
              <dd className="font-medium">{course.enrollment_count}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Cập nhật</dt>
              <dd className="font-medium">{formatDate(course.updated_at)}</dd>
            </div>
          </dl>

          {course.description && (
            <section className="mt-10">
              <h2 className="text-lg">Giới thiệu khóa học</h2>
              <p className="mt-3 max-w-prose whitespace-pre-line leading-7">{course.description}</p>
            </section>
          )}

          {previews.length > 0 && (
            <section className="mt-10">
              <h2 className="text-lg">Học thử miễn phí</h2>
              <FreePreviewList lessons={previews} />
            </section>
          )}

          <section className="mt-10">
            <h2 className="mb-4 text-lg">Đề cương</h2>
            <CourseOutline chapters={course.chapters} quizzes={course.quizzes} />
          </section>

          {course.instructor && (
            <section className="mt-10">
              <h2 className="text-lg">Giảng viên</h2>
              <div className="mt-4 flex items-center gap-3">
                <Avatar name={course.instructor.full_name} src={course.instructor.avatar_url} size={44} />
                <p className="font-medium">{course.instructor.full_name}</p>
              </div>
            </section>
          )}
        </div>

        <aside className="lg:sticky lg:top-24 lg:self-start">
          <CourseCover course={course} />
          <EnrollPanel courseId={course.id} instructorId={course.instructor_id} />
        </aside>
      </div>
    </div>
  );
}
