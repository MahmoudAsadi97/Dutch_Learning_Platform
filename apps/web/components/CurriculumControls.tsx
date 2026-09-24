"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { PhraseAudio } from "@/components/PhraseAudio";
import { Icon } from "@/components/Icon";
import { LearningText, type LearningCopy } from "@/components/LanguageSupport";
import { apiFetch, apiJson, ApiError } from "@/lib/client/api";
import { friendlyError, type CurriculumQuestion } from "@/lib/client/curriculum";
import { useRecorder, type Recording } from "@/lib/client/recorder";
import { claimAudioFocus, isAudioRecording, observeNativeAudioFocus, releaseAudioFocus, subscribeAudioRecording } from "@/lib/client/audio-focus";

export function CurriculumQuestions({ questions, answers, onAnswer, exam = false, checked = false, disabled = false }: { questions: CurriculumQuestion[]; answers: Record<string, number>; onAnswer: (id: string, index: number) => void; exam?: boolean; checked?: boolean; disabled?: boolean }) {
  return <div className="curriculum-questions">{questions.map((question, number) => <fieldset key={question.id} className="curriculum-question" disabled={disabled}>
    <legend><span className="question-number">{number + 1}</span>{exam ? question.prompt.nl : <LearningText text={question.prompt}/>}</legend>
    {!exam && <PhraseAudio text={question.prompt.nl} disabled={disabled}/>}
    <div className="answer-options">{question.options.map((option, index) => <div className="answer-option-shell" key={index}><label className={answers[question.id] === index ? "selected" : ""}><input type="radio" name={`q-${question.id}`} checked={answers[question.id] === index} onChange={() => onAnswer(question.id, index)}/>{exam ? <span lang="nl">{option.nl}</span> : <LearningText text={option}/>}</label>{!exam && <PhraseAudio text={option.nl} disabled={disabled}/>}</div>)}</div>
    {checked && question.answer_index !== undefined && <div className={answers[question.id] === question.answer_index ? "practice-correct" : "practice-hint"} role="status"><strong>{answers[question.id] === question.answer_index ? "Goed gedaan." : "Bekijk de uitleg en probeer opnieuw."}</strong>{question.explanation && <LearningText text={question.explanation}/>}</div>}
  </fieldset>)}</div>;
}

export function CurriculumAudio({ endpoint, parts = 1, transcript, disabled = false }: { endpoint: string; parts?: number; transcript?: LearningCopy; disabled?: boolean }) {
  return <CurriculumAudioPlayer key={endpoint} endpoint={endpoint} parts={parts} transcript={transcript} disabled={disabled}/>;
}

