import Link from "next/link";
import type { Course } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Cover image, or – without one – a sunk panel with the title set in the serif. */
export function CourseCover({ course, className }: { course: Pick<Course, "title" | "thumbnail_url">; className?: string }) {
  if (course.thumbnail_url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={course.thumbnail_url}
        alt=""
        className={cn("aspect-[16/10] w-full rounded-md border border-line object-cover", className)}
      />
    );
  }
  return (
    <div
      aria-hidden
      className={cn(
        "relative flex aspect-[16/10] w-full items-end overflow-hidden rounded-md border border-line bg-paper-sunk p-5",
        className,
      )}
    >
      {/* Two hairlines and an amber stub: the progress bar, abstracted */}
      <span className="absolute inset-x-5 top-5 h-px bg-line" />
      <span className="absolute left-5 top-5 h-px w-1/3 bg-amber" />
      <p className="line-clamp-3 font-serif text-xl leading-tight text-ink-muted">{course.title}</p>
    </div>
  );
}

export function CourseCard({ course, href }: { course: Course; href?: string }) {
  return (
    <Link
      href={href ?? `/courses/${course.id}`}
      className="group flex h-full flex-col rounded-md border border-line bg-paper-raised p-3 transition-colors hover:border-line-strong"
    >
      <CourseCover course={course} className="border-0" />
      <div className="flex flex-1 flex-col px-2 pb-2 pt-4">
        {course.category && <p className="text-[13px] leading-5 text-ink-muted">{course.category.name}</p>}
        <h3 className="mt-1 line-clamp-2 text-xl leading-[26px] group-hover:underline group-hover:decoration-line-strong group-hover:underline-offset-4">
          {course.title}
        </h3>
        {course.instructor && <p className="mt-2 text-[15px] text-ink">{course.instructor.full_name}</p>}
      </div>
    </Link>
  );
}

export function CourseGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">{children}</div>;
}
