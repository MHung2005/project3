import axios, { AxiosError, type AxiosRequestConfig } from "axios";
import { useAuth } from "@/hooks/use-auth";
import type { Envelope } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/** Axios instance that attaches the in-memory access token and silently refreshes it once on 401. */
export const http = axios.create({
  baseURL: API_URL,
  withCredentials: true, // send the HttpOnly refresh-token cookie
});

http.interceptors.request.use((config) => {
  const token = useAuth.getState().accessToken;
  if (token) config.headers.set("Authorization", `Bearer ${token}`);
  return config;
});

let refreshing: Promise<string | null> | null = null;

/** Exchange the refresh cookie for a new access token. Concurrent callers share one request. */
export function refreshAccessToken(): Promise<string | null> {
  if (!refreshing) {
    refreshing = axios
      .post<Envelope<{ access_token: string }>>(`${API_URL}/auth/refresh`, null, { withCredentials: true })
      .then((res) => {
        const token = res.data.data.access_token;
        useAuth.getState().setToken(token);
        return token;
      })
      .catch(() => null)
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

http.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as (AxiosRequestConfig & { _retried?: boolean }) | undefined;
    const isAuthCall = original?.url?.startsWith("/auth/login") || original?.url?.startsWith("/auth/refresh");
    if (error.response?.status === 401 && original && !original._retried && !isAuthCall) {
      original._retried = true;
      const token = await refreshAccessToken();
      if (token) {
        original.headers = { ...(original.headers ?? {}), Authorization: `Bearer ${token}` };
        return http(original);
      }
      useAuth.getState().clear();
    }
    return Promise.reject(error);
  },
);

/** Unwrap the `{ success, message, data }` envelope. */
export async function api<T>(config: AxiosRequestConfig): Promise<T> {
  const res = await http.request<Envelope<T>>(config);
  return res.data.data;
}

/** Like `api` but also returns the server message (used for toasts after mutations). */
export async function apiWithMessage<T>(config: AxiosRequestConfig): Promise<{ data: T; message: string }> {
  const res = await http.request<Envelope<T>>(config);
  return { data: res.data.data, message: res.data.message };
}

/** Human-readable error text from FastAPI's `{ detail }` (string or validation array). */
export function errorMessage(error: unknown, fallback = "Đã có lỗi xảy ra. Vui lòng thử lại."): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) return "Không kết nối được máy chủ. Kiểm tra backend đã chạy chưa.";
    const detail = (error.response.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg.replace(/^Value error,\s*/i, "");
    }
  }
  return fallback;
}

export function errorStatus(error: unknown): number | undefined {
  return axios.isAxiosError(error) ? error.response?.status : undefined;
}
