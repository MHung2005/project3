import Link from "next/link";
import type { Metadata } from "next";
import { serverApi } from "@/lib/server-api";
import type { Category, Course, Paginated } from "@/lib/types";
import { cn } from "@/lib/utils";
import { CourseCard, CourseGrid } from "@/components/course/course-card";
import { EmptyState, ErrorNote } from "@/components/ui/misc";

export const metadata: Metadata = { title: "Khóa học" };
export const dynamic = "force-dynamic";

const PAGE_SIZE = 12;

export default async function CoursesPage({
  searchParams,
}: {
  searchParams: { search?: string; category_id?: string; page?: string };
}) {
  const search = searchParams.search?.trim() ?? "";
  const categoryId = Number(searchParams.category_id) || undefined;
  const page = Math.max(1, Number(searchParams.page) || 1);

  let categories: Category[] = [];
  let result: Paginated<Course> | null = null;
  try {
    [categories, result] = await Promise.all([
      serverApi.categories(),
      serverApi.courses({ search, category_id: categoryId, page, limit: PAGE_SIZE }),
    ]);
  } catch {
    result = null;
  }

  const hrefFor = (p: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams();
    const merged = { search, category_id: categoryId, ...p };
    Object.entries(merged).forEach(([k, v]) => v !== undefined && v !== "" && qs.set(k, String(v)));
    const s = qs.toString();
    return s ? `/courses?${s}` : "/courses";
  };

  const activeCategory = categories.find((c) => c.id === categoryId);

  return (
    <div className="container py-12">
      <h1 className="text-2xl">{activeCategory ? activeCategory.name : "Tất cả khóa học"}</h1>
      {activeCategory?.description && <p className="mt-1 max-w-prose text-ink-muted">{activeCategory.description}</p>}

      <form action="/courses" role="search" className="mt-6 flex max-w-xl gap-2">
        {categoryId && <input type="hidden" name="category_id" value={categoryId} />}
        <label htmlFor="course-search" className="sr-only">
          Tìm khóa học
        </label>
        <input
          id="course-search"
          name="search"
          defaultValue={search}
          placeholder="Tìm theo tên khóa học"
          className="h-10 flex-1 rounded-sm border border-line-strong bg-paper-raised px-3 text-[15px] placeholder:text-ink-muted"
        />
        <button className="h-10 rounded border border-blue bg-blue px-4 text-[15px] font-medium text-on-blue hover:border-ink hover:bg-ink hover:text-paper">Tìm</button>
      </form>

      {categories.length > 0 && (
        <nav aria-label="Lọc theo danh mục" className="mt-6 flex flex-wrap gap-2">
          <Link
            href={hrefFor({ category_id: undefined, page: undefined })}
            className={cn(
              "rounded-sm border px-3 py-1 text-[13px] font-medium",
              !categoryId ? "border-blue bg-blue text-on-blue" : "border-line-strong text-ink hover:bg-paper-sunk",
            )}
          >
            Tất cả
          </Link>
          {categories.map((c) => (
            <Link
              key={c.id}
              href={hrefFor({ category_id: c.id, page: undefined })}
              className={cn(
                "rounded-sm border px-3 py-1 text-[13px] font-medium",
                c.id === categoryId ? "border-blue bg-blue text-on-blue" : "border-line-strong text-ink hover:bg-paper-sunk",
              )}
            >
              {c.name}
            </Link>
          ))}
        </nav>
      )}

      <div className="mt-10">
        {!result ? (
          <ErrorNote message="Chưa tải được danh sách khóa học. Kiểm tra backend đang chạy rồi tải lại trang." />
        ) : result.items.length === 0 ? (
          <EmptyState
            title={search ? `Không có khóa học nào khớp “${search}”` : "Danh mục này chưa có khóa học"}
            description="Thử từ khóa ngắn hơn hoặc chọn danh mục khác."
            action={
              <Link href="/courses" className="text-sm text-blue hover:underline underline-offset-4">
                Xem tất cả khóa học
              </Link>
            }
          />
        ) : (
          <>
            <p className="mb-6 text-sm text-ink-muted">{result.total} khóa học</p>
            <CourseGrid>
              {result.items.map((c) => (
                <CourseCard key={c.id} course={c} />
              ))}
            </CourseGrid>
            {result.pages > 1 && (
              <nav aria-label="Phân trang" className="mt-12 flex items-center justify-between text-sm">
                {page > 1 ? (
                  <Link href={hrefFor({ page: page - 1 })} className="text-blue hover:underline">
                    Trang trước
                  </Link>
                ) : (
                  <span />
                )}
                <span className="text-ink-muted">
                  Trang {page} / {result.pages}
                </span>
                {page < result.pages ? (
                  <Link href={hrefFor({ page: page + 1 })} className="text-blue hover:underline">
                    Trang sau
                  </Link>
                ) : (
                  <span />
                )}
              </nav>
            )}
          </>
        )}
      </div>
    </div>
  );
}
