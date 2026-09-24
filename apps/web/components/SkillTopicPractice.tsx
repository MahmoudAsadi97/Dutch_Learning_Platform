"use client";

import { useEffect, useRef, useState } from "react";
import { CurriculumAudio, CurriculumQuestions, CurriculumRecorder, countWords } from "@/components/CurriculumControls";
import { LearningText, useLanguageSupport } from "@/components/LanguageSupport";
import { SpokenPassage } from "@/components/LearningLibrary";
import { PhraseAudio } from "@/components/PhraseAudio";
import { ConversationTopicChoices, TopicConversation } from "@/components/TopicConversation";
import { WritingCoach } from "@/components/WritingCoach";
import { Icon, type IconName } from "@/components/Icon";
import { apiJson, ApiError, newRequestId } from "@/lib/client/api";
import { friendlyError, skillNames } from "@/lib/client/curriculum";
import type { TopicDetail, TopicFeedback, TopicPage } from "@/lib/client/topics";
import type { Skill } from "@/lib/types";

const icons: Record<Skill, IconName> = {reading: "book", listening: "headphones", speaking: "mic", writing: "pen"};
type Props = {stageId: string; skill: Skill; learnerKey: string; initialTopic?: string; maxSeconds?: number; onActivityChange: (busy: boolean) => void; onCompleted: () => void};

