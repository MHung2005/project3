"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { errorMessage } from "@/lib/api-client";
import { authApi } from "@/lib/endpoints";
import { useAuth } from "@/hooks/use-auth";
import { homeForRole } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { ErrorNote } from "@/components/ui/misc";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const setSession = useAuth((s) => s.setSession);
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access_token, user } = await authApi.login({ email: email.trim(), password });
      setSession(access_token, user);
      const next = params.get("next");
      router.replace(next && next.startsWith("/") && !next.startsWith("//") ? next : homeForRole(user.role));
    } catch (err) {
      setError(errorMessage(err, "Email hoặc mật khẩu không đúng."));
      setLoading(false);
    }
  }

  return (
    <>
      <h1 className="text-2xl">Đăng nhập</h1>
      <p className="mt-1 text-ink-muted">Tiếp tục học từ chỗ bạn dừng lại.</p>
      <form onSubmit={submit} className="mt-8 space-y-5" noValidate>
        {params.get("registered") && !error && (
          <p className="rounded border border-blue/30 bg-blue/5 px-4 py-3 text-sm text-blue">
            Đã tạo tài khoản. Đăng nhập để bắt đầu học.
          </p>
        )}
        {error && <ErrorNote message={error} />}
        <Field label="Email" htmlFor="email">
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label="Mật khẩu" htmlFor="password">
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <Button type="submit" className="w-full" size="lg" loading={loading} disabled={!email || !password}>
          Đăng nhập
        </Button>
      </form>
      <p className="mt-8 text-sm text-ink-muted">
        Chưa có tài khoản?{" "}
        <Link href="/register" className="text-blue underline-offset-4 hover:underline">
          Tạo tài khoản học viên
        </Link>
      </p>
    </>
  );
}

export default function LoginPage() {
  return (
    <React.Suspense>
      <LoginForm />
    </React.Suspense>
  );
}
