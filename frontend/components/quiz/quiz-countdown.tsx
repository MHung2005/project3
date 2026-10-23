"use client";

import * as React from "react";
import { Timer } from "lucide-react";
import { cn, formatClock } from "@/lib/utils";

/** Counts down to `deadline` and calls `onExpire` once. */
export function QuizCountdown({ deadline, onExpire }: { deadline: Date; onExpire: () => void }) {
  const [left, setLeft] = React.useState(() => Math.max(0, (deadline.getTime() - Date.now()) / 1000));
  const fired = React.useRef(false);
  const expireRef = React.useRef(onExpire);
  expireRef.current = onExpire;

  React.useEffect(() => {
    const tick = () => {
      const s = Math.max(0, (deadline.getTime() - Date.now()) / 1000);
      setLeft(s);
      if (s <= 0 && !fired.current) {
        fired.current = true;
        expireRef.current();
      }
    };
    tick();
    const id = setInterval(tick, 500);
    return () => clearInterval(id);
  }, [deadline]);

  const urgent = left <= 60;
  return (
    <span
      className={cn("inline-flex items-center gap-1.5 numeric", urgent ? "font-semibold text-red" : "text-ink")}
      aria-live={urgent ? "assertive" : "off"}
      aria-label={`Thời gian còn lại ${formatClock(left)}`}
    >
      <Timer className="size-4" aria-hidden />
      {formatClock(left)}
    </span>
  );
}