/** Only one page of summaries is fetched. A task is loaded after a deliberate choice. */
export function SkillTopicPractice(props: Props) {
  const {stageId, skill, learnerKey, onActivityChange} = props;
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("all");
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState(props.initialTopic ?? "");
  const [result, setResult] = useState<{key: string; page: TopicPage} | null>(null);
  const [failed, setFailed] = useState<{key: string; message: string} | null>(null);
  const {showEnglish, showPersian} = useLanguageSupport();
  const focusRef = useRef<HTMLHeadingElement>(null);
  const key = JSON.stringify([stageId, learnerKey, skill, query, category, status, offset, revision]);
  const data = result?.key === key ? result.page : null;
  const metadata = result?.page.stage_id === stageId && result.page.skill === skill && result.page.learner_key === learnerKey ? result.page : null;
  useEffect(() => {
    if (selected) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams({skill, q: query, category, status, offset: String(offset), limit: "12"});
      apiJson<TopicPage>(`curriculum/${stageId}/topics?${params}`, {signal: controller.signal})
        .then(page => {if (!controller.signal.aborted) setResult({key, page});})
        .catch(cause => {if (!controller.signal.aborted) setFailed({key, message: friendlyError(cause instanceof ApiError ? cause.status : undefined)});});
    }, query ? 180 : 0);
    return () => {window.clearTimeout(timer); controller.abort();};
  }, [key, selected, stageId, skill, query, category, status, offset]);

  if (selected) return <TopicReader key={`${learnerKey}.${stageId}.${skill}.${selected}`} {...props} topicId={selected} onBack={() => {
    setSelected(""); setRevision(value => value + 1); onActivityChange(false);
    window.requestAnimationFrame(() => focusRef.current?.focus());
  }}/>;

  return <section className="skill-topic-library" aria-label={`Onderwerpen voor ${skillNames[skill].toLowerCase()}`}>
    <div className="topic-library-intro"><div><p className="eyebrow">KIES · OEFEN · GROEI</p><h3 ref={focusRef} tabIndex={-1}>{metadata ? `${metadata.total_topics} onderwerpen voor ${skillNames[skill].toLowerCase()}` : `Onderwerpen voor ${skillNames[skill].toLowerCase()}`}</h3>
      <p><LearningText text={{nl: "Kies een situatie die bij je dag past. Elk onderwerp heeft een eigen opdracht. Je kunt vrij kiezen en zo vaak oefenen als je wilt.", en: "Choose a situation from everyday life. Each topic has its own task. Pick freely and practise as often as you like.", fa: "موقعیتی متناسب با روزت انتخاب کن. هر موضوع تمرین خودش را دارد. آزادانه انتخاب کن و هرقدر می‌خواهی تمرین کن."}}/></p></div>
      {metadata && <div className="topic-progress-summary"><span className="topic-progress-number">{metadata.completed_count}<span> / {metadata.total_topics}</span></span><span>onderwerpen geoefend</span><progress aria-label={`Voortgang ${skillNames[skill].toLowerCase()}`} max={metadata.total_topics || 1} value={metadata.completed_count}/><span className="small-text">Alleen deze vaardigheid</span></div>}
    </div>
    {skill === "speaking" && <ConversationTopicChoices stageId={stageId} learnerKey={learnerKey} onChoose={setSelected}/>}
    <div className="topic-filters">
      <div><label htmlFor="practice-topic-search">Zoek een situatie</label><input id="practice-topic-search" type="search" maxLength={120} value={query} placeholder="Bijvoorbeeld: trein, eten, werk…" onChange={event => {setQuery(event.target.value); setOffset(0);}}/></div>
      <div><label htmlFor="practice-topic-category">Thema</label><select id="practice-topic-category" value={category} onChange={event => {setCategory(event.target.value); setOffset(0);}}><option value="">Alle thema’s</option>{metadata?.categories.map(item => <option key={item.nl} value={item.nl}>{[item.nl, showEnglish && item.en, showPersian && item.fa].filter(Boolean).join(" · ")}</option>)}</select></div>
      <div><label htmlFor="practice-topic-status">Oefenstatus</label><select id="practice-topic-status" value={status} onChange={event => {setStatus(event.target.value); setOffset(0);}}><option value="all">Alles</option><option value="not_started">Nog niet begonnen</option><option value="completed">Geoefend</option></select></div>
    </div>
    {failed?.key === key ? <div className="error" role="alert"><p>{failed.message}</p><button className="button secondary" onClick={() => setRevision(value => value + 1)}>Opnieuw proberen</button></div> : !data ? <p role="status">Onderwerpen laden…</p> : <>
      {!data.total && <div className="topic-empty"><Icon name="book" size={32}/><h4>Geen onderwerpen gevonden</h4><p>Probeer een ander zoekwoord of toon alle thema’s.</p><button className="button secondary" onClick={() => {setQuery(""); setCategory(""); setStatus("all"); setOffset(0);}}>Toon alle onderwerpen</button></div>}
      <div className="topic-grid">{data.items.map((topic, index) => <article className={`topic-tile ${topic.completed ? "is-complete" : ""}`} key={topic.id}><div className="topic-tile-meta"><span className="topic-index">{String(offset + index + 1).padStart(2, "0")}</span><span className="small-text">{topic.completed ? "Geoefend" : topic.attempted ? "Opnieuw proberen" : "Nog ontdekken"}</span></div><span className="eyebrow">{topic.category.nl}</span><h4><LearningText text={topic.title}/></h4><button className="button secondary" aria-label={`Oefen ${topic.title.nl}`} onClick={() => setSelected(topic.id)}><Icon name={icons[skill]} size={17}/>{topic.completed ? "Oefen opnieuw" : "Begin met oefenen"}<Icon name="arrow" size={17}/></button></article>)}</div>
      <nav className="library-pagination" aria-label="Pagina’s met oefenonderwerpen"><button className="button secondary" disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 12))}>Vorige</button><span role="status">{data.total ? `${offset + 1}–${Math.min(offset + 12, data.total)} van ${data.total}` : "Geen resultaten"}</span><button className="button secondary" disabled={offset + 12 >= data.total} onClick={() => setOffset(value => value + 12)}>Volgende</button></nav>
    </>}
  </section>;
}

