"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-line">
      <div className="container flex flex-col gap-2 py-8 text-sm text-ink-muted sm:flex-row sm:justify-between">
        <p>Uniwise, nền tảng học trực tuyến. Đồ án Project 3, Đại học Bách khoa Hà Nội.</p>
        <p>Lê Mạnh Hùng, 20235096</p>
      </div>
    </footer>
  );
}

/** Secondary navigation for the instructor and admin workspaces. */
export function WorkspaceNav({ items }: { items: { href: string; label: string }[] }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Khu vực làm việc" className="border-b border-line">
      <div className="container flex gap-1 overflow-x-auto overflow-y-hidden">
        {items.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "-mb-px whitespace-nowrap border-b-2 px-3 py-3 text-sm",
                active ? "border-blue text-blue" : "border-transparent text-ink-muted hover:text-ink",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
