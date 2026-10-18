"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { GrammarPractice } from "@/components/GrammarPractice";
import { LearningText } from "@/components/LanguageSupport";
import { apiJson } from "@/lib/client/api";
import { friendlyError, type CurriculumStage } from "@/lib/client/curriculum";
import { studyHref } from "@/lib/client/study";
import { studyCopy } from "@/lib/copy/study";
import { StudyError } from "./StudyShared";

/** Grammar remains a contextual tool. Answers live only in this mounted panel. */
export function StudyGrammar({ stageId }: { stageId: string }) {
  const router = useRouter();
  const [loaded, setLoaded] = useState<{ stage: string; value: CurriculumStage } | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    apiJson<CurriculumStage>(`curriculum/${stageId}`, { signal: controller.signal })
      .then((value) => {
        if (controller.signal.aborted) return;
        setLoaded({ stage: stageId, value });
        setAnswers({});
        setChecked({});
        setError("");
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(friendlyError(cause, "load"));
      });
    return () => controller.abort();
  }, [stageId, retry]);

  if (error) return <StudyError message={error} retry={() => setRetry((value) => value + 1)} />;
  if (!loaded || loaded.stage !== stageId)
    return (
      <p role="status">
        <LearningText text={studyCopy.loadingLesson} />
      </p>
    );
  return (
    <GrammarPractice
      key={stageId}
      topics={loaded.value.grammar}
      answers={answers}
      onAnswer={(id, index) => setAnswers((value) => ({ ...value, [id]: index }))}
      checked={checked}
      onCheck={(id) => setChecked((value) => ({ ...value, [id]: true }))}
      onPractice={(skill) => router.push(studyHref(stageId, skill))}
    />
  );
}
