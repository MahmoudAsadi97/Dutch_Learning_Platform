"use client";

import { useId, useState } from "react";
import { LearningText } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { DUTCH_ALPHABET, DUTCH_LETTER_PAIRS, letterQuestion } from "@/lib/alphabet";

/** Adult beginner spelling and listening practice; no microphone grading or proficiency score. */
export function AlphabetPractice() {
  const id = useId();
  const [index, setIndex] = useState(0);
  const [round, setRound] = useState(0);
  const [answer, setAnswer] = useState<string | null>(null);
  const current = DUTCH_ALPHABET[index];
  const question = letterQuestion(round);
  return <section className="alphabet-practice card" aria-labelledby={`${id}-title`} data-testid="alphabet-practice">
    <div className="section-heading"><div><p className="eyebrow">PRE-A1 · EEN GOEDE START</p><h2 id={`${id}-title`}><LearningText text={{ nl: "Letters en klanken", en: "Letters and sounds", fa: "حروف و آواها" }}/></h2></div><span className="label warn"><LearningText text={{ nl: "Nog niet nagekeken", en: "Not yet reviewed", fa: "هنوز بازبینی نشده" }}/></span></div>
    <p><LearningText text={{ nl: "Een letter heeft een naam. In een woord kan die letter anders klinken. Luister naar de letter en daarna naar het hele woord.", en: "A letter has a name. Inside a word it can sound different. Listen to the letter name and then to the whole word.", fa: "هر حرف نامی دارد. در یک واژه ممکن است صدای دیگری داشته باشد. ابتدا نام حرف و سپس واژهٔ کامل را بشنو." }}/></p>
    <div className="alphabet-picker" role="group" aria-label="Kies een letter">
      {DUTCH_ALPHABET.map((letter, position) => <button type="button" key={letter.letter} lang="nl" aria-pressed={position === index} onClick={() => setIndex(position)}>{letter.letter}<span aria-hidden="true"> {letter.letter.toLowerCase()}</span></button>)}
    </div>
    <div className="alphabet-focus" key={current.letter}>
      <div className="alphabet-glyph" aria-hidden="true">{current.letter}<span>{current.letter.toLowerCase()}</span></div>
      <div><h3><LearningText text={{ nl: "De naam van de letter", en: "The letter name", fa: "نام حرف" }}/></h3><p className="alphabet-spoken-name" lang="nl">{current.name} <PhraseAudio text={current.speech} label={`De naam van de letter ${current.letter}`}/></p><p><LearningText text={{ nl: "Een woord met deze letter", en: "A word containing this letter", fa: "واژه‌ای شامل این حرف" }}/></p><p className="phrase-line"><LearningText text={current.example}/><PhraseAudio text={current.example.nl}/></p></div>
    </div>
    <div className="alphabet-note"><LearningText text={{ nl: "Bijvoorbeeld: de naam van A klinkt als aa. Luister hoe de a in kat verschilt van de aa in maan. Y heet ypsilon of Griekse ij; ij is een lettercombinatie.", en: "For example, the name of A sounds like aa. Listen to the difference between a in kat and aa in maan. Y is called ypsilon or Griekse ij; ij is a letter combination.", fa: "برای نمونه، نام A مانند aa است. تفاوت a در kat و aa در maan را بشنو. نام Y، ypsilon یا Griekse ij است؛ ij ترکیب دو حرف است." }}/><div className="alphabet-contrast"><span lang="nl">kat <PhraseAudio text="kat"/></span><span lang="nl">maan <PhraseAudio text="maan"/></span></div></div>
    <section className="alphabet-quiz" aria-labelledby={`${id}-quiz-title`}>
      <h3 id={`${id}-quiz-title`}><LearningText text={{ nl: "Luister en kies de letter", en: "Listen and choose the letter", fa: "بشنو و حرف را انتخاب کن" }}/></h3>
      <p><LearningText text={{ nl: "Druk op de luidspreker. Welke letternaam hoor je?", en: "Press the speaker. Which letter name do you hear?", fa: "دکمهٔ صدا را بزن. نام کدام حرف را می‌شنوی؟" }}/></p>
      <div className="alphabet-question-audio"><PhraseAudio key={round} text={question.target.speech} label="Luister naar de letter"/><span><LearningText text={{ nl: "Luister opnieuw zo vaak als je wilt.", en: "Replay as often as you like.", fa: "هر چند بار که می‌خواهی دوباره بشنو." }}/></span></div>
      <div className="alphabet-options" role="group" aria-label="Welke letter hoor je?">{question.options.map(option => <button type="button" key={option.letter} disabled={answer !== null} className={answer === option.letter ? "selected" : ""} onClick={() => setAnswer(option.letter)}>{option.letter}</button>)}</div>
      {answer && <div className="alphabet-answer" role="status"><p><LearningText text={answer === question.target.letter ? { nl: `Juist: ${question.target.letter} heet ${question.target.name}.`, en: `Correct: ${question.target.letter} is called ${question.target.name}.`, fa: `درست است: نام ${question.target.letter}، ${question.target.name} است.` } : { nl: `Je hoorde ${question.target.name}: de letter ${question.target.letter}. Luister nog eens en vergelijk.`, en: `You heard ${question.target.name}: the letter ${question.target.letter}. Listen again and compare.`, fa: `صدای ${question.target.name} را شنیدی: حرف ${question.target.letter}. دوباره بشنو و مقایسه کن.` }}/></p><button type="button" className="button secondary" onClick={() => { setRound(value => value + 1); setAnswer(null); }}><LearningText text={{ nl: "Volgende letter", en: "Next letter", fa: "حرف بعدی" }}/></button></div>}
    </section>
    <details className="alphabet-pairs"><summary><LearningText text={{ nl: "Letters die samenwerken", en: "Letters that work together", fa: "حروفی که با هم می‌آیند" }}/></summary><p><LearningText text={{ nl: "Luister naar het hele woord. Deze combinaties helpen je woorden lezen; ze zijn geen extra letters van het alfabet. Ei en ij kunnen hetzelfde klinken, net als au en ou. Leer daarom ook de spelling van elk woord.", en: "Listen to the whole word. These combinations help you read; they are not extra alphabet letters. Ei and ij can sound the same, as can au and ou. Learn the spelling of each word too.", fa: "واژهٔ کامل را بشنو. این ترکیب‌ها به خواندن کمک می‌کنند و حروف اضافی الفبا نیستند. ei و ij می‌توانند هم‌صدا باشند، همان‌طور که au و ou. پس املای هر واژه را هم یاد بگیر." }}/></p><div className="alphabet-pair-grid">{DUTCH_LETTER_PAIRS.map(pair => <div key={pair.letters}><strong lang="nl">{pair.letters}</strong><LearningText text={pair.example}/><PhraseAudio text={pair.example.nl}/></div>)}</div></details>
    <p className="course-note"><LearningText text={{ nl: "Synthetische luistervoorbeelden. Zeg de letters en woorden daarna zelf. Dit is oefening, geen beoordeling van je uitspraak.", en: "Synthetic listening examples. Say the letters and words yourself afterwards. This is practice, not a pronunciation assessment.", fa: "نمونه‌های شنیداری با صدای مصنوعی هستند. سپس حروف و واژه‌ها را خودت بگو. این تمرین است، نه ارزیابی تلفظ." }}/></p>
  </section>;
}
