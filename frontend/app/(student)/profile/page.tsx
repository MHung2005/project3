"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { errorMessage } from "@/lib/api-client";
import { authApi, storageApi } from "@/lib/endpoints";
import { useAuth } from "@/hooks/use-auth";
import { formatDate, passwordProblem, ROLE_LABEL } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { Avatar } from "@/components/ui/misc";

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const [fullName, setFullName] = React.useState(user?.full_name ?? "");
  const fileRef = React.useRef<HTMLInputElement>(null);

  const saveProfile = useMutation({
    mutationFn: () => authApi.updateProfile({ full_name: fullName.trim() }),
    onSuccess: ({ data, message }) => {
      setUser(data);
      toast.success(message);
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const uploadAvatar = useMutation({
    mutationFn: (file: File) => storageApi.uploadAvatar(file),
    onSuccess: ({ data, message }) => {
      setUser(data.user);
      toast.success(message);
    },
    onError: (e) => toast.error(errorMessage(e)),
    onSettled: () => {
      if (fileRef.current) fileRef.current.value = "";
    },
  });

  if (!user) return null;

  return (
    <div className="container max-w-2xl py-10">
      <h1 className="text-2xl">Hồ sơ cá nhân</h1>
      <p className="mt-1 text-ink-muted">
        {ROLE_LABEL[user.role]}
        {user.created_at && `, tham gia từ ${formatDate(user.created_at)}`}
      </p>

      <section className="mt-10 border-t border-line pt-8">
        <h2 className="text-lg">Thông tin</h2>
        <div className="mt-5 flex items-center gap-4">
          <Avatar name={user.full_name} src={user.avatar_url} size={64} />
          <div>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="sr-only"
              tabIndex={-1}
              onChange={(e) => e.target.files?.[0] && uploadAvatar.mutate(e.target.files[0])}
            />
            <Button variant="outline" size="sm" loading={uploadAvatar.isPending} onClick={() => fileRef.current?.click()}>
              Đổi ảnh đại diện
            </Button>
            <p className="mt-1.5 text-xs text-ink-muted">PNG, JPG hoặc WEBP.</p>
          </div>
        </div>
        <form
          className="mt-6 space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            saveProfile.mutate();
          }}
        >
          <Field label="Email" htmlFor="email" hint="Email dùng để đăng nhập và không đổi được.">
            <Input id="email" value={user.email} disabled />
          </Field>
          <Field label="Họ và tên" htmlFor="full_name">
            <Input id="full_name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </Field>
          <Button
            type="submit"
            loading={saveProfile.isPending}
            disabled={fullName.trim().length < 2 || fullName.trim() === user.full_name}
          >
            Lưu thông tin
          </Button>
        </form>
      </section>

      <ChangePassword />
    </div>
  );
}

function ChangePassword() {
  const [current, setCurrent] = React.useState("");
  const [next, setNext] = React.useState("");
  const [confirm, setConfirm] = React.useState("");
  const [touched, setTouched] = React.useState(false);

  const problem = passwordProblem(next);
  const mismatch = confirm && confirm !== next ? "Mật khẩu nhập lại không khớp." : null;

  const change = useMutation({
    mutationFn: () => authApi.changePassword({ current_password: current, new_password: next }),
    onSuccess: ({ message }) => {
      toast.success(message);
      setCurrent("");
      setNext("");
      setConfirm("");
      setTouched(false);
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  return (
    <section className="mt-12 border-t border-line pt-8">
      <h2 className="text-lg">Đổi mật khẩu</h2>
      <form
        className="mt-5 space-y-5"
        onSubmit={(e) => {
          e.preventDefault();
          setTouched(true);
          if (!current || problem || mismatch || confirm !== next) return;
          change.mutate();
        }}
      >
        <Field label="Mật khẩu hiện tại" htmlFor="current_password">
          <Input
            id="current_password"
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
          />
        </Field>
        <Field
          label="Mật khẩu mới"
          htmlFor="new_password"
          hint="Ít nhất 6 ký tự, có 1 chữ hoa và 1 chữ số."
          error={touched ? problem : null}
        >
          <Input
            id="new_password"
            type="password"
            autoComplete="new-password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
          />
        </Field>
        <Field label="Nhập lại mật khẩu mới" htmlFor="confirm_password" error={mismatch}>
          <Input
            id="confirm_password"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
        </Field>
        <Button type="submit" variant="outline" loading={change.isPending}>
          Đổi mật khẩu
        </Button>
      </form>
    </section>
  );
}
