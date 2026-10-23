"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { ChevronDown, LogOut, Menu, UserRound, X } from "lucide-react";
import { authApi } from "@/lib/endpoints";
import { useAuth } from "@/hooks/use-auth";
import type { Role } from "@/lib/types";
import { cn, ROLE_LABEL } from "@/lib/utils";
import { Avatar } from "@/components/ui/misc";
import { Button } from "@/components/ui/button";
import { Logo } from "./logo";

interface NavItem {
  href: string;
  label: string;
  roles?: Role[];
}

const NAV: NavItem[] = [
  { href: "/courses", label: "Khóa học" },
  { href: "/dashboard", label: "Khóa học của tôi", roles: ["STUDENT", "INSTRUCTOR", "ADMIN"] },
  { href: "/instructor/courses", label: "Giảng dạy", roles: ["INSTRUCTOR", "ADMIN"] },
  { href: "/admin/courses", label: "Quản trị", roles: ["ADMIN"] },
];

export function SiteHeader() {
  const { user, status } = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  React.useEffect(() => setMobileOpen(false), [pathname]);

  const items = NAV.filter((n) => !n.roles || (user && n.roles.includes(user.role)));
  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/95 backdrop-blur">
      <div className="container flex h-16 items-center gap-6">
        <Logo />
        <nav aria-label="Điều hướng chính" className="hidden items-center gap-1 md:flex">
          {items.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={cn(
                "rounded px-3 py-2 text-sm text-ink-muted hover:text-blue",
                isActive(n.href) && "text-blue underline decoration-2 underline-offset-[22px]",
              )}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          {status === "loading" ? (
            <span className="h-9 w-24" aria-hidden />
          ) : user ? (
            <AccountMenu />
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/login">Đăng nhập</Link>
              </Button>
              <Button asChild size="sm" className="hidden sm:inline-flex">
                <Link href="/register">Tạo tài khoản</Link>
              </Button>
            </>
          )}
          <button
            className="rounded p-2 text-ink-muted hover:bg-blue-soft md:hidden"
            aria-label={mobileOpen ? "Đóng menu" : "Mở menu"}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((v) => !v)}
          >
            {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>
      {mobileOpen && (
        <nav aria-label="Điều hướng chính" className="border-t border-line bg-paper md:hidden">
          <div className="container flex flex-col py-2">
            {items.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                className={cn("rounded px-2 py-3 text-sm", isActive(n.href) ? "text-blue" : "text-ink")}
              >
                {n.label}
              </Link>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}

function AccountMenu() {
  const { user, clear } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!user) return null;

  async function logout() {
    try {
      await authApi.logout();
    } catch {
      // Cookie removal failing must not keep the user signed in locally
    }
    clear();
    queryClient.clear();
    router.push("/");
  }

  return (
    <div ref={ref} className="relative">
      <button
        className="flex items-center gap-2 rounded py-1 pl-1 pr-2 hover:bg-blue-soft"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Tài khoản: ${user.full_name}`}
        onClick={() => setOpen((v) => !v)}
      >
        <Avatar name={user.full_name} src={user.avatar_url} size={30} />
        <span className="hidden max-w-[10rem] truncate text-sm sm:block">{user.full_name}</span>
        <ChevronDown className="size-4 text-ink-muted" aria-hidden />
      </button>
      {open && (
        <div role="menu" className="absolute right-0 mt-2 w-60 rounded-md border border-line bg-paper-raised p-1.5 shadow-[0_1px_2px_rgb(22_25_29_/0.08),0_8px_24px_-6px_rgb(22_25_29_/0.14)]">
          <div className="px-3 py-2">
            <p className="truncate text-sm font-medium">{user.full_name}</p>
            <p className="truncate text-xs text-ink-muted">
              {user.email}, {ROLE_LABEL[user.role].toLowerCase()}
            </p>
          </div>
          <div className="my-1 h-px bg-line" />
          <Link
            role="menuitem"
            href="/profile"
            className="flex items-center gap-2 rounded px-3 py-2 text-sm hover:bg-blue-soft hover:text-blue"
            onClick={() => setOpen(false)}
          >
            <UserRound className="size-4" aria-hidden /> Hồ sơ cá nhân
          </Link>
          <button
            role="menuitem"
            className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm hover:bg-blue-soft hover:text-blue"
            onClick={logout}
          >
            <LogOut className="size-4" aria-hidden /> Đăng xuất
          </button>
        </div>
      )}
    </div>
  );
}
