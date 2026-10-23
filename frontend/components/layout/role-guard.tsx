"use client";

import * as React from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import type { Role } from "@/lib/types";
import { Spinner } from "@/components/ui/misc";

/** Client-side guard. middleware.ts redirects early using the role hint cookie;
 *  this waits for the real session and is the source of truth in the browser. */
export function RoleGuard({ roles, children }: { roles?: Role[]; children: React.ReactNode }) {
  const { user, status } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const allowed = !!user && (!roles || roles.includes(user.role));

  React.useEffect(() => {
    if (status === "anonymous") {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    } else if (status === "authenticated" && !allowed) {
      router.replace("/unauthorized");
    }
  }, [status, allowed, router, pathname]);

  if (!allowed) return <Spinner label="Đang kiểm tra phiên đăng nhập" className="py-24" />;
  return <>{children}</>;
}
