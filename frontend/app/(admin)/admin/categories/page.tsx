"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { categoryApi } from "@/lib/endpoints";
import type { Category } from "@/lib/types";
import { formatDate, slugify } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ConfirmDialog, Dialog, DialogClose, DialogContent, DialogFooter } from "@/components/ui/dialog";
import { Field, Input, Textarea } from "@/components/ui/input";
import { EmptyState, ErrorNote, PageHeader, Spinner } from "@/components/ui/misc";
import { Table, Td, Th } from "@/components/ui/table";

export default function AdminCategoriesPage() {
  const qc = useQueryClient();
  const list = useQuery({ queryKey: ["categories"], queryFn: categoryApi.list });
  const [editing, setEditing] = React.useState<Category | "new" | null>(null);
  const [deleting, setDeleting] = React.useState<Category | null>(null);

  const remove = useMutation({
    mutationFn: (id: number) => categoryApi.remove(id),
    onSuccess: ({ message }) => {
      toast.success(message);
      setDeleting(null);
      qc.invalidateQueries({ queryKey: ["categories"] });
    },
    onError: (e) => {
      setDeleting(null);
      toast.error(errorMessage(e));
    },
  });

  return (
    <>
      <PageHeader
        title="Danh mục"
        description="Giảng viên chọn danh mục khi tạo khóa học. Học viên lọc khóa học theo danh mục."
        actions={
          <Button onClick={() => setEditing("new")}>
            <Plus /> Tạo danh mục
          </Button>
        }
      />
      {list.isLoading ? (
        <Spinner />
      ) : list.error ? (
        <ErrorNote message={errorMessage(list.error)} />
      ) : list.data!.length === 0 ? (
        <EmptyState
          title="Chưa có danh mục"
          description="Tạo danh mục đầu tiên để giảng viên có thể tạo khóa học."
          action={<Button onClick={() => setEditing("new")}>Tạo danh mục</Button>}
        />
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Tên</Th>
              <Th>Đường dẫn</Th>
              <Th>Mô tả</Th>
              <Th>Ngày tạo</Th>
              <Th />
            </tr>
          </thead>
          <tbody>
            {list.data!.map((c) => (
              <tr key={c.id}>
                <Td className="font-medium">{c.name}</Td>
                <Td className="text-ink-muted">/{c.slug}</Td>
                <Td className="max-w-xs truncate text-ink-muted">{c.description || "—"}</Td>
                <Td className="text-ink-muted">{formatDate(c.created_at)}</Td>
                <Td className="whitespace-nowrap text-right">
                  <Button variant="link" size="sm" onClick={() => setEditing(c)}>
                    Sửa
                  </Button>
                  <Button variant="link" size="sm" className="ml-3 text-red" onClick={() => setDeleting(c)}>
                    Xóa
                  </Button>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {editing && (
        <CategoryDialog
          category={editing === "new" ? undefined : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            qc.invalidateQueries({ queryKey: ["categories"] });
          }}
        />
      )}
      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(o) => !o && setDeleting(null)}
        title={`Xóa danh mục “${deleting?.name ?? ""}”?`}
        description="Không xóa được danh mục đang có khóa học."
        confirmLabel="Xóa danh mục"
        loading={remove.isPending}
        onConfirm={() => deleting && remove.mutate(deleting.id)}
      />
    </>
  );
}

function CategoryDialog({
  category,
  onClose,
  onSaved,
}: {
  category?: Category;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = React.useState(category?.name ?? "");
  const [slug, setSlug] = React.useState(category?.slug ?? "");
  const [slugTouched, setSlugTouched] = React.useState(!!category);
  const [description, setDescription] = React.useState(category?.description ?? "");

  const save = useMutation({
    mutationFn: () => {
      const body = { name: name.trim(), slug, description: description.trim() || null };
      return category ? categoryApi.update(category.id, body) : categoryApi.create(body);
    },
    onSuccess: ({ message }) => {
      toast.success(message);
      onSaved();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const slugValid = /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) && slug.length >= 2;

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent title={category ? "Sửa danh mục" : "Tạo danh mục"}>
        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
        >
          <Field label="Tên danh mục" htmlFor="cat-name">
            <Input
              id="cat-name"
              value={name}
              autoFocus
              onChange={(e) => {
                setName(e.target.value);
                if (!slugTouched) setSlug(slugify(e.target.value));
              }}
            />
          </Field>
          <Field
            label="Đường dẫn"
            htmlFor="cat-slug"
            hint="Chữ thường không dấu, nối bằng gạch ngang. Tự tạo từ tên."
            error={slug && !slugValid ? "Chỉ dùng a-z, 0-9 và dấu gạch ngang." : null}
          >
            <Input
              id="cat-slug"
              value={slug}
              onChange={(e) => {
                setSlugTouched(true);
                setSlug(e.target.value.toLowerCase());
              }}
            />
          </Field>
          <Field label="Mô tả" htmlFor="cat-desc">
            <Textarea id="cat-desc" rows={3} maxLength={500} value={description} onChange={(e) => setDescription(e.target.value)} />
          </Field>
          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Hủy
              </Button>
            </DialogClose>
            <Button type="submit" loading={save.isPending} disabled={name.trim().length < 2 || !slugValid}>
              {category ? "Lưu danh mục" : "Tạo danh mục"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
