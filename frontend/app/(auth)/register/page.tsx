"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { errorMessage } from "@/lib/api-client";
import { authApi } from "@/lib/endpoints";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { ErrorNote } from "@/components/ui/misc";
import { passwordProblem } from "@/lib/utils";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = React.useState({ full_name: "", email: "", password: "" });
  const [touched, setTouched] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const pwProblem = passwordProblem(form.password);
  const nameProblem = form.full_name.trim().length < 2 ? "Nhập họ và tên (ít nhất 2 ký tự)." : null;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (pwProblem || nameProblem || !form.email) return;
    setError(null);
    setLoading(true);
    try {
      await authApi.register({ ...form, full_name: form.full_name.trim(), email: form.email.trim() });
      router.replace("/login?registered=1");
    } catch (err) {
      setError(errorMessage(err));
      setLoading(false);
    }
  }

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  return (
    <>
      <h1 className="text-2xl">Tạo tài khoản học viên</h1>
      <p className="mt-1 text-ink-muted">Miễn phí. Đăng ký khóa học ngay sau khi tạo tài khoản.</p>
      <form onSubmit={submit} className="mt-8 space-y-5" noValidate>
        {error && <ErrorNote message={error} />}
        <Field label="Họ và tên" htmlFor="full_name" error={touched ? nameProblem : null}>
          <Input id="full_name" autoComplete="name" value={form.full_name} onChange={set("full_name")} />
        </Field>
        <Field label="Email" htmlFor="email">
          <Input id="email" type="email" autoComplete="email" value={form.email} onChange={set("email")} />
        </Field>
        <Field
          label="Mật khẩu"
          htmlFor="password"
          hint="Ít nhất 6 ký tự, có 1 chữ hoa và 1 chữ số."
          error={touched ? pwProblem : null}
        >
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={set("password")}
          />
        </Field>
        <Button type="submit" className="w-full" size="lg" loading={loading}>
          Tạo tài khoản
        </Button>
      </form>
      <p className="mt-8 text-sm text-ink-muted">
        Đã có tài khoản?{" "}
        <Link href="/login" className="text-blue underline-offset-4 hover:underline">
          Đăng nhập
        </Link>
      </p>
    </>
  );
}
