import { Logo } from "@/components/layout/logo";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      <div className="flex flex-col px-4 py-6 sm:px-10">
        <Logo />
        <main className="flex flex-1 items-center py-12">
          <div className="mx-auto w-full max-w-sm">{children}</div>
        </main>
      </div>
      <aside aria-hidden className="relative hidden border-l border-line bg-paper-sunk lg:block">
        <div className="absolute bottom-16 left-16 right-16 max-w-md">
          <p className="font-serif text-[44px] leading-[48px] tracking-tight text-ink">
            Học có cấu trúc. Tiến độ trung thực.
          </p>
          <div className="mt-10 space-y-2">
            <div className="flex justify-between text-[13px] text-ink-muted">
              <span>Đã xem 64% · cần trên 80% để hoàn thành</span>
              <span className="numeric text-amber-ink">64%</span>
            </div>
            {/* Static illustration of the watch-time bar */}
            <div className="relative h-1.5 rounded-xs bg-paper shadow-[inset_0_0_0_1px_rgb(var(--line))]">
              <div className="h-full w-[64%] rounded-xs bg-amber" />
              <span className="absolute -bottom-[3px] -top-[3px] left-[80%] w-0.5 rounded-xs bg-ink" />
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
