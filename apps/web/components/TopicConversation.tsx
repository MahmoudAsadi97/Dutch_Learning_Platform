"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { CurriculumRecorder, countWords } from "@/components/CurriculumControls";
import { LearningText } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { Icon } from "@/components/Icon";
import { apiJson, ApiError, newRequestId } from "@/lib/client/api";
import { friendlyError } from "@/lib/client/curriculum";
import { topicHref } from "@/lib/client/learning-agents";
import type { ConversationCatalog, ConversationChoice, ConversationSession, ConversationTurnRequest } from "@/lib/client/learning-agents";

type Props = {stageId: string; topicId: string; learnerKey: string; disabled?: boolean; onActivityChange: (value: boolean) => void; onOpenChange: (value: boolean) => void};
type Saved = {sessionId?: string; draft?: string; pending?: ConversationTurnRequest};

export function ConversationTopicChoices({stageId, learnerKey, onChoose}: {stageId: string; learnerKey: string; onChoose: (id: string) => void}) {
  const [choices, setChoices] = useState<ConversationChoice[]>([]);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<ConversationCatalog>(`topic-conversations?stage_id=${stageId}`, {signal: controller.signal}).then(catalog => {
      if (!controller.signal.aborted && catalog.learner_key === learnerKey) setChoices(catalog.items.filter(item => item.stage_id === stageId));
    }).catch(() => {});
    return () => controller.abort();
  }, [stageId, learnerKey]);
  if (!choices.length) return null;
  return <section className="conversation-topic-choices" aria-labelledby="conversation-topic-title"><h4 id="conversation-topic-title">Korte gesprekken</h4><p><LearningText text={{nl: "Bij deze onderwerpen kun je om de beurt antwoorden en vragen stellen. De andere onderwerpen blijven losse spreekopdrachten.", en: "These topics let you take turns answering and asking questions. Other topics remain individual speaking tasks.", fa: "در این موضوع‌ها می‌توانی به نوبت پاسخ بدهی و سؤال بپرسی. موضوع‌های دیگر همچنان تمرین‌های گفتاری مستقل هستند."}}/></p><div>{choices.map(choice => <button className="button secondary" key={choice.id} onClick={() => onChoose(choice.topic_id)}><Icon name="mic" size={17}/><LearningText text={choice.title}/></button>)}</div></section>;
}

/** The catalogue is free; a provider call only starts after a deliberate learner response. */
export function TopicConversation({stageId, topicId, learnerKey, disabled, onActivityChange, onOpenChange}: Props) {
  const [choice, setChoice] = useState<ConversationChoice | null>(null);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<ConversationCatalog>(`topic-conversations?stage_id=${stageId}`, {signal: controller.signal}).then(catalog => {
      if (!controller.signal.aborted && catalog.learner_key === learnerKey) setChoice(catalog.items.find(item => item.stage_id === stageId && item.topic_id === topicId) ?? null);
    }).catch(() => { /* The existing single-response task stays available when this optional pilot is unavailable. */ });
    return () => controller.abort();
  }, [stageId, topicId, learnerKey]);
  if (!choice) return null;
  return <section className="topic-conversation" aria-label="Oefengesprek">
    {!open ? <div className="conversation-invitation"><div><span className="eyebrow">VAN EEN ANTWOORD NAAR EEN GESPREK</span><h4>Oefen dit gesprek</h4><p><LearningText text={{nl: "Praat in korte beurten, stel een vraag en probeer samen iets te regelen. Je kunt spreken of typen.", en: "Take short turns, ask a question and work towards an agreement. Speak or type.", fa: "در نوبت‌های کوتاه صحبت کن، سؤال بپرس و برای رسیدن به توافق تمرین کن. می‌توانی حرف بزنی یا تایپ کنی."}}/></p></div><button className="button" disabled={disabled} onClick={() => {setOpen(true); onOpenChange(true);}}><Icon name="mic" size={17}/>Oefen dit gesprek</button></div> : <ConversationPractice key={`${learnerKey}.${choice.id}`} choice={choice} learnerKey={learnerKey} onActivityChange={onActivityChange} onRestart={() => setChoice({...choice, active_session_id: null})} onClose={() => {setOpen(false); onOpenChange(false);}}/>}
  </section>;
}

