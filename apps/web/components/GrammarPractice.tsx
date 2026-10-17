"use client";

import { useState } from "react";
import { grammarCopy as copy } from "@/lib/copy/grammar";
import { fill } from "@/lib/ui-copy";
import { CurriculumQuestions } from "@/components/CurriculumControls";
import { LearningText } from "@/components/LanguageSupport";
import { PhraseAudio } from "@/components/PhraseAudio";
import { SpokenText } from "@/components/SpokenPassage";
import type { CurriculumStage } from "@/lib/client/curriculum";
import type { Skill } from "@/lib/types";

const skills: Skill[] = ["reading", "listening", "speaking", "writing"];

export function GrammarPractice({
  topics,
  answers,
  onAnswer,
  checked,
  onCheck,
  onPractice,
}: {
  topics: CurriculumStage["grammar"];
  answers: Record<string, number>;
  onAnswer: (id: string, index: number) => void;
  checked: Record<string, boolean>;
  onCheck: (id: string) => void;
  onPractice: (skill: Skill) => void;
}) {
  const [selected, setSelected] = useState(
    () => topics.find((t) => t.id.startsWith("practice-"))?.id ?? topics[0]?.id,
  );
  const [listenFirst, setListenFirst] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const index = Math.max(
    0,
    topics.findIndex((t) => t.id === selected),
  );
  const topic = topics[index];
  if (!topic) return null;
  const total = topics.reduce((sum, t) => sum + t.practice.length, 0);
  function select(id: string) {
    setSelected(id);
    setRevealed(false);
  }
  return (
    <section className="grammar-practice" aria-label={copy.region.nl}>
      <p className="eyebrow">
        {total} <LearningText text={copy.count} />
      </p>
      <label className="field-label" htmlFor="grammar-topic">
        <LearningText text={copy.choose} />
      </label>
      <select id="grammar-topic" value={topic.id} onChange={(e) => select(e.target.value)}>
        {topics.map((t) => (
          <option key={t.id} value={t.id}>
            {t.title.nl} · {t.practice.length}
          </option>
        ))}
      </select>
      <section className="grammar-card" aria-labelledby="grammar-round-title">
        <h3 id="grammar-round-title" aria-live="polite">
          <LearningText text={topic.title} />
        </h3>
        <p>
          <LearningText text={topic.explanation} />
        </p>
        <label className="answer-option">
          <input
            type="checkbox"
            checked={listenFirst}
            onChange={(e) => {
              setListenFirst(e.target.checked);
              setRevealed(false);
            }}
          />
          <LearningText text={copy.listen} />
        </label>
        <div className="grammar-examples">
          {topic.examples.map((example, n) => (
            <p key={n}>
              {listenFirst && !revealed ? (
                <PhraseAudio text={example.nl} label={fill(copy.audioExample, { n: n + 1 }).nl} />
              ) : (
                <SpokenText text={example} />
              )}
            </p>
          ))}
          {listenFirst && !revealed && (
            <button className="button secondary" onClick={() => setRevealed(true)}>
              <LearningText text={copy.reveal} />
            </button>
          )}
        </div>
        <CurriculumQuestions
          questions={topic.practice}
          answers={answers}
          onAnswer={onAnswer}
          checked={!!checked[topic.id]}
        />
        <button
          className="button secondary"
          disabled={!topic.practice.every((q) => answers[q.id] !== undefined)}
          onClick={() => onCheck(topic.id)}
        >
          <LearningText text={copy.check} />
        </button>
      </section>
      <div className="action-row">
        <button
          className="button secondary"
          disabled={index === 0}
          onClick={() => select(topics[index - 1].id)}
        >
          <LearningText text={copy.previous} />
        </button>
        <button
          className="button secondary"
          disabled={index === topics.length - 1}
          onClick={() => select(topics[index + 1].id)}
        >
          <LearningText text={copy.next} />
        </button>
      </div>
      <section className="grammar-card">
        <h3>
          <LearningText text={copy.transfer} />
        </h3>
        <p>
          <LearningText text={copy.invitation} />
        </p>
        <div className="action-row">
          {skills.map((skill) => (
            <button key={skill} className="button secondary" onClick={() => onPractice(skill)}>
              <LearningText text={copy[skill]} />
            </button>
          ))}
        </div>
      </section>
    </section>
  );
}
