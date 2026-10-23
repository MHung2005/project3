"use client";

import { create } from "zustand";
import type { Role, User, UserBrief } from "@/lib/types";

/** Non-HttpOnly hint cookie read by middleware.ts for coarse route guarding.
 *  It carries no secret – the backend re-checks the role on every request. */
export const ROLE_COOKIE = "el_role";

function writeRoleCookie(role: Role | null) {
  if (typeof document === "undefined") return;
  if (role) {
    document.cookie = `${ROLE_COOKIE}=${role}; path=/; max-age=${7 * 24 * 3600}; samesite=lax`;
  } else {
    document.cookie = `${ROLE_COOKIE}=; path=/; max-age=0; samesite=lax`;
  }
}

type SessionStatus = "loading" | "authenticated" | "anonymous";

interface AuthState {
  /** Access token lives in memory only (SDD §4.1); the refresh token is an HttpOnly cookie. */
  accessToken: string | null;
  user: (UserBrief & Partial<User>) | null;
  status: SessionStatus;
  setSession: (token: string, user: UserBrief | User) => void;
  setToken: (token: string) => void;
  setUser: (user: UserBrief | User) => void;
  clear: () => void;
  markAnonymous: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  status: "loading",
  setSession: (accessToken, user) => {
    writeRoleCookie(user.role);
    set({ accessToken, user, status: "authenticated" });
  },
  setToken: (accessToken) => set({ accessToken }),
  setUser: (user) => {
    writeRoleCookie(user.role);
    set({ user, status: "authenticated" });
  },
  clear: () => {
    writeRoleCookie(null);
    set({ accessToken: null, user: null, status: "anonymous" });
  },
  markAnonymous: () => {
    writeRoleCookie(null);
    set({ status: "anonymous" });
  },
}));

export function hasRole(user: { role: Role } | null, ...roles: Role[]) {
  return !!user && roles.includes(user.role);
}