function ConversationPractice({choice, learnerKey, onActivityChange, onRestart, onClose}: {choice: ConversationChoice; learnerKey: string; onActivityChange: (value: boolean) => void; onRestart: () => void; onClose: () => void}) {
  const storageKey = `taalstudio.conversation.${learnerKey}.${choice.stage_id}.${choice.topic_id}`;
  const [saved] = useState<Saved>(() => {
    try {
      const raw: unknown = JSON.parse(sessionStorage.getItem(storageKey) ?? "{}");
      if (raw && typeof raw === "object") {
        const value = raw as Saved;
        return {sessionId: typeof value.sessionId === "string" && /^[a-zA-Z0-9_-]{8,80}$/.test(value.sessionId) ? value.sessionId : undefined, draft: typeof value.draft === "string" ? value.draft.slice(0, 2000) : "", pending: value.pending && /^[a-zA-Z0-9_-]{8,80}$/.test(value.pending.client_turn_id) ? value.pending : undefined};
      }
    } catch {}
    return {};
  });
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [mode, setMode] = useState<"typed" | "spoken">("typed");
  const [draft, setDraft] = useState(saved.draft ?? "");
  const [audioId, setAudioId] = useState("");
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [resumeMissing, setResumeMissing] = useState(false);
  const [restoring, setRestoring] = useState(Boolean(saved.sessionId || choice.active_session_id));
  const [error, setError] = useState("");
  const [storageError, setStorageError] = useState(false);
  const [recorderVersion, setRecorderVersion] = useState(0);
  const [reloadVersion, setReloadVersion] = useState(0);
  const request = useRef<AbortController | null>(null);
  const pending = useRef<ConversationTurnRequest | undefined>(saved.pending);
  const startId = useRef(newRequestId());
  const sessionRef = useRef<ConversationSession | null>(null);
  const draftRef = useRef(draft);
  const activity = useRef(onActivityChange);
  const latest = useRef<HTMLDivElement>(null);
  const stateBusy = busy || recording || restoring;
  const responseWords = countWords(draft);
  const resumeAvailable = !resumeMissing && Boolean(saved.sessionId || choice.active_session_id);
  useEffect(() => {activity.current = onActivityChange;}, [onActivityChange]);
  useEffect(() => {activity.current(stateBusy);}, [stateBusy]);
  useEffect(() => () => {request.current?.abort(); activity.current(false);}, []);
  function save(value: ConversationSession | null = sessionRef.current, text = draftRef.current) {
    try {sessionStorage.setItem(storageKey, JSON.stringify({sessionId: value?.id, draft: text, pending: pending.current})); setStorageError(false);} catch {setStorageError(true);}
  }
  function canonical(value: ConversationSession) {
    if (value.learner_key !== learnerKey || value.blueprint_id !== choice.id || value.stage_id !== choice.stage_id || value.topic_id !== choice.topic_id) throw new Error("Unexpected conversation");
    sessionRef.current = value; setSession(value); setMode(value.mode);
    if (pending.current && value.history.some(turn => turn.id === pending.current?.client_turn_id)) {
      if (pending.current.action === "respond") {draftRef.current = ""; setDraft(""); setAudioId(""); setRecorderVersion(version => version + 1);}
      pending.current = undefined;
    } else if (value.mode === "spoken" && value.status === "active" && pending.current?.action === "respond" && pending.current.expected_turn === value.turn_count && pending.current.audio_asset_id) {
      setAudioId(pending.current.audio_asset_id);
    }
    save(value);
    window.requestAnimationFrame(() => latest.current?.focus({preventScroll: true}));
  }
  useEffect(() => {
    const id = sessionRef.current?.id ?? saved.sessionId ?? choice.active_session_id;
    if (!id) return;
    const controller = new AbortController();
    apiJson<ConversationSession>(`topic-conversations/${encodeURIComponent(id)}`, {signal: controller.signal}).then(value => {
      if (!controller.signal.aborted) {canonical(value); setError(""); setRestoring(false);}
    }).catch(cause => {
      if (controller.signal.aborted) return;
      setRestoring(false);
      if (cause instanceof ApiError && [404, 403].includes(cause.status)) {setResumeMissing(true); pending.current = undefined; try {sessionStorage.removeItem(storageKey);} catch {} setError("Dit bewaarde gesprek is niet meer beschikbaar. Begin een nieuw gesprek.");}
      else setError(friendlyError(cause instanceof ApiError ? cause.status : undefined));
    });
    return () => controller.abort();
    // Identity is fixed by the keyed parent; reload only after a server turn conflict.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadVersion]);
  async function start() {
    if (stateBusy || request.current) return;
    const controller = new AbortController(); request.current = controller; setBusy(true); setError("");
    try {
      const value = await apiJson<ConversationSession>("topic-conversations/start", {method: "POST", signal: controller.signal, body: {blueprint_id: choice.id, request_id: startId.current, mode}});
      if (!controller.signal.aborted) canonical(value);
    } catch (cause) {if (!controller.signal.aborted) setError(friendlyError(cause instanceof ApiError ? cause.status : undefined));}
    finally {if (request.current === controller) {request.current = null; setBusy(false);}}
  }
  async function send(action: ConversationTurnRequest["action"]) {
    if (!session || session.status !== "active" || stateBusy || request.current) return;
    if (action === "respond" && (mode === "typed" ? responseWords < 1 || responseWords > 100 : !audioId)) return;
    const fields = {expected_turn: session.turn_count, action, ...(action === "respond" ? mode === "typed" ? {text: draft.trim()} : {audio_asset_id: audioId} : {})};
    const {client_turn_id: existingId, ...existingFields} = pending.current ?? {client_turn_id: ""};
    const payload: ConversationTurnRequest = JSON.stringify(existingFields) === JSON.stringify(fields) ? {...fields, client_turn_id: existingId} : {...fields, client_turn_id: newRequestId()};
    pending.current = payload; save();
    const controller = new AbortController(); request.current = controller; setBusy(true); setError("");
    try {
      const value = await apiJson<ConversationSession>(`topic-conversations/${session.id}/turns`, {method: "POST", signal: controller.signal, body: payload});
      if (!controller.signal.aborted) {
        pending.current = undefined;
        if (action === "respond") {draftRef.current = ""; setDraft(""); setAudioId(""); setRecorderVersion(version => version + 1);}
        canonical(value);
      }
    } catch (cause) {
      if (!controller.signal.aborted) {
        if (cause instanceof ApiError && cause.status === 409) {setError("Het gesprek is elders veranderd. We laden de laatste beurt; je concept blijft staan."); setRestoring(true); setReloadVersion(value => value + 1);}
        else setError(friendlyError(cause instanceof ApiError ? cause.status : undefined));
      }
    } finally {if (request.current === controller) {request.current = null; setBusy(false);}}
  }
  function restart() {
    if (stateBusy || request.current) return;
    sessionRef.current = null; setSession(null); setResumeMissing(true); pending.current = undefined;
    draftRef.current = ""; setDraft(""); setAudioId(""); setRecorderVersion(value => value + 1);
    setError(""); startId.current = newRequestId();
    try {sessionStorage.removeItem(storageKey);} catch {setStorageError(true);}
    onRestart();
  }
  async function finish() {
    if (!session || stateBusy || request.current) return;
    const controller = new AbortController(); request.current = controller; setBusy(true); setError("");
    try {
      const value = await apiJson<ConversationSession>(`topic-conversations/${session.id}/end`, {method: "POST", signal: controller.signal, body: {}});
      if (!controller.signal.aborted) {pending.current = undefined; canonical(value);}
    } catch (cause) {if (!controller.signal.aborted) setError(friendlyError(cause instanceof ApiError ? cause.status : undefined));}
    finally {if (request.current === controller) {request.current = null; setBusy(false);}}
  }
  return <div className="conversation-practice">
    <div className="conversation-toolbar"><h4>Jouw oefengesprek</h4><button className="button secondary" disabled={stateBusy} onClick={onClose}>Gesprek sluiten</button></div>
    {!session ? <>
      <p><LearningText text={choice.role}/></p>
      <fieldset disabled={stateBusy || resumeAvailable} className="conversation-mode"><legend>Hoe wil je antwoorden?</legend><label><input type="radio" name="conversation-mode" checked={mode === "typed"} onChange={() => {setMode("typed"); startId.current = newRequestId();}}/>Typen</label><label><input type="radio" name="conversation-mode" checked={mode === "spoken"} onChange={() => {setMode("spoken"); startId.current = newRequestId();}}/>Spreken met de microfoon</label></fieldset>
      <p className="small-text"><LearningText text={{nl: "Typen helpt je het gesprek voor te bereiden. Alleen ingesproken antwoorden oefenen ook je mondelinge productie. Beide zijn oefening, geen eindtoets.", en: "Typing helps you rehearse the conversation. Only recorded responses also practise spoken production. Both are practice, not a final test.", fa: "تایپ برای آماده شدن برای مکالمه است. فقط پاسخ‌های ضبط‌شده تولید گفتاری را هم تمرین می‌کنند. هر دو تمرین‌اند، نه آزمون پایانی."}}/></p>
      <button className="button" disabled={stateBusy} onClick={() => {if (resumeAvailable) {setRestoring(true); setReloadVersion(value => value + 1);} else void start();}}>{restoring ? "Je gesprek terughalen…" : busy ? "Je gesprek openen…" : resumeAvailable ? "Gesprek opnieuw laden" : "Begin het gesprek"}</button>
    </> : <>
      <p className="conversation-status"><span>{session.mode === "spoken" ? "Gesproken oefening" : "Getypte voorbereiding"}</span><span>{session.turn_count} / {session.max_turns} beurten</span></p>
      <p className="conversation-setup"><LearningText text={session.setup}/></p>
      <ol className="conversation-messages" aria-label="Jouw gesprek"><li className="conversation-partner"><strong><LearningText text={session.role}/></strong><p><LearningText text={session.opening}/><PhraseAudio text={session.opening.nl} disabled={stateBusy}/></p></li>{session.history.map(turn => <li key={turn.id} className="conversation-exchange">{turn.action === "respond" ? <div className="conversation-learner"><span className="small-text">Jij · {turn.mode === "spoken" ? "ingesproken" : "getypt"}</span><p lang="nl">{turn.learner_text}</p></div> : <p className="conversation-assistance">{turn.action === "hint" ? "Je vroeg om een hint." : "Je vroeg om herhaling."}</p>}<div className="conversation-partner"><p><LearningText text={turn.reply}/><PhraseAudio text={turn.reply.nl} disabled={stateBusy}/></p>{turn.assisted && <span className="small-text">Met hulp geoefend</span>}</div></li>)}</ol>
      <div ref={latest} tabIndex={-1} className="conversation-next" aria-live="polite">{session.status === "active" ? <><h5>Jouw volgende stap</h5><LearningText text={session.current_goal}/></> : <h5>{session.status === "completed" ? "Je gesprek is afgerond" : "Je hebt het gesprek beëindigd"}</h5>}</div>
      {session.status === "active" ? <>
        <p className="small-text">Herhaling en hints tellen mee als beurt. Je kunt de uitspraak ook beluisteren met het afspeelknopje.</p>
        <div className="conversation-help"><button className="button secondary" disabled={stateBusy} onClick={() => void send("repeat")}><LearningText text={{nl: "Herhaal de laatste vraag", en: "Repeat the last question", fa: "سؤال آخر را تکرار کن"}}/></button><button className="button secondary" disabled={stateBusy} onClick={() => void send("hint")}><LearningText text={{nl: "Geef me een hint", en: "Give me a hint", fa: "یک راهنمایی بده"}}/></button></div>
        {mode === "typed" ? <div className="conversation-composer"><label htmlFor="conversation-response">Jouw antwoord in het Nederlands</label><textarea id="conversation-response" rows={4} maxLength={2000} value={draft} disabled={busy || restoring} onChange={event => {draftRef.current = event.target.value; setDraft(event.target.value); pending.current = undefined; save();}}/><p className="small-text" role="status">{responseWords} / 100 woorden</p></div> : <CurriculumRecorder key={recorderVersion} disabled={busy || restoring} minWords={1} maxWords={100} maxSeconds={session.recording_max_seconds} onActivityChange={setRecording} onReady={assetId => {setAudioId(assetId); pending.current = undefined; save();}}/>}
        <div className="conversation-send"><button className="button" disabled={stateBusy || (mode === "typed" ? responseWords < 1 || responseWords > 100 : !audioId)} onClick={() => void send("respond")}>{busy ? "Even wachten…" : "Verstuur je antwoord"}<Icon name="arrow" size={17}/></button><button className="linklike" disabled={stateBusy} onClick={() => void finish()}>Stop en bekijk mijn oefening</button></div>
      </> : <div className="conversation-summary"><LearningText text={session.summary}/><ul>{session.goals.map((goal, index) => <li key={index}><span className="quiet-badge">{goal.met ? goal.assisted ? "Gelukt met hulp" : "Gelukt" : "Verder oefenen"}</span><LearningText text={goal.goal}/></li>)}</ul><p className="small-text">Dit gesprek telt niet als eindtoets of uitspraakbeoordeling.</p><div className="conversation-send"><button className="button" onClick={restart}>Oefen het gesprek opnieuw</button><button className="button secondary" onClick={onClose}>Verder met deze oefening</button><Link className="button secondary" href={topicHref(choice.stage_id, "writing", choice.topic_id) ?? "/"}>Schrijf over deze situatie<Icon name="pen" size={17}/></Link></div></div>}
    </>}
    {storageError && <p className="practice-hint" role="status">Je browser kan je concept niet bewaren. Kopieer je antwoord voordat je weggaat.</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}
