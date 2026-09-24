"use client";

import Link from "next/link";
import { WordLibrary, StoryTime, SpokenPassage } from "@/components/LearningLibrary";
import { AlphabetPractice } from "@/components/AlphabetPractice";
import { PhraseAudio } from "@/components/PhraseAudio";
import { SkillTopicPractice } from "@/components/SkillTopicPractice";
import { WritingCoach } from "@/components/WritingCoach";
import { CommunicationCoach } from "@/components/CommunicationCoach";
import { useEffect, useState } from "react";
import { CurriculumAudio, CurriculumQuestions, CurriculumRecorder, countWords } from "@/components/CurriculumControls";
import { Icon, type IconName } from "@/components/Icon";
import { LearningText, type LearningCopy } from "@/components/LanguageSupport";
import { apiJson, ApiError } from "@/lib/client/api";
import { friendlyError, skillNames, stageLabel, type CurriculumStage } from "@/lib/client/curriculum";
import { useNavigationGuard } from "@/lib/client/navigation";
import type { Skill } from "@/lib/types";

type Section = "words" | "grammar" | "stories" | "alphabet" | Skill;
const sections: { id: Section; label: string; icon: IconName }[] = [
  { id: "words", label: "Woorden", icon: "book" }, { id: "grammar", label: "Grammatica", icon: "pen" },
  { id: "reading", label: "Lezen", icon: "book" }, { id: "listening", label: "Luisteren", icon: "headphones" },
  { id: "speaking", label: "Spreken", icon: "mic" }, { id: "writing", label: "Schrijven", icon: "pen" },
  { id: "stories", label: "Story Time", icon: "book" },
];
interface PracticeResponse { completed: boolean; correct?: number; total?: number; feedback: LearningCopy }

