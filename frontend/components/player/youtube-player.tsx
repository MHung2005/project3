"use client";

import { CheckCircle2 } from "lucide-react";
import { useYouTubeTracker } from "@/hooks/use-youtube-tracker";
import type { Lesson } from "@/lib/types";
import { formatClock } from "@/lib/utils";
import { ProgressBar } from "@/components/ui/misc";

const THRESHOLD = 0.8;

export function YouTubePlayer({
  lesson,
  startAt,
  completed,
  onSavePosition,
  onComplete,
}: {
  lesson: Lesson;
  startAt: number;
  completed: boolean;
  onSavePosition: (second: number) => void;
  onComplete: (second: number) => void;
}) {
  const tracker = useYouTubeTracker({
    videoId: lesson.youtube_video_id,
    duration: lesson.duration_seconds,
    startAt,
    threshold: THRESHOLD,
    alreadyCompleted: completed,
    onSavePosition,
    onComplete,
  });

  if (!lesson.youtube_video_id) {
    return <p className="rounded-md border border-line p-6 text-sm text-ink-muted">Bài học chưa có video hợp lệ.</p>;
  }

  const pct = Math.round(tracker.watchedRatio * 100);
  const needed = Math.round(THRESHOLD * 100);

  return (
    <div>
      <div className="relative aspect-video w-full overflow-hidden rounded-md bg-[#000]">
        <div ref={tracker.containerRef} className="absolute inset-0 [&>iframe]:size-full" />
        {!tracker.ready && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-[#bbb]">Đang tải video…</div>
        )}
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        {tracker.completed ? (
          <span className="inline-flex items-center gap-1.5 font-medium text-blue">
            <CheckCircle2 className="size-4" aria-hidden /> Hoàn thành bài học
          </span>
        ) : (
          <>
            {/* Amber watch-time bar with the 80% completion tick */}
            <ProgressBar value={pct} threshold={needed} className="w-48" label="Thời lượng đã xem" />
            <span className="text-ink-muted" aria-live="polite">
              Đã xem <span className="numeric text-amber-ink">{pct}%</span> · cần trên {needed}% để hoàn thành
            </span>
          </>
        )}
        {tracker.duration > 0 && (
          <span className="numeric ml-auto text-[13px] text-ink-muted">
            {formatClock(tracker.currentSecond)} / {formatClock(tracker.duration)}
          </span>
        )}
      </div>
    </div>
  );
}