function CurriculumAudioPlayer({ endpoint, parts, transcript, disabled }: { endpoint: string; parts: number; transcript?: LearningCopy; disabled: boolean }) {
  const [busy, setBusy] = useState(false);
  const [developmentTone, setDevelopmentTone] = useState(false);
  const [part, setPart] = useState(0);
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef("");
  const controllerRef = useRef<AbortController | null>(null);
  const focusRef = useRef(Symbol("listening"));
  const recording = useSyncExternalStore(subscribeAudioRecording, isAudioRecording, () => false);
  useEffect(observeNativeAudioFocus, []);
  useEffect(() => {
    const player = audioRef.current;
    const focus = focusRef.current;
    return () => {
      controllerRef.current?.abort();
      releaseAudioFocus(focus);
      if (player) { player.pause(); player.removeAttribute("src"); player.load(); }
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    };
  }, []);
  function clearAudio() {
    controllerRef.current?.abort();
    releaseAudioFocus(focusRef.current);
    if (audioRef.current) { audioRef.current.pause(); audioRef.current.removeAttribute("src"); audioRef.current.load(); }
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    urlRef.current = ""; setUrl("");
  }
  async function play() {
    if (disabled || isAudioRecording()) return;
    controllerRef.current?.abort();
    releaseAudioFocus(focusRef.current);
    const request = new AbortController();
    controllerRef.current = request;
    // Claim focus during loading too: another clip or microphone request cancels stale synthesis.
    if (!claimAudioFocus(focusRef.current, () => {
      request.abort();
      audioRef.current?.pause();
      setBusy(false);
    })) return;
    setBusy(true); setError("");
    try {
      if (!urlRef.current) {
        const response = await apiFetch(`${endpoint}?part=${part}`, { method: "POST", signal: request.signal });
        if (!response.ok) throw new ApiError(response.status, "", "");
        if (!(response.headers.get("content-type") ?? "").startsWith("audio/")) throw new Error("Invalid audio response");
        const blob = await response.blob();
        if (request.signal.aborted) return;
        if (!blob.size || blob.size > 8 * 1024 * 1024) throw new Error("Invalid audio response");
        setDevelopmentTone(response.headers.get("x-audio-voice") === "fixture-tone");
        urlRef.current = URL.createObjectURL(blob); setUrl(urlRef.current);
      }
      if (request.signal.aborted || isAudioRecording()) return;
      const player = audioRef.current;
      if (player) {
        if (player.src !== urlRef.current) player.src = urlRef.current;
        player.currentTime = 0;
        // Native play events coordinate the active element after the network request completes.
        releaseAudioFocus(focusRef.current);
        await player.play().catch(() => { if (!request.signal.aborted) setError("Gebruik de afspeelknop hieronder om te luisteren."); });
      }
    } catch (cause) {
      if (!request.signal.aborted) setError(friendlyError(cause instanceof ApiError ? cause.status : undefined));
    } finally { if (controllerRef.current === request) { releaseAudioFocus(focusRef.current); setBusy(false); } }
  }
  return <div className="curriculum-audio"><div className="audio-intro"><span className="audio-icon"><Icon name="headphones" size={27}/></span><div><strong>Luister aandachtig</strong><p>{developmentTone ? "Testtoon; dit is geen luistervoorbeeld." : "Je mag opnieuw luisteren. Je hoort een synthetische stem."}</p></div></div><div className="audio-actions">{parts > 1 && <label>Fragment <select value={part} disabled={disabled || busy || recording} onChange={event => { clearAudio(); setPart(Number(event.target.value)); }}>{Array.from({ length: parts }, (_, index) => <option value={index} key={index}>{index + 1} / {parts}</option>)}</select></label>}<button className="button" onClick={() => void play()} disabled={disabled || busy || recording}><Icon name="volume"/>{busy ? "Even laden…" : "Luister naar het fragment"}</button></div><audio ref={audioRef} controls hidden={!url} aria-label="Luisterfragment"/>{error && <p role="status">{error}</p>}{transcript && <details className="transcript-help"><summary>Lees mee als je hulp nodig hebt</summary><p className="story-copy"><LearningText text={transcript}/></p></details>}</div>;
}

