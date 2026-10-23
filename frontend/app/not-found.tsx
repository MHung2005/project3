import Link from "next/link";
import { Logo } from "@/components/layout/logo";

export default function NotFound() {
  return (
    <div className="container max-w-xl py-16">
      <Logo />
      <p className="numeric mt-20 text-[40px] leading-[44px] text-ink-muted">404</p>
      <h1 className="mt-4 text-2xl">Không tìm thấy trang</h1>
      <p className="mt-2 text-ink-muted">Đường dẫn có thể đã sai, hoặc khóa học chưa được xuất bản.</p>
      <Link href="/courses" className="mt-8 inline-block text-blue underline-offset-4 hover:underline">
        Xem danh sách khóa học
      </Link>
    </div>
  );
}
