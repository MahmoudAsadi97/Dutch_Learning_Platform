"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AlphabetPractice } from "@/components/AlphabetPractice";
import { LearningText } from "@/components/LanguageSupport";
import { VocabularyRecall } from "@/components/VocabularyRecall";
import { Button } from "@/components/ui/Button";
import { Notice } from "@/components/ui/Notice";
import { Skeleton, SkeletonPanel } from "@/components/ui/Skeleton";
import { UiText } from "@/components/ui/UiText";
import { library, type LibraryWord } from "@/lib/client/library";
import { words } from "@/lib/client/stories";
import { fill, uiCopy } from "@/lib/ui-copy";

const STARTER_COUNT = 8;

/** The first words of the chosen stage; the learner ticks the ones to keep, nothing is kept unasked. */
function StarterWords({ stage }: { stage: string }) {
  const list = useQuery({
    queryKey: ["library", "words", stage, STARTER_COUNT],
    queryFn: ({ signal }) => library.words(stage, STARTER_COUNT, signal),
    staleTime: Infinity,
  });
  const [chosen, setChosen] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(0);
  const [failed, setFailed] = useState(false);

  if (list.isError) {
    return (
      <Notice tone="warning" role="status">
        <UiText text={uiCopy.welcome.wordsUnavailable} tier="always" />
      </Notice>
    );
  }
  if (!list.data) {
    return (
      <SkeletonPanel label="Woorden laden…">
        <Skeleton lines={4} />
      </SkeletonPanel>
    );
  }
  const items = list.data.items;
  const toggle = (id: string) =>
    setChosen((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  async function keep() {
    const picked: LibraryWord[] = items.filter((item) => chosen.has(item.id));
    setSaving(true);
    setFailed(false);
    try {
      for (const item of picked) await words.saveLibrary(item);
      setSaved(picked.length);
      setChosen(new Set());
    } catch {
      setFailed(true);
    } finally {
      setSaving(false);
    }
  }
  return (
    <div className="starter-words" data-testid="starter-words">
      <p>
        <UiText text={uiCopy.welcome.wordsIntro} tier="always" />
      </p>
      <ul className="starter-list">
        {items.map((item) => (
          <li key={item.id}>
            <label className="starter-word">
              <input type="checkbox" checked={chosen.has(item.id)} onChange={() => toggle(item.id)} />
              <span>
                <strong lang="nl">{item.term}</strong>
                <LearningText text={item.meaning} supportOnly />
              </span>
            </label>
          </li>
        ))}
      </ul>
      <div className="welcome-actions">
        <Button
          variant="secondary"
          icon="star"
          disabled={chosen.size === 0 || saving}
          onClick={() => void keep()}
        >
          <UiText text={fill(uiCopy.welcome.wordsSave, { count: chosen.size })} inline />
        </Button>
        {saved > 0 && (
          <p className="muted" role="status">
            <UiText text={fill(uiCopy.welcome.wordsSaved, { count: saved })} tier="always" inline />
          </p>
        )}
      </div>
      {failed && (
        <Notice tone="warning" role="alert">
          <UiText text={uiCopy.welcome.saveFailed} tier="always" />
        </Notice>
      )}
      <h3 className="starter-practise">
        <UiText text={uiCopy.welcome.wordsPractise} tier="always" />
      </h3>
      <VocabularyRecall words={items} />
    </div>
  );
}

/** Something real to do while episode one is written: the alphabet at pre-A1, first words otherwise. */
export function FirstActivity({ stage }: { stage: string }) {
  const alphabet = stage === "pre-a1";
  return (
    <section className="first-activity" aria-labelledby="first-activity-title">
      <h2 id="first-activity-title">
        <UiText text={alphabet ? uiCopy.welcome.alphabetTitle : uiCopy.welcome.wordsTitle} tier="always" />
      </h2>
      {alphabet ? <AlphabetPractice /> : <StarterWords stage={stage} />}
    </section>
  );
}