export function countWords(text: string) { return (text.match(/[\p{L}\p{N}_]+(?:['’\-][\p{L}\p{N}_]+)*/gu) ?? []).length; }

export function CurriculumRecorder({ onReady, onActivityChange, disabled = false, minWords = 1, maxWords = 150, maxSeconds = 60, initialTranscript = "" }: {
  onReady: (assetId: string, transcript: string) => void;
  onActivityChange?: (active: boolean) => void;
  disabled?: boolean; minWords?: number; maxWords?: number; maxSeconds?: number; initialTranscript?: string;
}) {
  const limit = Math.max(1, Math.min(58, maxSeconds - 1));
  const [busy, setBusy] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState("");
  const [transcript, setTranscript] = useState(initialTranscript);
  const [url, setUrl] = useState("");
  const urlRef = useRef("");
  const replayRef = useRef<HTMLAudioElement | null>(null);
  const uploadRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(false);
  const onActivityRef = useRef(onActivityChange);
  useEffect(() => { onActivityRef.current = onActivityChange; });
  useEffect(() => {
    mountedRef.current = true;
    const replay = replayRef.current;
    return () => {
      mountedRef.current = false;
      uploadRef.current?.abort();
      replay?.pause();
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      onActivityRef.current?.(false);
    };
  }, []);
  async function upload(recording: Recording) {
    if (!mountedRef.current) return;
    uploadRef.current?.abort();
    const request = new AbortController(); uploadRef.current = request;
    setBusy(true); setError(""); setTranscript(""); onReady("", "");
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    urlRef.current = URL.createObjectURL(recording.blob); setUrl(urlRef.current);
    const form = new FormData(); form.append("audio", recording.blob, recording.fileName); form.append("keep_recording", "true");
    try {
      const response = await apiJson<{ audio: { asset_id: string }; transcript: { text: string } }>("speech/transcribe", { method: "POST", formData: form, signal: request.signal });
      if (request.signal.aborted || !mountedRef.current) return;
      if (!response.transcript.text.trim()) throw new Error("empty");
      setTranscript(response.transcript.text);
      const words = countWords(response.transcript.text);
      onReady(words >= minWords && words <= maxWords ? response.audio.asset_id : "", response.transcript.text);
    } catch (cause) { if (!request.signal.aborted && mountedRef.current) setError(cause instanceof ApiError ? friendlyError(cause.status) : "We konden je niet goed verstaan. Probeer een nieuwe opname in een rustige ruimte."); }
    finally { if (uploadRef.current === request && mountedRef.current) setBusy(false); }
  }
  const recorder = useRecorder(recording => void upload(recording));
  const recording = recorder.phase === "recording";
  const stopRecording = recorder.stop;
  useEffect(() => { onActivityRef.current?.(recording || busy || requesting); }, [recording, busy, requesting]);
  useEffect(() => {
    if (!recording) return;
    const started = Date.now();
    const timer = window.setInterval(() => {
      const elapsed = Math.floor((Date.now() - started) / 1000);
      setSeconds(elapsed);
      if (elapsed >= limit) { stopRecording(); window.clearInterval(timer); }
    }, 200);
    return () => window.clearInterval(timer);
  }, [recording, stopRecording, limit]);
  const words = countWords(transcript);
  const withinBounds = words >= minWords && words <= maxWords;
  return <div className={`curriculum-recorder ${recording ? "is-recording" : ""}`}><span className="record-symbol" aria-hidden="true"><Icon name="mic" size={28}/></span><button type="button" className="button" disabled={disabled || busy || requesting || recorder.phase === "unsupported"} aria-pressed={recording} onClick={() => {
    if (recording) recorder.stop();
    else { onReady("", ""); setSeconds(0); setRequesting(true); void recorder.start().finally(() => { if (mountedRef.current) setRequesting(false); }); }
  }}>{recording ? "Stop de opname" : busy ? "Je opname verwerken…" : requesting ? "Microfoon openen…" : transcript ? "Opnieuw opnemen" : "Start de opname"}</button><p role="status">{recording ? `Opname: ${seconds} / ${limit} seconden. Klik op stoppen als je klaar bent.` : recorder.phase === "unsupported" ? "Deze browser kan geen geluid opnemen. Open de oefening in een actuele browser." : `Doel: ${minWords}–${maxWords} woorden. De opname stopt na ${limit} seconden.`}</p>{(error || recorder.error) && <p className="error" role="alert">{error || "Geef je browser toegang tot de microfoon en probeer opnieuw."}</p>}<audio ref={replayRef} controls src={url || undefined} hidden={!url} aria-label="Je eigen opname"/>{transcript && <><p className={withinBounds ? "practice-complete" : "practice-hint"} role="status">{words} woorden herkend · doel: {minWords}–{maxWords}.{!withinBounds && " Maak een nieuwe opname met de gevraagde lengte."}</p><details><summary>Dit hebben we verstaan</summary><p lang="nl">{transcript}</p><p className="small-text muted">Controleer of dit klopt. Maak bij herkenningsfouten een nieuwe opname.</p></details></>}<p className="small-text muted">Je opname wordt bij deze oefening bewaard. De beoordeling gaat over begrijpelijk communiceren, niet over een accentcijfer.</p></div>;
}
