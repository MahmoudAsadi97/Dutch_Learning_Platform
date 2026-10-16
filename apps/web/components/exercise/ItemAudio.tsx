"use client";

import { useEffect, useId, useSyncExternalStore } from "react";

import { Button } from "@/components/ui/Button";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import { ApiError } from "@/lib/client/api";
import {
  claimAudioFocus,
  isAudioRecording,
  observeNativeAudioFocus,
  releaseAudioFocus,
  subscribeAudioRecording,
} from "@/lib/client/audio-focus";
import { exercises } from "@/lib/client/exercises";
import { IDLE_PHRASE_AUDIO, PhraseAudioController, type PhraseAudioError } from "@/lib/client/phrase-audio";
import { storyLearningCopy } from "@/lib/copy/storyLearning";
import type { Copy } from "@/lib/ui-copy";

/**
 * The sound of an item, fetched from the item's audio route (the spoken text never reaches the browser as
 * text) and kept for the tab, so hearing it again costs nothing. One sound plays at a time, here and in the rest
 * of the app; a recording silences it.
 */
const player = new PhraseAudioController({
  async synthesize(key, signal) {
    const [sessionId, itemId] = key.split("/");
    try {
      return await exercises.audio(sessionId, itemId, signal);
    } catch (cause) {
      if (cause instanceof ApiError)
        throw new Error(
          cause.status === 401 || cause.status === 403
            ? "signin"
            : cause.status === 429
              ? "limit"
              : "unavailable",
        );
      throw cause;
    }
  },
  player: (url) => new Audio(url),
  createUrl: (blob) => URL.createObjectURL(blob),
  revokeUrl: (url) => URL.revokeObjectURL(url),
});
const focus = Symbol("exercise-audio");
player.subscribe(() => {
  const { phase } = player.getSnapshot();
  if (phase === "loading" || phase === "playing") {
    if (!claimAudioFocus(focus, () => player.stop())) player.stop();
  } else releaseAudioFocus(focus);
});

const ERRORS: Record<PhraseAudioError, Copy> = {
  support: storyLearningCopy.audioSupportFailed,
  signin: exerciseCopy.audioSignin,
  limit: exerciseCopy.audioLimit,
  blocked: exerciseCopy.audioBlocked,
  unavailable: exerciseCopy.audioUnavailable,
  "too-long": exerciseCopy.audioUnavailable,
};

interface Props {
  sessionId: string;
  itemId: string;
  /** Read-only once answered: it can still be heard again. */
  disabled?: boolean;
}

/** "Luister": plays the item's sound (and stops it); a failure says why in words. */
export function ItemAudio({ sessionId, itemId, disabled = false }: Props) {
  const owner = useId();
  const key = `${sessionId}/${itemId}`;
  const state = useSyncExternalStore(player.subscribe, player.getSnapshot, () => IDLE_PHRASE_AUDIO);
  const recording = useSyncExternalStore(subscribeAudioRecording, isAudioRecording, () => false);
  const own = state.owner === owner;
  const active = own && (state.phase === "loading" || state.phase === "playing");
  const error = own && state.phase === "error" ? state.error : undefined;
  useEffect(observeNativeAudioFocus, []);
  useEffect(() => () => player.stop(owner), [owner, key]);
  return (
    <div className="item-audio">
      <Button
        variant="secondary"
        icon="volume"
        aria-pressed={active}
        disabled={disabled || recording}
        onClick={() => {
          if (active) player.stop(owner);
          else if (!isAudioRecording()) void player.play(owner, key);
        }}
      >
        <UiText text={active ? exerciseCopy.audioStop : exerciseCopy.audioPlay} inline />
      </Button>
      <span className="item-audio-status" role="status">
        {error && <UiText text={ERRORS[error]} tier="guide" />}
        {own && state.developmentTone && <UiText text={exerciseCopy.audioTestTone} tier="guide" />}
      </span>
    </div>
  );
}
