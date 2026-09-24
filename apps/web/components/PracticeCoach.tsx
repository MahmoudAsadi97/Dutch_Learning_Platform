"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { LearningText } from "@/components/LanguageSupport";
import { Icon } from "@/components/Icon";
import { apiJson, ApiError, newRequestId } from "@/lib/client/api";
import { friendlyError, skillNames, stageLabel } from "@/lib/client/curriculum";
import { practiceStages, topicHref, type PracticePlan } from "@/lib/client/learning-agents";

export function PracticeCoach({learnerKey, initialStage = "a1"}: {learnerKey: string; initialStage?: string}) {
  const preferenceKey = `taalstudio.practice-stage.${learnerKey}`;
  const [stage, setStage] = useState(() => {
    try {const saved = localStorage.getItem(preferenceKey); if (saved && practiceStages.includes(saved)) return saved;} catch {}
    return practiceStages.includes(initialStage) ? initialStage : "a1";
  });
  const [plan, setPlan] = useState<PracticePlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [unavailable, setUnavailable] = useState(false);
  const pending = useRef<AbortController | null>(null);
  const requestId = useRef("");
  useEffect(() => {
    const controller = new AbortController();
    apiJson<PracticePlan>(`coach/plan?stage_id=${stage}`, {signal: controller.signal}).then(value => {
      if (!controller.signal.aborted) {setPlan(value); setError(""); setUnavailable(false);}
    }).catch(cause => {if (!controller.signal.aborted) {if (cause instanceof ApiError && cause.status === 404) setUnavailable(true); else setError(friendlyError(cause instanceof ApiError ? cause.status : undefined));}});
    return () => controller.abort();
  }, [stage, revision]);
  useEffect(() => () => pending.current?.abort(), []);
  async function personalise() {
    if (busy || !plan?.can_personalise || pending.current) return;
    const controller = new AbortController(); pending.current = controller;
    setBusy(true); setError("");
    requestId.current ||= newRequestId();
    try {
      const value = await apiJson<PracticePlan>("coach/plan", {method: "POST", signal: controller.signal, requestId: requestId.current, body: {stage_id: stage, request_id: requestId.current}});
      if (!controller.signal.aborted) {setPlan(value); requestId.current = "";}
    } catch (cause) {if (!controller.signal.aborted) setError(friendlyError(cause instanceof ApiError ? cause.status : undefined));}
    finally {if (pending.current === controller) {pending.current = null; setBusy(false);}}
  }
  if (unavailable) return null;
  const current = plan?.stage_id === stage ? plan : null;
  return <section className="practice-coach" aria-labelledby="practice-coach-title">
    <header className="practice-coach-heading"><div><p className="eyebrow">EEN KLEINE STAP VOORUIT</p><h2 id="practice-coach-title">Jouw volgende oefening</h2><p><LearningText text={{nl: "Kies je niveau. Deze suggesties helpen je om verschillende vaardigheden te gebruiken.", en: "Choose your level. These suggestions help you practise different skills.", fa: "سطحت را انتخاب کن. این پیشنهادها به تمرین مهارت‌های مختلف کمک می‌کنند."}}/></p></div><div><label htmlFor="practice-coach-stage">Mijn oefenniveau</label><select id="practice-coach-stage" value={stage} disabled={busy} onChange={event => {const value = event.target.value; setStage(value); setError(""); requestId.current = ""; try {localStorage.setItem(preferenceKey, value);} catch {}}}>{practiceStages.map(value => <option key={value} value={value}>{stageLabel(value)}</option>)}</select></div></header>
    {error && <div className="error" role="alert"><p>{error}</p>{!current && <button className="button secondary" onClick={() => setRevision(value => value + 1)}>Opnieuw proberen</button>}</div>}
    {!current && !error ? <p role="status">Je volgende stappen laden…</p> : current && <>
      <ol className="practice-recommendations">{current.items.map((item, index) => {
        const href = topicHref(item.stage_id, item.skill, item.topic_id);
        return href && <li key={item.id}><div className="recommendation-label"><span>{String(index + 1).padStart(2, "0")}</span><span>{skillNames[item.skill]} · {stageLabel(item.stage_id)}</span></div><h3><LearningText text={item.title}/></h3><p><LearningText text={item.reason}/></p><Link href={href} className="button secondary">Open deze oefening<Icon name="arrow" size={17}/></Link></li>;
      })}</ol>
      <div className="practice-coach-footer"><p className="small-text"><LearningText text={current.notice}/></p>{current.can_personalise && <button className="button secondary" disabled={busy} onClick={() => void personalise()}>{busy ? "Je oefenroute kiezen…" : "Stem de volgorde op mij af"}</button>}</div>
    </>}
  </section>;
}
