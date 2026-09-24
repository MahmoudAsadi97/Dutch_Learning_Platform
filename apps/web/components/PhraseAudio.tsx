"use client";

import { useEffect, useId, useSyncExternalStore } from "react";
import { Icon } from "@/components/Icon";
import { LearningText, type LearningCopy } from "@/components/LanguageSupport";
import { apiFetch } from "@/lib/client/api";
import { claimAudioFocus, isAudioRecording, observeNativeAudioFocus, releaseAudioFocus, subscribeAudioRecording } from "@/lib/client/audio-focus";
import { IDLE_PHRASE_AUDIO, PhraseAudioController, type PhraseAudioError } from "@/lib/client/phrase-audio";

const player = new PhraseAudioController({
  async synthesize(text, signal) {
    const response = await apiFetch("speech/synthesize", { method: "POST", body: { text, store: false }, signal });
    if (!response.ok) throw new Error(response.status === 401 || response.status === 403 ? "signin" : response.status === 429 ? "limit" : "unavailable");
    const type = response.headers.get("content-type") ?? "";
    if (!type.startsWith("audio/")) throw new Error("unavailable");
    const blob = await response.blob();
    if (!blob.size || blob.size > 8 * 1024 * 1024) throw new Error("unavailable");
    return { blob, developmentTone: response.headers.get("x-audio-voice") === "fixture-tone" };
  },
  player: url => new Audio(url),
  createUrl: blob => URL.createObjectURL(blob),
  revokeUrl: url => URL.revokeObjectURL(url),
});
const audioFocus = Symbol("pronunciation");
player.subscribe(() => {
  const { phase } = player.getSnapshot();
  if (phase === "loading" || phase === "playing") {
    if (!claimAudioFocus(audioFocus, () => player.stop())) player.stop();
  }
  else releaseAudioFocus(audioFocus);
});

const messages: Record<PhraseAudioError, LearningCopy> = {
  signin: { nl: "Meld je opnieuw aan om te luisteren.", en: "Sign in again to listen.", fa: "برای شنیدن دوباره وارد حساب شو." },
  limit: { nl: "Je luisterlimiet is bereikt. Probeer later opnieuw.", en: "Your audio allowance has been reached. Try again later.", fa: "سهمیهٔ صوتی تمام شده است. بعداً دوباره تلاش کن." },
  blocked: { nl: "Je browser vraagt nog een tik. Druk opnieuw op afspelen.", en: "Your browser needs another tap. Press play again.", fa: "مرورگر به یک بار لمس دیگر نیاز دارد. دوباره پخش را بزن." },
  unavailable: { nl: "De uitspraak is nu niet beschikbaar. Probeer opnieuw.", en: "The pronunciation audio is unavailable. Try again.", fa: "صدای تلفظ فعلاً در دسترس نیست. دوباره تلاش کن." },
  "too-long": { nl: "Kies een kortere tekst om te beluisteren.", en: "Choose a shorter text to listen to.", fa: "برای شنیدن متن کوتاه‌تری انتخاب کن." },
};

/** Compact explicit play/stop control. One pronunciation clip plays across all mounted buttons. */
export function PhraseAudio({ text, label, disabled = false }: { text: string; label?: string; disabled?: boolean }) {
  const owner = useId();
  const state = useSyncExternalStore(player.subscribe, player.getSnapshot, () => IDLE_PHRASE_AUDIO);
  const recording = useSyncExternalStore(subscribeAudioRecording, isAudioRecording, () => false);
  const own = state.owner === owner;
  const active = own && (state.phase === "loading" || state.phase === "playing");
  const unavailable = disabled || recording || !text.trim();
  useEffect(observeNativeAudioFocus, []);
  useEffect(() => () => player.stop(owner), [owner, text]);
  useEffect(() => { if (disabled) player.stop(owner); }, [disabled, owner]);
  const name = label ?? (text.length <= 90 ? text : `${text.slice(0, 87)}…`);
  const title = active ? `Stop: ${name}` : `Luister: ${name} · synthetische stem`;
  const error = own && state.phase === "error" ? state.error : undefined;
  return <span className="phrase-audio">
    <button type="button" className={`phrase-audio-button${active ? " is-playing" : ""}`} aria-label={title} title={title}
      aria-pressed={active} disabled={unavailable} aria-describedby={error ? `${owner}-error` : undefined}
      onClick={() => { if (active) player.stop(owner); else if (!isAudioRecording()) void player.play(owner, text); }}>
      {active ? <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><rect x="4" y="4" width="8" height="8" rx="1" fill="currentColor"/></svg> : <Icon name="volume" size={17}/>}
    </button>
    {error && <span className="phrase-audio-message" role="status" id={`${owner}-error`}><LearningText text={messages[error]}/></span>}
    {own && state.developmentTone && <span className="phrase-audio-message" role="status"><LearningText text={{ nl: "Testtoon; dit is geen uitspraakvoorbeeld.", en: "Test tone; this is not a pronunciation example.", fa: "صدای آزمایشی است؛ نمونهٔ تلفظ نیست." }}/></span>}
  </span>;
}
