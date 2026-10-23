import Link from "next/link";
import { Button } from "@/components/ui/button";

export const metadata = { title: "Không có quyền truy cập" };

export default function UnauthorizedPage() {
  return (
    <div className="container max-w-xl py-24">
      <h1 className="text-[28px] leading-[34px]">Trang này không dành cho tài khoản của bạn.</h1>
      <p className="mt-6 text-ink-muted">
        Trang bạn mở yêu cầu vai trò khác (giảng viên hoặc quản trị viên). Nếu bạn cần quyền này, hãy liên hệ quản trị
        viên hệ thống.
      </p>
      <div className="mt-8 flex gap-3">
        <Button asChild>
          <Link href="/">Về trang chủ</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/login">Đăng nhập tài khoản khác</Link>
        </Button>
      </div>
    </div>
  );
}
