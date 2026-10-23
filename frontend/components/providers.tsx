"use client";

import * as React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { refreshAccessToken } from "@/lib/api-client";
import { authApi } from "@/lib/endpoints";
import { useAuth } from "@/hooks/use-auth";

/** Restores the session on page load: refresh cookie → access token → /auth/me. */
function SessionBootstrap() {
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      const token = await refreshAccessToken();
      if (cancelled) return;
      if (!token) {
        useAuth.getState().markAnonymous();
        return;
      }
      try {
        const me = await authApi.me();
        if (!cancelled) useAuth.getState().setSession(token, me);
      } catch {
        if (!cancelled) useAuth.getState().clear();
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <SessionBootstrap />
      {children}
      <Toaster
        position="bottom-right"
        toastOptions={{
          classNames: {
            toast: "!bg-paper-raised !text-ink !border-line !font-sans",
            error: "!text-red",
          },
        }}
      />
    </QueryClientProvider>
  );
}
