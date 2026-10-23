"use client";

import * as React from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { categoryApi, instructorApi } from "@/lib/endpoints";
import type { CourseDetail } from "@/lib/types";
import { CourseCover } from "@/components/course/course-card";
import { Button } from "@/components/ui/button";
import { FileUpload } from "@/components/ui/file-upload";
import { Field, Input, Select, Textarea } from "@/components/ui/input";

export function CourseInfoForm({
  course,
  locked,
  onSaved,
}: {
  course: CourseDetail;
  locked: boolean;
  onSaved: () => void;
}) {
  const categories = useQuery({ queryKey: ["categories"], queryFn: categoryApi.list });
  const [title, setTitle] = React.useState(course.title);
  const [categoryId, setCategoryId] = React.useState(String(course.category_id));
  const [description, setDescription] = React.useState(course.description ?? "");
  const [thumbnail, setThumbnail] = React.useState(course.thumbnail_url ?? "");

  const save = useMutation({
    mutationFn: () =>
      instructorApi.updateCourse(course.id, {
        title: title.trim(),
        category_id: Number(categoryId),
        description: description.trim() || null,
        thumbnail_url: thumbnail || null,
      }),
    onSuccess: ({ message }) => {
      toast.success(message);
      onSaved();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  return (
    <form
      className="grid max-w-4xl gap-8 md:grid-cols-[minmax(0,1fr)_260px]"
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
    >
      <fieldset disabled={locked} className="space-y-5">
        <Field label="Tên khóa học" htmlFor="i-title">
          <Input id="i-title" value={title} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <Field label="Danh mục" htmlFor="i-cat">
          <Select id="i-cat" value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
            {categories.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Mô tả" htmlFor="i-desc" hint="Học viên đọc phần này trước khi đăng ký.">
          <Textarea id="i-desc" rows={8} value={description} onChange={(e) => setDescription(e.target.value)} />
        </Field>
        <Button type="submit" loading={save.isPending} disabled={title.trim().length < 2}>
          Lưu thông tin
        </Button>
      </fieldset>
      <div>
        <p className="field-label">Ảnh bìa</p>
        <CourseCover course={{ title, thumbnail_url: thumbnail || null }} />
        {!locked && (
          <div className="mt-3 space-y-2">
            <FileUpload
              bucket="thumbnails"
              accept="image/png,image/jpeg,image/webp"
              label="Tải ảnh bìa"
              onUploaded={(f) => setThumbnail(f.file_url)}
            />
            {thumbnail && (
              <button type="button" className="text-xs text-ink-muted hover:text-red" onClick={() => setThumbnail("")}>
                Bỏ ảnh bìa
              </button>
            )}
            <p className="text-xs text-ink-muted">Bấm Lưu thông tin để áp dụng ảnh mới.</p>
          </div>
        )}
      </div>
    </form>
  );
}
