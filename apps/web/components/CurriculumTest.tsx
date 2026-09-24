"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { CurriculumAudio, CurriculumQuestions, CurriculumRecorder, countWords } from "@/components/CurriculumControls";
import { Icon, type IconName } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { apiJson, ApiError, newRequestId } from "@/lib/client/api";
import { friendlyError, skillNames, skillOrder, stageLabel, type CurriculumAttempt, type CurriculumCatalog } from "@/lib/client/curriculum";
import { useNavigationGuard } from "@/lib/client/navigation";
import type { Skill } from "@/lib/types";

const skillIcons: Record<Skill, IconName> = { reading: "book", listening: "headphones", speaking: "mic", writing: "pen" };
interface TestDraft { reading: Record<string, number>; listening: Record<string, number>; writing: string }
const emptyDraft: TestDraft = { reading: {}, listening: {}, writing: "" };

export function CurriculumTest({ stageId }: { stageId: string }) {
  const [attempt, setAttempt] = useState<CurriculumAttempt | null>(null);
  const [skill, setSkill] = useState<Skill>("reading");
  const [draft, setDraft] = useState<TestDraft>(emptyDraft);
  const [audioId, setAudioId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [recordingBusy, setRecordingBusy] = useState(false);
  const [submissionLocked, setSubmissionLocked] = useState(false);
  const registerGuard = useNavigationGuard();
  useEffect(() => {
    registerGuard(async () => {
      if (busy || recordingBusy) { setError("Rond je opname af en wacht tot je werk is bewaard voordat je verdergaat."); return false; }
      return true;
    });
    return () => registerGuard(null);
  }, [busy, recordingBusy, registerGuard]);
  const [restoring, setRestoring] = useState(true);
  const requestId = useRef("");
  const [learnerKey, setLearnerKey] = useState("");
  const storageKey = `taalstudio.test.${learnerKey}.${stageId}`;
  useEffect(() => {
    const controller = new AbortController();
    let restoredKey = "";
    async function restore() {
      try {
        const catalog = await apiJson<CurriculumCatalog>("curriculum", { signal: controller.signal });
        setLearnerKey(catalog.learner_key);
        restoredKey = `taalstudio.test.${catalog.learner_key}.${stageId}`;
        const saved = sessionStorage.getItem(restoredKey);
        if (saved) {
          const value = JSON.parse(saved) as { id: string; draft: TestDraft; audioId?: string; submissionLocked?: boolean };
          const result = await apiJson<CurriculumAttempt>(`curriculum/attempts/${value.id}`, { signal: controller.signal });
          setAttempt(result);
          const savedSubmission = result.submission;
          setDraft(savedSubmission ? { reading: savedSubmission.reading_answers, listening: savedSubmission.listening_answers, writing: savedSubmission.writing_text } : value.draft ?? emptyDraft);
          setAudioId(savedSubmission?.speaking_asset_id ?? value.audioId ?? "");
          setSubmissionLocked(!!savedSubmission || !!value.submissionLocked);
        }
      } catch (cause) {
        if (cause instanceof ApiError && cause.status === 404) { try { sessionStorage.removeItem(restoredKey); } catch {} }
        else if (!(cause instanceof DOMException && cause.name === "AbortError")) setError("Je vorige toets kon niet worden hersteld. Probeer de pagina opnieuw te laden.");
      } finally { if (!controller.signal.aborted) setRestoring(false); }
    }
    void restore(); return () => controller.abort();
  }, [stageId]);
  function store(value: TestDraft, id = attempt?.id, asset = audioId, locked = submissionLocked) {
    setDraft(value);
    if (id) { try { sessionStorage.setItem(storageKey, JSON.stringify({ id, draft: value, audioId: asset, submissionLocked: locked })); } catch {} }
  }
  async function start() {
    setBusy(true); setError("");
    requestId.current ||= newRequestId();
    try {
      const result = await apiJson<CurriculumAttempt>(`curriculum/${stageId}/test`, { method: "POST", body: { request_id: requestId.current } });
      setAttempt(result); setSkill("reading"); setAudioId(""); setSubmissionLocked(false); store(emptyDraft, result.id, "", false);
    } catch (cause) { setError(cause instanceof ApiError && cause.status === 409 ? "Oefen eerst lezen, luisteren, spreken en schrijven. Daarna kun je deze eindtoets starten." : friendlyError(cause instanceof ApiError ? cause.status : undefined)); }
    finally { setBusy(false); }
  }
  async function submit() {
    if (!attempt) return;
    setBusy(true); setError(""); setSubmissionLocked(true); store(draft, attempt.id, audioId, true);
    try {
      const result = await apiJson<CurriculumAttempt>(`curriculum/attempts/${attempt.id}/submit`, { method: "POST", body: { reading_answers: draft.reading, listening_answers: draft.listening, writing_text: draft.writing, speaking_asset_id: audioId } });
      setAttempt(result);
    } catch (cause) {
      setError(friendlyError(cause instanceof ApiError ? cause.status : undefined));
      try {
        const saved = await apiJson<CurriculumAttempt>(`curriculum/attempts/${attempt.id}`);
        setAttempt(saved);
        if (saved.submission) {
          const snapshot = { reading: saved.submission.reading_answers, listening: saved.submission.listening_answers, writing: saved.submission.writing_text };
          setAudioId(saved.submission.speaking_asset_id); store(snapshot, attempt.id, saved.submission.speaking_asset_id, true);
        } else { setSubmissionLocked(false); store(draft, attempt.id, audioId, false); }
      } catch { /* Keep the submitted snapshot locked until a reliable retry confirms its state. */ }
    } finally { setBusy(false); }
  }
  const hasResult = attempt?.results && (attempt.status === "passed" || attempt.status === "needs_practice");
  const currentQuestions = attempt && (skill === "reading" || skill === "listening") ? attempt.test[skill].questions : [];
  const answersReady = !!attempt && attempt.test.reading.questions.every(question => draft.reading[question.id] !== undefined) && attempt.test.listening.questions.every(question => draft.listening[question.id] !== undefined);
  const words = countWords(draft.writing);
  return <div className="curriculum-test">
    <Link href={`/learn/${stageId}`} className="back-link">← Terug naar de oefeningen</Link>
    <header className="test-heading"><span className="stage-level">{stageLabel(stageId)}</span><div><p className="eyebrow">ZELFSTANDIG TOEPASSEN</p><h1>Laat zien wat je kunt.</h1></div></header>
    {error && <div className="error" role="alert">{error}</div>}
    {restoring ? <p role="status">Je toets klaarzetten…</p> : !attempt ? <section className="test-introduction"><h2>Vier vaardigheden, één volgende stap.</h2><p><LearningText text={{ nl: "Je leest, luistert, spreekt en schrijft in het Nederlands. Voor elk onderdeel moet je voldoende laten zien om het volgende niveau te openen.", en: "Read, listen, speak and write in Dutch. Each skill must meet the course criteria before the next stage opens.", fa: "به هلندی بخوان، گوش بده، صحبت کن و بنویس. برای باز شدن مرحلهٔ بعد، باید معیار هر چهار مهارت را برآورده کنی." }}/></p><div className="test-skill-preview">{skillOrder.map(item => <div key={item}><Icon name={skillIcons[item]}/><strong>{skillNames[item]}</strong></div>)}</div><ul><li>Maak een nieuwe geluidsopname tijdens deze toets.</li><li>Je kunt tussen de onderdelen wisselen voor je indient.</li><li>De antwoorden en luistertekst krijg je niet vooraf te zien.</li><li>Na de toets krijg je per vaardigheid een volgende oefenstap.</li></ul><p className="course-note">Dit is een interne voortgangstoets. Het resultaat is geen erkend CEFR-certificaat.</p><button className="button" onClick={() => void start()} disabled={busy}>{busy ? "Toets klaarzetten…" : "Start de eindtoets"}<Icon name="arrow"/></button></section> : hasResult ? <section className="test-results" aria-live="polite"><div className={`result-banner ${attempt.status === "passed" ? "passed" : "practice"}`}><Icon name={attempt.status === "passed" ? "check" : "book"} size={28}/><div><h2>{attempt.admin_preview ? "Je testweergave is afgerond." : attempt.status === "passed" ? "Je hebt dit niveau afgerond." : "Je weet nu wat je verder kunt oefenen."}</h2><p>{attempt.admin_preview ? "Dit is een testpoging. Er is geen leerlingniveau toegekend of ontgrendeld." : attempt.status === "passed" ? "Je volgende stap staat klaar op je leerpad." : "Bekijk je feedback per vaardigheid en probeer daarna opnieuw."}</p></div></div><div className="result-grid">{skillOrder.map(item => { const result = attempt.results![item]; return <article className="skill-result" key={item}><div><Icon name={skillIcons[item]}/><h3>{skillNames[item]}</h3><span className={result.passed ? "result-pass" : "result-practice"}>{result.passed ? "Voldoende" : "Verder oefenen"}</span></div><p><LearningText text={result.feedback}/></p>{result.total !== undefined && <p>{result.correct} van {result.total} juist</p>}{result.criteria?.length ? <ul>{result.criteria.map((criterion, index) => <li key={index}><strong>{criterion.met ? "✓ " : "↗ "}<LearningText text={criterion.criterion}/></strong><LearningText text={criterion.feedback}/></li>)}</ul> : null}</article>; })}</div><div className="test-actions"><Link className="button" href="/">Terug naar je leerpad<Icon name="arrow"/></Link><Link className="button secondary" href={`/learn/${stageId}`}>Verder oefenen</Link>{attempt.status !== "passed" && <button className="button secondary" onClick={() => { requestId.current = ""; setAttempt(null); setAudioId(""); try { sessionStorage.removeItem(storageKey); } catch {} }}>Nieuwe poging voorbereiden</button>}</div></section> : <div className="test-workspace">
      <nav className="test-tabs" aria-label="Onderdelen van de eindtoets">{skillOrder.map((item, index) => <button key={item} disabled={busy || recordingBusy} aria-current={skill === item ? "step" : undefined} onClick={() => setSkill(item)}><span>{index + 1}</span>{skillNames[item]}</button>)}</nav>
      <section className="test-paper" key={skill}><h2><Icon name={skillIcons[skill]}/>{skillNames[skill]}</h2>
        {skill === "reading" && <article className="story-panel"><div lang="nl" className="story-copy">{attempt.test.reading.text.nl}</div></article>}
        {skill === "listening" && <CurriculumAudio endpoint={`curriculum/attempts/${attempt.id}/listening`} parts={attempt.test.listening.audio_parts} disabled={busy}/>}
        {(skill === "reading" || skill === "listening") && <CurriculumQuestions questions={currentQuestions} answers={draft[skill]} onAnswer={(id, index) => store({ ...draft, [skill]: { ...draft[skill], [id]: index } })} exam disabled={busy || submissionLocked}/>}
        {(skill === "speaking" || skill === "writing") && <><div className="productive-task"><p><LearningText text={attempt.test[skill].prompt}/></p><ul className="task-criteria">{attempt.test[skill].criteria.map((criterion, index) => <li key={index}><LearningText text={criterion}/></li>)}</ul></div>{skill === "speaking" ? <><CurriculumRecorder onReady={id => { setAudioId(id); store(draft, attempt.id, id); }} onActivityChange={setRecordingBusy} minWords={attempt.test.speaking.min_words} maxWords={attempt.test.speaking.max_words} maxSeconds={attempt.policy?.recording_max_seconds} disabled={busy || submissionLocked}/>{audioId && <p className="practice-complete" role="status"><Icon name="check"/>Je opname is klaar om in te dienen.</p>}</> : <div className="writing-workspace"><label htmlFor="test-writing">Jouw antwoord in het Nederlands</label><textarea id="test-writing" disabled={busy || submissionLocked} rows={12} value={draft.writing} maxLength={12000} onChange={event => store({ ...draft, writing: event.target.value })}/><p className="writing-meta">{words} woorden · doel: {attempt.test.writing.min_words}–{attempt.test.writing.max_words}</p></div>}</>}
        <div className="test-section-actions">{skill !== "writing" && <button className="button secondary" disabled={busy || recordingBusy} onClick={() => setSkill(skillOrder[skillOrder.indexOf(skill) + 1])}>Volgende onderdeel<Icon name="arrow"/></button>}</div>
      </section>
      {submissionLocked && !busy && <p className="practice-hint" role="status">Je antwoorden zijn vastgezet tijdens het nakijken. Probeer dezelfde inzending opnieuw om veilig verder te gaan.</p>}
      <div className="test-submit-bar"><div><strong>Klaar met alle vier de onderdelen?</strong><p>{!answersReady ? "Beantwoord alle lees- en luistervragen." : !audioId ? "Maak een nieuwe opname voor spreken." : words < attempt.test.writing.min_words || words > attempt.test.writing.max_words ? `Schrijf tussen ${attempt.test.writing.min_words} en ${attempt.test.writing.max_words} woorden.` : "Je kunt je antwoorden nog controleren voordat je indient."}</p></div><button className="button" disabled={busy || recordingBusy || !answersReady || !audioId || words < attempt.test.writing.min_words || words > attempt.test.writing.max_words} onClick={() => void submit()}>{busy ? "Je werk wordt nagekeken…" : submissionLocked ? "Probeer dezelfde inzending opnieuw" : "Dien de eindtoets in"}<Icon name="check"/></button></div>
    </div>}
  </div>;
}
