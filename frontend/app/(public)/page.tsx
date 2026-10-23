import Link from "next/link";
import { Search } from "lucide-react";
import { serverApi } from "@/lib/server-api";
import type { Category, Course } from "@/lib/types";
import { CourseCard, CourseGrid } from "@/components/course/course-card";
import { EmptyState, ErrorNote } from "@/components/ui/misc";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let categories: Category[] = [];
  let courses: Course[] = [];
  let total = 0;
  let failed = false;
  try {
    const [cats, list] = await Promise.all([serverApi.categories(), serverApi.courses({ limit: 8 })]);
    categories = cats;
    courses = list.items;
    total = list.total;
  } catch {
    failed = true;
  }

  return (
    <>
      <section className="border-b border-line">
        <div className="container py-12 sm:py-20">
          <div className="max-w-3xl">
            <h1 className="text-[36px] leading-[40px] tracking-tight sm:text-[56px] sm:leading-[60px]">
              Học có cấu trúc. Tiến độ trung thực.
            </h1>
            <p className="mt-6 max-w-xl text-[17px] leading-7 text-ink">
              Mỗi khóa học chia thành chương và bài. Bài học chỉ được tính hoàn thành khi bạn xem hơn 80% video, bài
              kiểm tra được chấm tự động theo điểm đạt.
            </p>
            <div>
              <form action="/courses" className="mt-8 flex max-w-xl gap-2" role="search">
                <label htmlFor="hero-search" className="sr-only">
                  Tìm khóa học
                </label>
                <div className="relative flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-muted" aria-hidden />
                  <input
                    id="hero-search"
                    name="search"
                    placeholder="Tìm theo tên khóa học, ví dụ: React"
                    className="h-12 w-full rounded-sm border border-line-strong bg-paper-raised pl-10 pr-3 text-[15px] placeholder:text-ink-muted"
                  />
                </div>
                <button className="h-12 rounded border border-blue bg-blue px-5 text-[15px] font-medium text-on-blue hover:border-ink hover:bg-ink hover:text-paper">Tìm</button>
              </form>
            </div>
          </div>
        </div>
      </section>

      <div className="container py-14">
        {failed ? (
          <ErrorNote message="Chưa tải được danh sách khóa học. Kiểm tra backend đang chạy ở cổng 8000 rồi tải lại trang." />
        ) : (
          <>
            {categories.length > 0 && (
              <nav aria-label="Danh mục" className="mb-12 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                <span className="text-ink-muted">Danh mục:</span>
                {categories.map((c) => (
                  <Link key={c.id} href={`/courses?category_id=${c.id}`} className="text-blue hover:underline underline-offset-4">
                    {c.name}
                  </Link>
                ))}
              </nav>
            )}
            <div className="mb-6 flex items-baseline justify-between gap-4">
              <h2 className="text-xl">Khóa học mới xuất bản</h2>
              {total > courses.length && (
                <Link href="/courses" className="text-sm text-blue hover:underline underline-offset-4">
                  Xem tất cả {total} khóa học
                </Link>
              )}
            </div>
            {courses.length === 0 ? (
              <EmptyState
                title="Chưa có khóa học nào được xuất bản"
                description="Khi giảng viên gửi khóa học và quản trị viên phê duyệt, khóa học sẽ xuất hiện ở đây."
              />
            ) : (
              <CourseGrid>
                {courses.map((c) => (
                  <CourseCard key={c.id} course={c} />
                ))}
              </CourseGrid>
            )}
          </>
        )}
      </div>
    </>
  );
}
