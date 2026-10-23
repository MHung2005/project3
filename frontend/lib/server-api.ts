import "server-only";
import type { Category, Course, CourseDetail, Envelope, Paginated } from "./types";

// Inside Docker the Next.js server reaches FastAPI by service name, not localhost.
const BASE = process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ServerApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function get<T>(path: string, revalidate = 60): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { next: { revalidate } });
  } catch {
    throw new ServerApiError(0, "Không kết nối được máy chủ API.");
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new ServerApiError(res.status, body?.detail ?? `Lỗi ${res.status}`);
  }
  return ((await res.json()) as Envelope<T>).data;
}

export const serverApi = {
  categories: () => get<Category[]>("/categories", 300),
  courses: (params: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && v !== "" && qs.set(k, String(v)));
    return get<Paginated<Course>>(`/courses?${qs.toString()}`, 30);
  },
  course: (id: number) => get<CourseDetail>(`/courses/${id}`, 30),
};
