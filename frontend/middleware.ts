import { NextResponse, type NextRequest } from "next/server";

/**
 * Edge route guard (SDD §6.2).
 * The access token lives in memory and the refresh cookie is scoped to the API's
 * /api/v1/auth path, so the Edge cannot see either. Instead it reads the `el_role`
 * hint cookie written by the client after sign-in. The hint only steers navigation –
 * every API call is still authorised by the backend.
 */
const RULES: { prefix: string; roles: string[] }[] = [
  { prefix: "/admin", roles: ["ADMIN"] },
  { prefix: "/instructor", roles: ["INSTRUCTOR", "ADMIN"] },
  { prefix: "/dashboard", roles: ["STUDENT", "INSTRUCTOR", "ADMIN"] },
  { prefix: "/learn", roles: ["STUDENT", "INSTRUCTOR", "ADMIN"] },
  { prefix: "/profile", roles: ["STUDENT", "INSTRUCTOR", "ADMIN"] },
];

export function middleware(req: NextRequest) {
  const { pathname, search } = req.nextUrl;
  const rule = RULES.find((r) => pathname === r.prefix || pathname.startsWith(`${r.prefix}/`));
  if (!rule) return NextResponse.next();

  const role = req.cookies.get("el_role")?.value;
  if (!role) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }
  if (!rule.roles.includes(role)) {
    const url = req.nextUrl.clone();
    url.pathname = "/unauthorized";
    url.search = "";
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*", "/instructor/:path*", "/dashboard/:path*", "/learn/:path*", "/profile/:path*"],
};
