import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { CourseStatus, Role } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Backend stores naive UTC datetimes (SQL Server DATETIME2) – treat strings without a zone as UTC. */
export function parseDate(value: string): Date {
  return new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(value) ? value : `${value}Z`);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return parseDate(value).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return parseDate(value).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** 3725 → "1 giờ 2 phút"; 125 → "2 phút". */
export function formatDuration(seconds: number): string {
  if (!seconds) return "0 phút";
  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds % 3600) / 60);
  if (h === 0) return `${Math.max(m, 1)} phút`;
  return m ? `${h} giờ ${m} phút` : `${h} giờ`;
}

/** 125 → "02:05" */
export function formatClock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(r).padStart(2, "0");
  return h ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** Score on a 10-point scale, Vietnamese decimal comma: 8.5 → "8,5" */
export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return (Math.round(score * 100) / 100).toLocaleString("vi-VN", { maximumFractionDigits: 2 });
}

export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  // Vietnamese names put the given name last
  const last = parts[parts.length - 1] ?? "";
  const first = parts.length > 1 ? parts[0] : "";
  return (first.charAt(0) + last.charAt(0)).toUpperCase() || "?";
}

export const ROLE_LABEL: Record<Role, string> = {
  STUDENT: "Học viên",
  INSTRUCTOR: "Giảng viên",
  ADMIN: "Quản trị viên",
};

export const COURSE_STATUS_LABEL: Record<CourseStatus, string> = {
  DRAFT: "Bản nháp",
  PENDING: "Chờ duyệt",
  PUBLISHED: "Đã xuất bản",
  REJECTED: "Bị từ chối",
};

/** Where each role lands after signing in. */
export function homeForRole(role: Role): string {
  if (role === "ADMIN") return "/admin/courses";
  if (role === "INSTRUCTOR") return "/instructor/courses";
  return "/dashboard";
}

/** Mirrors backend _validate_password_strength + length rules. */
export function passwordProblem(pw: string): string | null {
  if (pw.length < 6) return "Mật khẩu cần ít nhất 6 ký tự.";
  if (!/[A-Z]/.test(pw)) return "Mật khẩu cần ít nhất 1 chữ hoa.";
  if (!/\d/.test(pw)) return "Mật khẩu cần ít nhất 1 chữ số.";
  return null;
}

/** Turn "Lập trình Web" into "lap-trinh-web" (matches backend slug pattern). */
export function slugify(input: string): string {
  return input
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function extractYoutubeId(url: string): string | null {
  const patterns = [
    /^(?:https?:\/\/)?(?:www\.|m\.)?youtube\.com\/watch\?(?:.*&)?v=([A-Za-z0-9_-]{11})/,
    /^(?:https?:\/\/)?(?:www\.)?youtu\.be\/([A-Za-z0-9_-]{11})/,
    /^(?:https?:\/\/)?(?:www\.)?youtube(?:-nocookie)?\.com\/(?:embed|shorts|live)\/([A-Za-z0-9_-]{11})/,
  ];
  for (const p of patterns) {
    const m = url.trim().match(p);
    if (m) return m[1];
  }
  return null;
}
