"use client";

import { useEffect, useRef, useState } from "react";
import { LearningText, type LearningCopy } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { apiJson, ApiError } from "@/lib/client/api";
import { friendlyError } from "@/lib/client/curriculum";

type Correction = {original: string; replacement: string; category: string; explanation: LearningCopy};
type Feedback = {stage_id?: string; original_text: string; corrected_text: string; corrections: Correction[]; summary: LearningCopy; review_status: string};
const categories: Record<string, string> = {spelling: "Spelling", grammar: "Grammatica", word_order: "Woordvolgorde", punctuation: "Leestekens", word_choice: "Woordkeuze"};

export function WritingCoach({stageId, text, onApply, disabled = false, onActivityChange}: {stageId: string; text: string; onApply: (text: string) => void; disabled?: boolean; onActivityChange?: (active: boolean) => void}) {
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState<{text: string; stage: string; message: string} | null>(null);
  const controller = useRef<AbortController | null>(null);
  const activity = useRef(onActivityChange);
  useEffect(() => {activity.current = onActivityChange;});
  useEffect(() => () => {controller.current?.abort(); activity.current?.(false);}, [text, stageId]);
  useEffect(() => () => {controller.current?.abort(); activity.current?.(false);}, []);
  async function review() {
    controller.current?.abort(); const request = new AbortController(); controller.current = request;
    setBusy(true); activity.current?.(true); setError(null);
    try {
      const result = await apiJson<Feedback>(`curriculum/${stageId}/writing-feedback`, {method: "POST", body: {text}, signal: request.signal});
      if (!request.signal.aborted && result.original_text === text) setFeedback({...result, stage_id: stageId});
    } catch (cause) {if (!request.signal.aborted) setError({text, stage: stageId, message: friendlyError(cause instanceof ApiError ? cause.status : undefined)});}
    finally {if (controller.current === request) {setBusy(false); activity.current?.(false);}}
  }
  const valid = feedback?.original_text === text && feedback.stage_id === stageId ? feedback : null;
  return <section className="writing-coach" aria-label="Schrijfhulp"><div className="section-heading"><div><h3>Maak je tekst sterker</h3><p><LearningText text={{nl: "Bekijk wat je kunt verbeteren en waarom. Je oorspronkelijke tekst blijft staan totdat je zelf een wijziging kiest.", en: "See what to correct and why. Your original stays unchanged until you choose to revise it.", fa: "ببین چه چیزی را باید اصلاح کنی و چرا. متن اصلی تا وقتی خودت تغییری را انتخاب نکنی، حفظ می‌شود."}}/></p></div></div><button className="button secondary" onClick={() => void review()} disabled={disabled || busy || !text.trim()}>{busy ? "Je tekst nakijken…" : "Controleer spelling en grammatica"}</button>{busy && <span className="small-text" role="status">Even nakijken. Je tekst blijft bewaard.</span>}{error?.text === text && error.stage === stageId && <p role="alert" className="error">{error.message}</p>}
    {valid && <div className="writing-review"><p role="status"><LearningText text={valid.summary}/></p>{valid.corrections.length > 0 && <><ol className="correction-list">{valid.corrections.map((correction, index) => <li key={index}><span className="quiet-badge">{categories[correction.category] ?? "Taal"}</span><div className="correction-pair"><div><span className="small-text">Jij schreef</span><p lang="nl"><del>{correction.original}</del></p></div><div><span className="small-text">Voorstel</span><p lang="nl"><ins>{correction.replacement || "Weglaten"}</ins></p>{correction.replacement && <PhraseAudio text={correction.replacement}/>}</div></div><LearningText text={correction.explanation}/></li>)}</ol><details className="corrected-draft"><summary>Je tekst met deze verbeteringen</summary><p lang="nl">{valid.corrected_text}</p><PhraseAudio text={valid.corrected_text}/><button className="button secondary" disabled={disabled || busy} onClick={() => onApply(valid.corrected_text)}>Gebruik als nieuwe versie</button></details><p className="small-text muted">Een taalvoorstel kan een fout bevatten. Controleer of je bedoeling hetzelfde blijft.</p></>}</div>}
  </section>;
}
