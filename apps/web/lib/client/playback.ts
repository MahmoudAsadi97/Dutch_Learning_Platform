"use client";

import { useCallback, useEffect, useRef } from "react";
import { claimAudioFocus, observeNativeAudioFocus, releaseAudioFocus } from "@/lib/client/audio-focus";

interface Active {
  player: HTMLAudioElement;
  url: string;
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
 * and stops the previous playback immediately. A pending `play()` can reject as an aborted load; its
 * rejection is observed below. Each playback uses its own element, and shares audio focus with phrase
 * buttons so two synthetic examples never overlap. A visible `<audio controls>` element
 * may be given the returned `url` for manual replay; it is never played from script.
 */
export function usePlayback() {
  const activeRef = useRef<Active | null>(null);
  const owner = useRef(Symbol("playback"));
  useEffect(observeNativeAudioFocus, []);

  const stop = useCallback(async () => {
    releaseAudioFocus(owner.current);
    const active = activeRef.current;
    if (!active) return;
    activeRef.current = null;
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
      if (!claimAudioFocus(owner.current, () => { void stop(); })) return { blocked: true, failed: false, url: "" };
      const url = URL.createObjectURL(wav);
      const player = new Audio(url);
      player.onended = () => { releaseAudioFocus(owner.current); onEnded?.(); };
      const result: PlaybackResult = { blocked: false, failed: false, url };
      const settled = player.play().then(
        () => undefined,
        (cause: unknown) => {
          const name = cause instanceof DOMException ? cause.name : "";
          if (name === "NotAllowedError") result.blocked = true;
          else if (name !== "AbortError") result.failed = true;
        },
      );
      activeRef.current = { player, url };
      await settled;
      return result;
    },
    [stop],
  );

  return { play, stop };
}