type Draft = {text: string; answers: Record<string, number>};
function loadDraft(key: string): Draft {
  const empty = {text: "", answers: {}};
  const raw = sessionStorage.getItem(key);
  if (!raw) return empty;
  try {
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== "object") return empty;
    const draft = value as Partial<Draft>;
    return {text: typeof draft.text === "string" ? draft.text.slice(0, 12000) : "", answers: Object.fromEntries(Object.entries(draft.answers ?? {}).filter(([key, index]) => key.length < 100 && Number.isInteger(index) && index >= 0 && index < 20))};
  } catch {return empty;}
}

function TopicReader({stageId, skill, learnerKey, maxSeconds, topicId, onActivityChange, onCompleted, onBack}: Props & {topicId: string; onBack: () => void}) {
  const draftKey = `taalstudio.topic-draft.${learnerKey}.${stageId}.${skill}.${topicId}`;
  const [initialDraft] = useState(() => {
    try {return {draft: loadDraft(draftKey), failed: false};}
    catch {return {draft: {text: "", answers: {}} as Draft, failed: true};}
  });
  const [topic, setTopic] = useState<TopicDetail | null>(null);
  const [loadError, setLoadError] = useState("");
  const [retry, setRetry] = useState(0);
  const [draft, setDraft] = useState<Draft>(initialDraft.draft);
  const [storageError, setStorageError] = useState(initialDraft.failed);
  const [submitBusy, setSubmitBusy] = useState(false);
  const [recordingBusy, setRecordingBusy] = useState(false);
  const [coachBusy, setCoachBusy] = useState(false);
  const [conversationBusy, setConversationBusy] = useState(false);
  const [conversationOpen, setConversationOpen] = useState(false);
  const submitKey = useRef<{fingerprint: string; key: string} | null>(null);
  const [audioId, setAudioId] = useState("");
  const [feedback, setFeedback] = useState<TopicFeedback | null>(null);
  const [error, setError] = useState("");
  const [showTranslation, setShowTranslation] = useState(false);
  const activityRef = useRef(onActivityChange);
  const completedRef = useRef(onCompleted);
  const submitRef = useRef<AbortController | null>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const busy = submitBusy || recordingBusy || coachBusy || conversationBusy;
  const endpoint = `curriculum/${stageId}/topics/${encodeURIComponent(topicId)}`;
  useEffect(() => {activityRef.current = onActivityChange; completedRef.current = onCompleted;});
  useEffect(() => {activityRef.current(busy);}, [busy]);
  useEffect(() => () => {submitRef.current?.abort(); activityRef.current(false);}, []);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<TopicDetail>(`${endpoint}?skill=${skill}`, {signal: controller.signal}).then(value => {
      if (!controller.signal.aborted) {setTopic(value); setLoadError(""); window.requestAnimationFrame(() => titleRef.current?.focus());}
    }).catch(cause => {if (!controller.signal.aborted) setLoadError(friendlyError(cause instanceof ApiError ? cause.status : undefined));});
    return () => controller.abort();
  }, [endpoint, skill, retry]);
  function updateDraft(next: Draft) {
    setDraft(next); setFeedback(null); setError("");
    try {sessionStorage.setItem(draftKey, JSON.stringify(next)); setStorageError(false);} catch {setStorageError(true);}
  }
  async function submit() {
    if (!topic || busy || submitRef.current) return;
    const controller = new AbortController(); submitRef.current = controller;
    setSubmitBusy(true); setError("");
    const questions = topic.activity.questions ?? [];
    try {
      const payload = {
        skill,
        ...(skill === "reading" || skill === "listening" ? {answers: Object.fromEntries(questions.map(question => [question.id, draft.answers[question.id]]))} : {}),
        ...(skill === "writing" ? {text: draft.text} : {}),
        ...(skill === "speaking" ? {audio_asset_id: audioId} : {}),
      };
      const fingerprint = JSON.stringify(payload);
      if (submitKey.current?.fingerprint !== fingerprint) submitKey.current = {fingerprint, key: newRequestId()};
      const response = await apiJson<TopicFeedback>(`${endpoint}/practice`, {method: "POST", signal: controller.signal, body: {...payload, request_id: submitKey.current.key}});
      if (!controller.signal.aborted) {
        submitKey.current = null;
        setFeedback(response);
        setTopic(current => current && ({...current, progress: {attempted: true, completed: current.progress.completed || response.completed}}));
        if (response.completed) completedRef.current();
      }
    } catch (cause) {if (!controller.signal.aborted) setError(friendlyError(cause instanceof ApiError ? cause.status : undefined));}
    finally {if (submitRef.current === controller) {submitRef.current = null; setSubmitBusy(false);}}
  }
  const questions = (topic?.activity.questions ?? []).map(question => {
    const explanation = feedback?.explanations?.find(item => item.id === question.id);
    return explanation ? {...question, answer_index: explanation.answer_index, explanation: explanation.explanation} : question;
  });
  const task = topic?.activity;
  const words = countWords(draft.text);
  const ready = topic && (skill === "reading" || skill === "listening" ? questions.length > 0 && questions.every(question => draft.answers[question.id] !== undefined) : skill === "speaking" ? !!audioId : words >= (task?.min_words ?? 1) && words <= (task?.max_words ?? 1));
  return <section className="topic-reader" aria-label="Oefenen met een onderwerp">
    <button className="back-link" disabled={busy} onClick={onBack}>← Alle onderwerpen</button>
    {!topic ? loadError ? <div className="error" role="alert"><p>{loadError}</p><button className="button secondary" onClick={() => setRetry(value => value + 1)}>Opnieuw proberen</button></div> : <p role="status">Je opdracht laden…</p> : <>
      <header className="topic-detail-heading"><div className="topic-detail-kicker"><span className="eyebrow">{topic.category.nl}</span>{topic.progress.completed && <span className="practice-complete"><Icon name="check" size={16}/>Al geoefend</span>}</div><h3 tabIndex={-1} ref={titleRef}><LearningText text={topic.title}/></h3><p className="topic-language-focus"><LearningText text={topic.language_focus}/></p></header>
      <details className="topic-goals"><summary>Wat oefen je hier?</summary><ul>{topic.objectives.map((goal, index) => <li key={index}><LearningText text={goal}/></li>)}</ul></details>
      {skill === "speaking" && <TopicConversation stageId={stageId} topicId={topicId} learnerKey={learnerKey} disabled={submitBusy || recordingBusy || coachBusy} onActivityChange={setConversationBusy} onOpenChange={setConversationOpen}/>}
      {!conversationOpen && <>
      {(skill === "speaking" || skill === "writing") && topic.context && <details className="topic-scene" open><summary>De situatie</summary><p className="small-text">Gebruik deze informatie voor jouw antwoord. Je hoeft geen andere oefening te openen.</p><h4>Wat je leest</h4><SpokenPassage text={topic.context.reading}/><h4>Het gesproken bericht</h4><SpokenPassage text={topic.context.listening}/></details>}
      {skill === "reading" && task?.text && <article className="story-panel topic-reading-text"><p className="eyebrow">LEES EN ONTDEK</p><SpokenPassage text={showTranslation ? task.text : {nl: task.text.nl}}/><button className="button secondary" aria-pressed={showTranslation} onClick={() => setShowTranslation(value => !value)}>{showTranslation ? "Vertaling verbergen" : "Vertaling tonen"}</button></article>}
      {skill === "listening" && task?.text && <CurriculumAudio endpoint={`${endpoint}/listening`} parts={task.audio_parts ?? 1} transcript={task.text} disabled={submitBusy}/>}
      {(skill === "reading" || skill === "listening") && <><h4>Wat heb je begrepen?</h4><CurriculumQuestions questions={questions} answers={draft.answers} onAnswer={(id, index) => updateDraft({...draft, answers: {...draft.answers, [id]: index}})} checked={!!feedback} disabled={submitBusy}/></>}
      {(skill === "speaking" || skill === "writing") && task?.prompt && <><div className="productive-task"><p><LearningText text={task.prompt}/><PhraseAudio text={task.prompt.nl} disabled={busy}/></p><h4>Dit probeer je te doen</h4><ul className="task-criteria">{task.criteria.map((criterion, index) => <li key={index}><LearningText text={criterion}/></li>)}</ul></div>
        {skill === "speaking" ? <CurriculumRecorder onReady={asset => {setAudioId(asset); setFeedback(null);}} onActivityChange={setRecordingBusy} disabled={submitBusy} minWords={task.min_words} maxWords={task.max_words} maxSeconds={topic.policy?.recording_max_seconds ?? maxSeconds}/> : <>
          <div className="writing-workspace"><label htmlFor="topic-writing">Jouw tekst bij dit onderwerp</label><textarea id="topic-writing" value={draft.text} disabled={submitBusy} rows={9} maxLength={12000} placeholder="Schrijf hier in het Nederlands…" onChange={event => updateDraft({...draft, text: event.target.value})}/><div className="writing-meta"><span>{words} woorden · doel: {task.min_words}–{task.max_words}</span><span>Concept per onderwerp in dit tabblad</span></div></div>
          <WritingCoach stageId={stageId} text={draft.text} disabled={submitBusy} onActivityChange={setCoachBusy} onApply={text => updateDraft({...draft, text})}/>
        </>}
        {task.sample && <details className="sample-help"><summary>{task.sample_is_excerpt ? "Bekijk een voorbeeldbegin" : "Bekijk een voorbeeld als je vastzit"}</summary>{task.sample_is_excerpt && <p>Dit is alleen een begin. Werk je eigen antwoord verder uit tot de gevraagde lengte.</p>}<p className="story-copy"><LearningText text={task.sample}/><PhraseAudio text={task.sample.nl} disabled={busy}/></p></details>}
      </>}
      <details className="topic-vocabulary"><summary>Woorden voor deze situatie</summary><div>{topic.vocabulary.map(word => <article key={word.id}><div className="word-card-heading"><h4 lang="nl">{word.term}</h4><PhraseAudio text={word.term} disabled={busy}/></div><LearningText text={word.meaning}/><p><LearningText text={word.example}/><PhraseAudio text={word.example.nl} disabled={busy}/></p></article>)}</div></details>
      {storageError && <p className="practice-hint" role="status">Je browser kan dit concept niet bewaren. Je tekst blijft hier staan; kopieer hem voordat je dit onderwerp verlaat.</p>}
      {error && <p className="error" role="alert">{error}</p>}
      <div className="practice-submit"><button className="button" disabled={busy || !ready} onClick={() => void submit()}>{submitBusy ? "Even nakijken…" : `Rond ${skillNames[skill].toLowerCase()} af`}<Icon name="check" size={17}/></button></div>
      {feedback && <div className={`practice-feedback ${feedback.completed ? "complete" : "retry"}`} role="status"><h4>{feedback.passed === false ? "Je hebt geoefend. Bekijk je volgende stap." : feedback.completed ? "Een onderwerp verder." : "Probeer het nog eens."}</h4><LearningText text={feedback.feedback}/>{feedback.total !== undefined && <p>{feedback.correct} van {feedback.total} juist</p>}{feedback.criteria && <ul className="topic-feedback-criteria">{feedback.criteria.map((item, index) => <li key={index}><strong><LearningText text={item.criterion}/></strong><span className="quiet-badge">{item.met ? "Gelukt" : "Verder oefenen"}</span><LearningText text={item.feedback}/></li>)}</ul>}<button className="button secondary" disabled={busy} onClick={onBack}>Kies een ander onderwerp<Icon name="arrow" size={17}/></button></div>}
    </>}
    </>}
  </section>;
}
