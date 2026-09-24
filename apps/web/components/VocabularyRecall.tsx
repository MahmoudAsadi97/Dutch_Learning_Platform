"use client";

import { useState } from "react";
import { LearningText, type LearningCopy } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";

type Word = { id: string; term: string; meaning: LearningCopy; example: LearningCopy };

/** A short recall round, deliberately separate from assessed skill evidence. */
export function VocabularyRecall({ words }: { words: Word[] }) {
  const [round, setRound] = useState<Word[]>([]);
  const [offset, setOffset] = useState(0);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [missed, setMissed] = useState<Word[]>([]);
  const [answer, setAnswer] = useState("");
  const [started, setStarted] = useState(false);
  function begin(next: Word[]) {
    setRound(next); setIndex(0); setMissed([]); setRevealed(false); setAnswer(""); setStarted(true);
  }
  function fresh() {
    const next = Array.from({ length: Math.min(5, words.length) }, (_, n) => words[(offset + n) % words.length]);
    setOffset((offset + next.length) % words.length); begin(next);
  }
  function remember(again: boolean) {
    if (again) setMissed(current => [...current, round[index]]);
    setIndex(value => value + 1); setRevealed(false); setAnswer("");
  }
  if (!words.length) return null;
  const active = started && index < round.length;
  const word = active ? round[index] : null;
  return <section className="recall-tool" aria-labelledby="recall-title" data-testid="vocabulary-recall">
    <div className="section-heading"><div><p className="eyebrow">EERST HERINNEREN, DAN KIJKEN</p><h3 id="recall-title">Vijf woorden uit je hoofd.</h3></div>{started && <button className="linklike" onClick={() => setStarted(false)}>Ronde sluiten</button>}</div>
    {!started ? <><p><LearningText text={{ nl: "Bekijk de betekenis, haal het Nederlandse woord uit je geheugen en maak er een eigen zin mee. Vergelijk pas daarna.", en: "Read the meaning, recall the Dutch word and use it in your own sentence. Then compare.", fa: "معنی را بخوان، واژهٔ هلندی را از حافظه به یاد بیاور و با آن جمله بساز. سپس پاسخ را مقایسه کن." }}/></p><button className="button secondary" onClick={fresh}>Start een korte woordronde</button></>
      : word ? <><p className="recall-counter" role="status">Woord {index + 1} van {round.length}</p><div className="recall-cue"><LearningText text={word.meaning}/></div><label htmlFor="recall-answer"><LearningText text={{ nl: "Welk woord past? Zeg het hardop of schrijf het hier.", en: "Which word fits? Say it aloud or write it here.", fa: "کدام واژه مناسب است؟ آن را با صدای بلند بگو یا اینجا بنویس." }}/></label><input id="recall-answer" value={answer} onChange={event => setAnswer(event.target.value)} autoComplete="off" maxLength={150} disabled={revealed}/>
        {!revealed ? <button className="button secondary" onClick={() => setRevealed(true)}>Vergelijk je antwoord</button> : <div className="recall-reveal"><h4 lang="nl">{word.term} <PhraseAudio text={word.term}/></h4><p className="phrase-line"><LearningText text={word.example}/><PhraseAudio text={word.example.nl}/></p><p><LearningText text={{ nl: "Maak nu zelf een andere zin. Kies eerlijk hoe het ging; een passend synoniem kan ook goed zijn.", en: "Make a different sentence yourself. Judge honestly how recall went; a suitable synonym can also be right.", fa: "حالا خودت جملهٔ دیگری بساز. صادقانه بگو یادآوری چطور بود؛ مترادف مناسب هم می‌تواند درست باشد." }}/></p><div className="recall-actions"><button className="button secondary" onClick={() => remember(true)}>Nog eens oefenen</button><button className="button" onClick={() => remember(false)}>Ik herinnerde het me</button></div></div>}</>
        : <div role="status"><h4>Deze ronde is afgerond.</h4><p>{missed.length ? `${missed.length} van ${round.length} woorden wil je opnieuw oefenen.` : `Je gaf aan dat je alle ${round.length} woorden kon herinneren.`}</p><div className="recall-actions">{missed.length > 0 && <button className="button" onClick={() => begin(missed)}>Herhaal de lastige woorden</button>}<button className="button secondary" onClick={fresh}>Een volgende woordronde</button></div></div>}
    <p className="course-note"><LearningText text={{ nl: "Zelfinschatting voor deze oefenronde. Dit verandert je toetsresultaten niet. Probeer de woorden op een andere dag opnieuw.", en: "Self-assessment for this round only. It does not change test results. Try the words again on another day.", fa: "این خودارزیابی فقط برای همین تمرین است و نتیجهٔ آزمون را تغییر نمی‌دهد. روز دیگری دوباره واژه‌ها را تمرین کن." }}/></p>
  </section>;
}
