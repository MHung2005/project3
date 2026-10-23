"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { errorMessage } from "@/lib/api-client";
import { instructorApi } from "@/lib/endpoints";
import { COURSE_STATUS_LABEL } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Field, Select } from "@/components/ui/input";
import { EmptyState, ErrorNote, PageHeader, Spinner } from "@/components/ui/misc";
import { StudentsPanel } from "@/components/instructor/students-panel";

export default function InstructorStudentsPage() {
  const courses = useQuery({ queryKey: ["instructor-courses", "all"], queryFn: () => instructorApi.courses({ limit: 50 }) });
  const [courseId, setCourseId] = React.useState<number | null>(null);

  const items = courses.data?.items ?? [];
  const selected = items.find((c) => c.id === courseId) ?? items.find((c) => c.status === "PUBLISHED") ?? items[0];

  return (
    <>
      <PageHeader title="Tiến độ học viên" description="Xem ai đang học và đã hoàn thành đến đâu trong từng khóa học." />
      {courses.isLoading ? (
        <Spinner />
      ) : courses.error ? (
        <ErrorNote message={errorMessage(courses.error)} />
      ) : items.length === 0 ? (
        <EmptyState
          title="Bạn chưa có khóa học nào"
          action={
            <Button asChild>
              <Link href="/instructor/courses">Tạo khóa học</Link>
            </Button>
          }
        />
      ) : (
        <>
          <Field label="Khóa học" htmlFor="pick-course" className="mb-8 max-w-md">
            <Select id="pick-course" value={selected?.id} onChange={(e) => setCourseId(Number(e.target.value))}>
              {items.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title} ({COURSE_STATUS_LABEL[c.status].toLowerCase()})
                </option>
              ))}
            </Select>
          </Field>
          {selected && <StudentsPanel key={selected.id} courseId={selected.id} canEnroll={selected.status === "PUBLISHED"} />}
        </>
      )}
    </>
  );
}
