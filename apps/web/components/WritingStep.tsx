"use client";

import { useEffect, useRef, useState } from "react";

import { WritingCoach } from "@/components/WritingCoach";
import { LearningText } from "@/components/LanguageSupport";
import { ContentLabel } from "@/components/ContentLabel";
import { FeedbackPanel } from "@/components/FeedbackPanel";
import { HelpLadder } from "@/components/HelpLadder";
import type { StepProps } from "@/components/ReadingStep";
import { StepHeader } from "@/components/StepHeader";
import { ApiError } from "@/lib/client/api";
import { DraftSaver } from "@/lib/client/draft-saver";
import { recordHelp, saveDraft, submitWriting } from "@/lib/client/practice";
import type { HelpRung, Step, WritingPayload } from "@/lib/types";

interface Props extends StepProps {
  step: Step & { payload: WritingPayload };
}

const AUTOSAVE_MS = 1200;

export function countWords(text: string): number {
  return (text.match(/[\p{L}\p{N}'’-]+/gu) ?? []).length;
}

/**
 * The writing step: a message typed in Dutch. The draft autosaves into the session (not evidence);
 * the submitted message is stored as typed evidence with its word count and the required words found.
 */
export function WritingStep({ step, labels, detail, ensureSession, onDetail, onProgressChanged, registerBeforeLeave }: Props) {
  const { payload } = step;
  const draft = detail?.drafts[step.key];
  const progress = detail?.session.step_progress[step.key];
  const [text, setText] = useState(draft?.text ?? "");
  const [savedAt, setSavedAt] = useState<string>(draft?.saved_at ?? "");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const timerRef = useRef<number | null>(null);
  const textRef = useRef(text);
  const mountedRef = useRef(false);
  const persistRef = useRef<(text: string) => Promise<void>>(async () => {});
  const saverRef = useRef<DraftSaver | null>(null);
  // The autosave timer fires after later renders; it must merge into the newest detail, not the one it closed over.
  const detailRef = useRef(detail);
  useEffect(() => {
    detailRef.current = detail;
  }, [detail]);

  if (!saverRef.current) {
    saverRef.current = new DraftSaver(draft?.text ?? "", async (next) => {
      const current = detailRef.current ?? (await ensureSession());
      const saved = await saveDraft(current.session.id, step.key, next);
      const latest = detailRef.current ?? current;
      onDetail({ ...latest, drafts: { ...latest.drafts, [step.key]: saved } });
      if (mountedRef.current) setSavedAt(saved.saved_at);
    });
  }

  const words = countWords(text);
  const missing = payload.must_include.filter((item) => !text.toLowerCase().includes(item.toLowerCase()));
  const withinBounds = words >= payload.min_words && words <= payload.max_words;

  useEffect(() => {
    mountedRef.current = true;
    const warn = (event: BeforeUnloadEvent) => {
      if (!saverRef.current?.isSaved(textRef.current)) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    registerBeforeLeave?.(async () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
      try {
        await persistRef.current(textRef.current);
        return true;
      } catch {
        return false;
      }
    });
    return () => {
      mountedRef.current = false;
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
      window.removeEventListener("beforeunload", warn);
      registerBeforeLeave?.(null);
    };
  }, [registerBeforeLeave]);

  function scheduleSave(next: string) {
    if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => {
      timerRef.current = null;
      void persist(next).catch(() => undefined);
    }, AUTOSAVE_MS);
  }

  async function persist(next: string) {
    setSaving(true);
    setSaveError("");
    try {
      await saverRef.current!.save(next);
    } catch (cause) {
      if (mountedRef.current) setSaveError(cause instanceof ApiError ? `Niet bewaard: ${cause.detail}` : "Niet bewaard: geen verbinding.");
      throw cause;
    } finally {
      if (mountedRef.current) setSaving(false);
    }
  }

  useEffect(() => { persistRef.current = persist; });

  async function submit() {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      // Drain older autosaves before submission so none can overwrite the submitted draft afterwards.
      await persist(text);
      const current = detailRef.current ?? (await ensureSession());
      const result = await submitWriting(current, step.key, text);
      onDetail(result.detail);
      onProgressChanged();
      setNotice(
        `Ingediend: ${result.word_count} woorden.` +
          (result.missing.length > 0 ? ` Ontbreekt nog: ${result.missing.join(", ")}.` : payload.must_include.length ? " Alle vereiste woorden staan erin." : " Lees uw bericht na en vraag feedback."),
      );
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.detail : "Indienen mislukt: geen verbinding.");
    } finally {
      setBusy(false);
    }
  }

  async function help(rung: HelpRung) {
    const current = detailRef.current ?? (await ensureSession());
    onDetail(await recordHelp(current, step.key, rung));
  }

  return (
    <article aria-labelledby="step-title" data-step={step.key} data-step-type="writing">
      <StepHeader step={step} labels={labels} />

      <section className="card" aria-labelledby="prompt-heading">
        <h3 id="prompt-heading">Opdracht</h3>
        <p>
          <ContentLabel status={payload.prompt.review_status} labelNl={labels.unreviewed_nl} labelFa={labels.unreviewed_fa} />
        </p>
        <p><LearningText text={payload.prompt} /></p>
        <p className="muted" style={{ fontSize: "0.85rem" }}>
          {payload.min_words}–{payload.max_words} woorden{payload.must_include.length > 0 && ` · gebruik: ${payload.must_include.join(", ")}`}
        </p>
      </section>

      <section className="card" aria-labelledby="message-heading">
        <h3 id="message-heading">Uw bericht</h3>
        <label htmlFor={`writing-${step.key}`} className="visually-hidden">
          Uw bericht in het Nederlands
        </label>
        <textarea
          id={`writing-${step.key}`}
          value={text}
          lang="nl"
          rows={8}
          maxLength={4000}
          disabled={busy}
          onChange={(event) => {
            textRef.current = event.target.value;
            setText(event.target.value);
            scheduleSave(event.target.value);
          }}
          onBlur={() => {
            if (timerRef.current !== null) window.clearTimeout(timerRef.current);
            void persist(text).catch(() => undefined);
          }}
          data-testid="writing-input"
          style={{ width: "100%", font: "inherit", padding: "0.6rem", lineHeight: 1.5 }}
        />
        <p className="status-line">
          <span data-testid="word-count" className={withinBounds ? "" : "muted"}>
            {words} woorden{!withinBounds && ` (${payload.min_words}–${payload.max_words} nodig)`}
          </span>
          {missing.length > 0 ? (
            <span className="muted" data-testid="missing-words">
              nog te gebruiken: {missing.join(", ")}
            </span>
          ) : (
            <span className="label ok">alle vereiste woorden</span>
          )}
          <span className="muted" data-testid="autosave-status">
            {saveError ? saveError : saving || !saverRef.current?.isSaved(text) ? "wijzigingen bewaren…" : savedAt ? `bewaard ${new Date(savedAt).toLocaleTimeString("nl-BE", { hour: "2-digit", minute: "2-digit" })}` : "nog niet bewaard"}
          </span>
        </p>
        {saveError && (
          <p role="alert">
            <button type="button" className="button secondary" onClick={() => void persist(text).catch(() => undefined)} disabled={saving}>
              Opnieuw bewaren
            </button>
            <span className="muted"> Uw tekst blijft hier staan. Bewaar voordat u verdergaat.</span>
          </p>
        )}
        <p>
          <button type="button" className="button" onClick={() => void submit()} disabled={busy || !withinBounds} data-testid="writing-submit">
            {busy ? "Indienen…" : progress?.completed ? "Opnieuw indienen" : "Dien in"}
          </button>
          {progress?.completed && (
            <span className="label ok" style={{ marginInlineStart: "0.75rem" }} data-testid="writing-done">
              bericht opgeslagen
            </span>
          )}
        </p>
        {notice && (
          <p role="status" data-testid="writing-notice">
            {notice}
          </p>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </section>

      <WritingCoach stageId="a2" text={text} disabled={busy} onApply={value => {textRef.current = value; setText(value); scheduleSave(value);}}/>

      <section className="card" aria-labelledby="help-heading">
        <h3 id="help-heading">
          <LearningText text={{nl: "Hulp", en: "Help", fa: "کمک"}} />
        </h3>
        <HelpLadder rungs={payload.help} idPrefix={step.key} onReveal={help} />
      </section>

      <FeedbackPanel stepKey={step.key} detail={detail} onDetail={onDetail} onProgressChanged={onProgressChanged} />
    </article>
  );
}
