"use client";

import { useCallback, useEffect, useRef } from "react";

interface Active {
  player: HTMLAudioElement;
  url: string;
  /** Resolves once the play() promise settled, whatever its outcome. */
  settled: Promise<void>;
}

export interface PlaybackResult {
  /** The browser refused to start playback without a user gesture; a visible control still works. */
  blocked: boolean;
  failed: boolean;
  /** Object URL of the blob, valid until the next `play()` or `stop()`; a visible `<audio controls>` may show it. */
  url: string;
}

/**
 * Plays WAV blobs one at a time through a fresh `Audio` object whose `play()` promise is always observed,
 * and only after the previous playback settled. Swapping the source of one shared element while an earlier
 * `play()` is still pending makes the browser reject that promise as an "aborted" load; this keeps each
 * playback on its own element so no rejection is ever left unhandled. A visible `<audio controls>` element
 * may be given the returned `url` for manual replay; it is never played from script.
 */
export function usePlayback() {
  const activeRef = useRef<Active | null>(null);

  const stop = useCallback(async () => {
    const active = activeRef.current;
    if (!active) return;
    activeRef.current = null;
    await Promise.race([active.settled, new Promise<void>((resolve) => setTimeout(resolve, 3000))]);
    active.player.onended = null;
    active.player.pause();
    active.player.removeAttribute("src");
    active.player.load();
    URL.revokeObjectURL(active.url);
  }, []);

  useEffect(() => {
    return () => {
      void stop();
    };
  }, [stop]);

  const play = useCallback(
    async (wav: Blob, onEnded?: () => void): Promise<PlaybackResult> => {
      await stop();
      const url = URL.createObjectURL(wav);
      const player = new Audio(url);
      player.onended = () => onEnded?.();
      const result: PlaybackResult = { blocked: false, failed: false, url };
      const settled = player.play().then(
        () => undefined,
        (cause: unknown) => {
          const name = cause instanceof DOMException ? cause.name : "";
          if (name === "NotAllowedError") result.blocked = true;
          else if (name !== "AbortError") result.failed = true;
        },
      );
      activeRef.current = { player, url, settled };
      await settled;
      return result;
    },
    [stop],
  );

  return { play, stop };
}