export function CurriculumLesson({ stageId }: { stageId: string }) {
  const lessonSections = stageId === "pre-a1" ? [{id: "alphabet" as Section, label: "Alfabet", icon: "volume" as IconName}, ...sections] : sections;
  const [stage, setStage] = useState<CurriculumStage | null>(null);
  const [section, setSection] = useState<Section>("words");
  const [showCore, setShowCore] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [busy, setBusy] = useState(false);
  const [recordingBusy, setRecordingBusy] = useState(false);
  const registerGuard = useNavigationGuard();
  useEffect(() => {
    registerGuard(async () => {
      if (busy || recordingBusy) { setError("Rond je opname af en wacht tot je werk is bewaard voordat je verdergaat."); return false; }
      return true;
    });
    return () => registerGuard(null);
  }, [busy, recordingBusy, registerGuard]);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [writing, setWriting] = useState("");
  const [audioId, setAudioId] = useState("");
  const [feedback, setFeedback] = useState<PracticeResponse | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<CurriculumStage>(`curriculum/${stageId}`, { signal: controller.signal }).then(data => { setStage(data); setError(""); try { setWriting(sessionStorage.getItem(`taalstudio.draft.${data.learner_key}.${stageId}`) ?? ""); } catch {} }).catch(cause => { if (cause?.name !== "AbortError") setError(friendlyError(cause instanceof ApiError ? cause.status : undefined)); });
    return () => controller.abort();
  }, [stageId, retry]);
  function changeSection(next: Section) {
    if (busy || recordingBusy) return;
    setSection(next); setShowCore(false); setFeedback(null); setError("");
  }
  function answer(id: string, index: number) { setAnswers(current => ({ ...current, [id]: index })); setFeedback(null); }
  async function submit() {
    setBusy(true); setError("");
    try {
      const result = await apiJson<PracticeResponse>(`curriculum/${stageId}/practice`, { method: "POST", body: { skill: section, ...(section === "reading" || section === "listening" ? { answers: Object.fromEntries(questions.map(question => [question.id, answers[question.id]])) } : {}), ...(section === "writing" ? { text: writing } : {}), ...(section === "speaking" ? { audio_asset_id: audioId } : {}) } });
      setFeedback(result); setChecked(current => ({ ...current, [section]: true }));
      if (result.completed) setStage(await apiJson<CurriculumStage>(`curriculum/${stageId}`));
    } catch (cause) { setError(friendlyError(cause instanceof ApiError ? cause.status : undefined)); }
    finally { setBusy(false); }
  }
  if (!stage) return <div className="card">{error ? <><p role="alert">{error}</p><button className="button secondary" onClick={() => setRetry(value => value + 1)}>Opnieuw proberen</button><p><Link href="/">Terug naar je leerpad</Link></p></> : <p role="status">Je les laden…</p>}</div>;
  const progress = stage.progress ?? stage;
  const completed = progress.practice_completed ?? [];
  const isSkill = ["reading", "listening", "speaking", "writing"].includes(section);
  const questions = section === "reading" ? stage.lesson.reading_questions : stage.lesson.listening_questions;
  const task = section === "speaking" ? stage.lesson.speaking : stage.lesson.writing;
  const wordCount = countWords(writing);
  const allAnswered = questions.every(question => answers[question.id] !== undefined);
  return <div className="curriculum-lesson">
    <Link href="/" className="back-link">← Terug naar je leerpad</Link>
    <header className="lesson-heading"><span className="stage-level">{stageLabel(stageId)}</span><div><h1><LearningText text={stage.title}/></h1><p><LearningText text={stage.description}/></p></div></header>
    <div className="learning-workspace"><aside className="unit-sidebar"><p className="eyebrow">STAP VOOR STAP</p><nav aria-label="Onderdelen van dit niveau">{lessonSections.map(item => <button key={item.id} disabled={busy || recordingBusy} aria-current={section === item.id ? "step" : undefined} onClick={() => changeSection(item.id)}><Icon name={item.icon}/><span>{item.label}</span>{completed.includes(item.id as Skill) && <Icon name="check" size={15}/>}</button>)}</nav><div className="unit-test-card"><strong>{completed.length} van 4 vaardigheden geoefend</strong><p>Laat daarna zelfstandig zien wat je kunt.</p>{progress.test_available || stage.admin_bypass ? <Link className="button" href={`/learn/${stageId}/test`}>Naar de eindtoets<Icon name="arrow" size={16}/></Link> : <span className="test-unavailable"><Icon name="shield" size={16}/>Eindtoets opent na vier vaardigheden</span>}</div></aside>
      <div className="unit-content" key={section}><div className="unit-section-title"><p className="eyebrow">{stageLabel(stageId)} · {lessonSections.find(item => item.id === section)?.label}</p><h2>{section === "alphabet" ? "Letters horen, herkennen en gebruiken" : section === "stories" ? "Story Time" : section === "words" ? "Woorden die je kunt gebruiken" : section === "grammar" ? "Zo bouw je een zin" : section === "reading" ? "Een verhaal om te ontdekken" : section === "listening" ? "Luister naar de situatie" : section === "speaking" ? "Breng het gesprek op gang" : "Schrijf je eigen boodschap"}</h2></div>
        {isSkill && <div className="practice-source-switch" role="group" aria-label="Kies je oefenmateriaal"><button className="button secondary" aria-pressed={!showCore} disabled={busy || recordingBusy} onClick={() => {setShowCore(false); setFeedback(null); setError("");}}>Onderwerpen</button><button className="button secondary" aria-pressed={showCore} disabled={busy || recordingBusy} onClick={() => {setShowCore(true); setFeedback(null); setError("");}}>Startles</button></div>}
        {isSkill && !showCore && <SkillTopicPractice key={`${stage.learner_key}.${stageId}.${section}`} stageId={stageId} skill={section as Skill} learnerKey={stage.learner_key} maxSeconds={stage.policy?.recording_max_seconds} onActivityChange={setRecordingBusy} onCompleted={() => setRetry(value => value + 1)}/>}
        {section === "alphabet" && <AlphabetPractice/>}
        {section === "stories" && <StoryTime stageId={stageId}/>}
        {section === "words" && <><WordLibrary stageId={stageId}/><details className="core-word-list"><summary>Woorden bij de vier vaardigheidsopdrachten</summary><p>Deze leswoorden sluiten direct aan bij de lees-, luister-, spreek- en schrijfopdrachten.</p><div className="vocabulary-cards">{stage.vocabulary.map(word => <article className="core-word-card" key={word.id}><div className="word-card-heading"><h3 lang="nl">{word.term}</h3><PhraseAudio text={word.term}/></div><LearningText text={word.meaning}/><p><LearningText text={word.example}/><PhraseAudio text={word.example.nl}/></p></article>)}</div></details><button className="button" onClick={() => changeSection("grammar")}>Verder met grammatica<Icon name="arrow"/></button></>}
        {section === "grammar" && <>{stage.grammar.map(topic => <section className="grammar-card" key={topic.id}><h3><LearningText text={topic.title}/></h3><p><LearningText text={topic.explanation}/></p><div className="grammar-examples">{topic.examples.map((example, index) => <p key={index}><LearningText text={example}/><PhraseAudio text={example.nl}/></p>)}</div><CurriculumQuestions questions={topic.practice} answers={answers} onAnswer={answer} checked={!!checked[topic.id]}/><button className="button secondary" disabled={!topic.practice.every(question => answers[question.id] !== undefined)} onClick={() => setChecked(current => ({ ...current, [topic.id]: true }))}>Controleer je zin</button></section>)}<button className="button" onClick={() => changeSection("reading")}>Gebruik dit in een verhaal<Icon name="arrow"/></button></>}
        {showCore && section === "reading" && <><article className="story-panel"><p className="eyebrow">JOUW LEESVERHAAL</p><div className="story-copy"><SpokenPassage text={stage.lesson.story}/></div></article><h3>Wat heb je gelezen?</h3><CurriculumQuestions questions={questions} answers={answers} onAnswer={answer} checked={!!checked.reading} disabled={busy}/></>}
        {showCore && section === "listening" && <><CurriculumAudio endpoint={`curriculum/${stageId}/listening`} parts={stage.lesson.audio_parts} transcript={stage.lesson.listening}/><CurriculumQuestions questions={questions} answers={answers} onAnswer={answer} checked={!!checked.listening} disabled={busy}/></>}
        {showCore && (section === "speaking" || section === "writing") && <><div className="productive-task"><p><LearningText text={task.prompt}/></p><h3>Dit probeer je te doen</h3><ul className="task-criteria">{task.criteria.map((criterion, index) => <li key={index}><LearningText text={criterion}/></li>)}</ul></div>{section === "speaking" ? <><CommunicationCoach stageId={stageId}/><CurriculumRecorder onReady={asset => setAudioId(asset)} onActivityChange={setRecordingBusy} minWords={task.min_words} maxWords={task.max_words} maxSeconds={stage.policy?.recording_max_seconds} disabled={busy}/></> : <div className="writing-workspace"><label htmlFor="curriculum-writing">Jouw tekst</label><textarea id="curriculum-writing" disabled={busy} value={writing} onChange={event => { setWriting(event.target.value); setFeedback(null); try { sessionStorage.setItem(`taalstudio.draft.${stage.learner_key}.${stageId}`, event.target.value); } catch {} }} rows={9} maxLength={12000} placeholder="Schrijf hier in het Nederlands…"/><div className="writing-meta"><span>{wordCount} woorden · doel: {task.min_words}–{task.max_words}</span><span>Concept in dit tabblad</span></div></div>}{task.sample && <details className="sample-help"><summary>{task.sample_is_excerpt ? "Bekijk een voorbeeldbegin" : "Bekijk een voorbeeld als je vastzit"}</summary>{task.sample_is_excerpt && <p className="small-text muted">Dit is alleen een begin. Werk je eigen antwoord verder uit tot de gevraagde lengte.</p>}<p className="story-copy"><LearningText text={task.sample}/><PhraseAudio text={task.sample.nl}/></p></details>}</>}
        {showCore && section === "writing" && <WritingCoach stageId={stageId} text={writing} disabled={busy} onActivityChange={setRecordingBusy} onApply={value => {setWriting(value); setFeedback(null); try {sessionStorage.setItem(`taalstudio.draft.${stage.learner_key}.${stageId}`, value);} catch {}}}/>}
        {error && <p className="error" role="alert">{error}</p>}
        {isSkill && showCore && <div className="practice-submit"><button className="button" onClick={() => void submit()} disabled={busy || recordingBusy || ((section === "reading" || section === "listening") && !allAnswered) || (section === "speaking" && !audioId) || (section === "writing" && (wordCount < task.min_words || wordCount > task.max_words))}>{busy ? "Even nakijken…" : `Rond ${skillNames[section as Skill].toLowerCase()} af`}<Icon name="check" size={17}/></button>{completed.includes(section as Skill) && <span className="practice-complete"><Icon name="check" size={16}/>Geoefend</span>}</div>}
        {showCore && feedback && <div className={`practice-feedback ${feedback.completed ? "complete" : "retry"}`} role="status"><h3>{feedback.completed ? "Een stap verder." : "Probeer het nog eens."}</h3><LearningText text={feedback.feedback}/>{feedback.total !== undefined && <p>{feedback.correct} van {feedback.total} juist</p>}{feedback.completed && section !== "writing" && <button className="button secondary" disabled={busy || recordingBusy} onClick={() => {changeSection(sections[sections.findIndex(item => item.id === section) + 1].id); setShowCore(true);}}>Volgende vaardigheid<Icon name="arrow" size={17}/></button>}</div>}
        <p className="course-note">Nieuwe les · taalreview nog niet afgerond.</p>
      </div>
    </div>
  </div>;
}
