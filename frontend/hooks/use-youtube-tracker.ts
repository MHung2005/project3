"use client";

import { useEffect, useRef, useState } from "react";

// Minimal typings for the YouTube IFrame Player API
interface YTPlayer {
  getCurrentTime(): number;
  getDuration(): number;
  getPlayerState(): number;
  seekTo(seconds: number, allowSeekAhead: boolean): void;
  destroy(): void;
}
interface YTNamespace {
  Player: new (
    el: HTMLElement,
    opts: {
      videoId: string;
      width?: string | number;
      height?: string | number;
      playerVars?: Record<string, number | string>;
      events?: {
        onReady?: (e: { target: YTPlayer }) => void;
        onStateChange?: (e: { data: number; target: YTPlayer }) => void;
      };
    },
  ) => YTPlayer;
  PlayerState: { ENDED: 0; PLAYING: 1; PAUSED: 2 };
}
declare global {
  interface Window {
    YT?: YTNamespace;
    onYouTubeIframeAPIReady?: () => void;
  }
}

let apiPromise: Promise<YTNamespace> | null = null;

function loadYouTubeApi(): Promise<YTNamespace> {
  if (window.YT?.Player) return Promise.resolve(window.YT);
  if (!apiPromise) {
    apiPromise = new Promise((resolve) => {
      const previous = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => {
        previous?.();
        resolve(window.YT!);
      };
      const script = document.createElement("script");
      script.src = "https://www.youtube.com/iframe_api";
      script.async = true;
      document.head.appendChild(script);
    });
  }
  return apiPromise;
}

/** Read a video's length with an off-screen player (no YouTube Data API key needed). */
export async function fetchYouTubeDuration(videoId: string): Promise<number> {
  const YT = await loadYouTubeApi();
  return new Promise((resolve, reject) => {
    const host = document.createElement("div");
    host.style.cssText = "position:fixed;left:-9999px;width:200px;height:120px";
    document.body.appendChild(host);
    const cleanup = (p?: YTPlayer) => {
      try {
        p?.destroy();
      } catch {
        // ignore
      }
      host.remove();
    };
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error("timeout"));
    }, 10000);
    const player = new YT.Player(host, {
      videoId,
      events: {
        onReady: ({ target }) => {
          clearTimeout(timer);
          const d = Math.round(target.getDuration() || 0);
          cleanup(player);
          if (d > 0) resolve(d);
          else reject(new Error("no duration"));
        },
      },
    });
  });
}

const SAVE_EVERY_SECONDS = 10;

/**
 * Tracks how far a learner has watched a YouTube lesson (SDD §4.3, §6.3).
 * - polls `getCurrentTime()` every second while playing
 * - calls `onSavePosition` every 10 s of playback and on pause/unmount (resume support)
 * - calls `onComplete` once when currentTime / duration ≥ threshold (default 80 %)
 */
export function useYouTubeTracker({
  videoId,
  duration,
  startAt = 0,
  threshold = 0.8,
  alreadyCompleted = false,
  onSavePosition,
  onComplete,
}: {
  videoId: string | null;
  /** Lesson duration from the backend (seconds). 0 → use the player's own duration. */
  duration: number;
  startAt?: number;
  threshold?: number;
  alreadyCompleted?: boolean;
  onSavePosition: (second: number) => void;
  onComplete: (second: number) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<YTPlayer | null>(null);
  const [currentSecond, setCurrentSecond] = useState(startAt);
  const [effectiveDuration, setEffectiveDuration] = useState(duration);
  const [completed, setCompleted] = useState(alreadyCompleted);
  const [ready, setReady] = useState(false);

  // Keep latest callbacks/flags without re-creating the player
  const saveRef = useRef(onSavePosition);
  const completeRef = useRef(onComplete);
  const completedRef = useRef(alreadyCompleted);
  saveRef.current = onSavePosition;
  completeRef.current = onComplete;

  useEffect(() => {
    completedRef.current = alreadyCompleted;
    setCompleted(alreadyCompleted);
  }, [alreadyCompleted, videoId]);

  useEffect(() => {
    if (!videoId || !containerRef.current) return;
    let disposed = false;
    let interval: ReturnType<typeof setInterval> | undefined;
    let lastSaved = startAt;
    setReady(false);
    setCurrentSecond(startAt);

    const host = document.createElement("div");
    containerRef.current.replaceChildren(host);

    const totalOf = (p: YTPlayer) => (duration > 0 ? duration : Math.floor(p.getDuration() || 0));

    const save = (p: YTPlayer) => {
      const t = Math.floor(p.getCurrentTime() || 0);
      if (Math.abs(t - lastSaved) >= 2) {
        lastSaved = t;
        saveRef.current(t);
      }
    };

    const markComplete = (second: number) => {
      if (completedRef.current) return;
      completedRef.current = true;
      setCompleted(true);
      completeRef.current(second);
    };

    loadYouTubeApi().then((YT) => {
      if (disposed) return;
      playerRef.current = new YT.Player(host, {
        videoId,
        width: "100%",
        height: "100%",
        playerVars: { start: Math.floor(startAt), rel: 0, modestbranding: 1, playsinline: 1 },
        events: {
          onReady: ({ target }) => {
            if (disposed) return;
            setReady(true);
            setEffectiveDuration(totalOf(target));
          },
          onStateChange: ({ data, target }) => {
            if (data === YT.PlayerState.PAUSED) save(target);
            // Watching to the very end always counts, even if the stored duration is slightly off
            if (data === YT.PlayerState.ENDED) markComplete(Math.max(totalOf(target), Math.floor(target.getCurrentTime())));
          },
        },
      });

      interval = setInterval(() => {
        const p = playerRef.current;
        if (!p || p.getPlayerState?.() !== YT.PlayerState.PLAYING) return;
        const t = p.getCurrentTime() || 0;
        setCurrentSecond(t);
        const total = totalOf(p);
        if (total > 0) {
          setEffectiveDuration(total);
          if (t / total >= threshold) markComplete(Math.floor(t));
        }
        if (Math.floor(t) - lastSaved >= SAVE_EVERY_SECONDS) {
          lastSaved = Math.floor(t);
          saveRef.current(lastSaved);
        }
      }, 1000);
    });

    return () => {
      disposed = true;
      if (interval) clearInterval(interval);
      const p = playerRef.current;
      if (p) {
        try {
          save(p);
          p.destroy();
        } catch {
          // player already torn down
        }
      }
      playerRef.current = null;
    };
    // startAt is read once per video so seeking does not rebuild the player
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId, duration, threshold]);

  const watchedRatio = effectiveDuration > 0 ? Math.min(1, currentSecond / effectiveDuration) : 0;

  return { containerRef, playerRef, ready, currentSecond, duration: effectiveDuration, watchedRatio, completed };
}
