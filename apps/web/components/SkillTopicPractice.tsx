"use client";

import { useEffect, useId, useRef, useState } from "react";
import { CurriculumRecorder, countWords } from "@/components/CurriculumControls";
import { ExerciseSession } from "@/components/exercise/ExerciseSession";
import { LearningText, useLanguageSupport } from "@/components/LanguageSupport";
import { SpokenPassage } from "@/components/SpokenPassage";
import { PhraseAudio } from "@/components/PhraseAudio";
import { ConversationTopicChoices, TopicConversation } from "@/components/TopicConversation";
import { WritingCoach } from "@/components/WritingCoach";
import { Icon, type IconName } from "@/components/Icon";
import { apiJson, newRequestId } from "@/lib/client/api";
import { friendlyError, skillNames } from "@/lib/client/curriculum";
import type { Summary } from "@/lib/client/exercises";
import type { TopicDetail, TopicFeedback, TopicPage } from "@/lib/client/topics";
import type { Skill } from "@/lib/types";
import { storageKeys } from "@/lib/client/storage";
import { playTone } from "@/lib/client/tones";
import { topicsCopy } from "@/lib/copy/topics";
import { stageLabel } from "@/lib/domain/registry";
import { fill, type Copy } from "@/lib/ui-copy";
import { Button, ProgressBar, UiText } from "@/components/ui";

const icons: Record<Skill, IconName> = {
  reading: "book",
  listening: "headphones",
  speaking: "mic",
  writing: "pen",
};
type Props = {
  stageId: string;
  skill: Skill;
  learnerKey: string;
  initialTopic?: string;
  maxSeconds?: number;
  onActivityChange: (busy: boolean) => void;
  onCompleted: () => void;
};

/** Only one page of summaries is fetched. A task is loaded after a deliberate choice. */
export function SkillTopicPractice(props: Props) {
  const { stageId, skill, learnerKey, onActivityChange } = props;
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("all");
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState(props.initialTopic ?? "");
  // how the topic was reached: from the list (its start card), or sent to its task (a link, a conversation)
  const [entry, setEntry] = useState<"list" | "task">(props.initialTopic ? "task" : "list");
  const [result, setResult] = useState<{ key: string; page: TopicPage } | null>(null);
  const [failed, setFailed] = useState<{ key: string; message: string } | null>(null);
  const { showEnglish, showPersian } = useLanguageSupport();
  const focusRef = useRef<HTMLHeadingElement>(null);
  const key = JSON.stringify([stageId, learnerKey, skill, query, category, status, offset, revision]);
  const data = result?.key === key ? result.page : null;
  const metadata =
    result?.page.stage_id === stageId && result.page.skill === skill && result.page.learner_key === learnerKey
      ? result.page
      : null;
  useEffect(() => {
    if (selected) return;
    const controller = new AbortController();
    const timer = window.setTimeout(
      () => {
        const params = new URLSearchParams({
          skill,
          q: query,
          category,
          status,
          offset: String(offset),
          limit: "12",
        });
        apiJson<TopicPage>(`curriculum/${stageId}/topics?${params}`, { signal: controller.signal })
          .then((page) => {
            if (!controller.signal.aborted) setResult({ key, page });
          })
          .catch((cause) => {
            if (!controller.signal.aborted)
              setFailed({
                key,
                message: friendlyError(cause, "load"),
              });
          });
      },
      query ? 180 : 0,
    );
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [key, selected, stageId, skill, query, category, status, offset]);

  if (selected)
    return (
      <TopicReader
        key={`${learnerKey}.${stageId}.${skill}.${selected}`}
        {...props}
        topicId={selected}
        entry={entry}
        onBack={() => {
          setSelected("");
          setRevision((value) => value + 1);
          onActivityChange(false);
          window.requestAnimationFrame(() => focusRef.current?.focus());
        }}
      />
    );

  return (
    <section
      className="skill-topic-library"
      aria-label={`Onderwerpen voor ${skillNames[skill].toLowerCase()}`}
    >
      <div className="topic-library-intro">
        <div>
          <p className="eyebrow">KIES · OEFEN · GROEI</p>
          <h3 ref={focusRef} tabIndex={-1}>
            {metadata
              ? `${metadata.total_topics} onderwerpen voor ${skillNames[skill].toLowerCase()}`
              : `Onderwerpen voor ${skillNames[skill].toLowerCase()}`}
          </h3>
          <p>
            <LearningText
              text={{
                nl: "Kies een situatie die bij je dag past. Elk onderwerp heeft een eigen opdracht. Je kunt vrij kiezen en zo vaak oefenen als je wilt.",
                en: "Choose a situation from everyday life. Each topic has its own task. Pick freely and practise as often as you like.",
                fa: "موقعیتی متناسب با روزت انتخاب کن. هر موضوع تمرین خودش را دارد. آزادانه انتخاب کن و هرقدر می‌خواهی تمرین کن.",
              }}
            />
          </p>
        </div>
        {metadata && (
          <div className="topic-progress-summary">
            <span className="topic-progress-number">
              {metadata.completed_count}
              <span> / {metadata.total_topics}</span>
            </span>
            <span>onderwerpen geoefend</span>
            <ProgressBar
              size="thin"
              value={metadata.completed_count}
              max={metadata.total_topics || 1}
              label={`Voortgang ${skillNames[skill].toLowerCase()}`}
            />
            <span className="small-text">Alleen deze vaardigheid</span>
          </div>
        )}
      </div>
      {skill === "speaking" && (
        <ConversationTopicChoices
          stageId={stageId}
          learnerKey={learnerKey}
          onChoose={(id) => {
            setEntry("task");
            setSelected(id);
          }}
        />
      )}
      <div className="topic-filters">
        <div>
          <label htmlFor="practice-topic-search">Zoek een situatie</label>
          <input
            id="practice-topic-search"
            type="search"
            maxLength={120}
            value={query}
            placeholder="Bijvoorbeeld: trein, eten, werk…"
            onChange={(event) => {
              setQuery(event.target.value);
              setOffset(0);
            }}
          />
        </div>
        <div>
          <label htmlFor="practice-topic-category">Thema</label>
          <select
            id="practice-topic-category"
            value={category}
            onChange={(event) => {
              setCategory(event.target.value);
              setOffset(0);
            }}
          >
            <option value="">Alle thema’s</option>
            {metadata?.categories.map((item) => (
              <option key={item.nl} value={item.nl}>
                {[item.nl, showEnglish && item.en, showPersian && item.fa].filter(Boolean).join(" · ")}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="practice-topic-status">Oefenstatus</label>
          <select
            id="practice-topic-status"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setOffset(0);
            }}
          >
            <option value="all">Alles</option>
            <option value="not_started">Nog niet begonnen</option>
            <option value="completed">Geoefend</option>
          </select>
        </div>
      </div>
      {failed?.key === key ? (
        <div className="error" role="alert">
          <p>{failed.message}</p>
          <button className="button secondary" onClick={() => setRevision((value) => value + 1)}>
            Opnieuw proberen
          </button>
        </div>
      ) : !data ? (
        <p role="status">Onderwerpen laden…</p>
      ) : (
        <>
          {!data.total && (
            <div className="topic-empty">
              <Icon name="book" size={32} />
              <h4>Geen onderwerpen gevonden</h4>
              <p>Probeer een ander zoekwoord of toon alle thema’s.</p>
              <button
                className="button secondary"
                onClick={() => {
                  setQuery("");
                  setCategory("");
                  setStatus("all");
                  setOffset(0);
                }}
              >
                Toon alle onderwerpen
              </button>
            </div>
          )}
          <div className="topic-grid">
            {data.items.map((topic, index) => (
              <article className={`topic-tile ${topic.completed ? "is-complete" : ""}`} key={topic.id}>
                <div className="topic-tile-meta">
                  <span className="topic-index">{String(offset + index + 1).padStart(2, "0")}</span>
                  <span className="small-text">
                    {topic.completed ? "Geoefend" : topic.attempted ? "Opnieuw proberen" : "Nog ontdekken"}
                  </span>
                </div>
                <span className="eyebrow">{topic.category.nl}</span>
                {topic.review_of && (
                  <span className="quiet-badge topic-review">
                    <UiText
                      text={fill(topicsCopy.reviewOf, { stage: stageLabel(topic.review_of.stage_id) })}
                      inline
                    />
                  </span>
                )}
                <h4>
                  <LearningText text={topic.title} />
                </h4>
                <button
                  className="button secondary"
                  aria-label={`Oefen ${topic.title.nl}`}
                  onClick={() => {
                    setEntry("list");
                    setSelected(topic.id);
                  }}
                >
                  <Icon name={icons[skill]} size={17} />
                  {topic.completed ? "Oefen opnieuw" : "Begin met oefenen"}
                  <Icon name="arrow" size={17} />
                </button>
              </article>
            ))}
          </div>
          <nav className="library-pagination" aria-label="Pagina’s met oefenonderwerpen">
            <button
              className="button secondary"
              disabled={offset === 0}
              onClick={() => setOffset((value) => Math.max(0, value - 12))}
            >
              Vorige
            </button>
            <span role="status">
              {data.total
                ? `${offset + 1}–${Math.min(offset + 12, data.total)} van ${data.total}`
                : "Geen resultaten"}
            </span>
            <button
              className="button secondary"
              disabled={offset + 12 >= data.total}
              onClick={() => setOffset((value) => value + 12)}
            >
              Volgende
            </button>
          </nav>
        </>
      )}
    </section>
  );
}

type Draft = { text: string };
function loadDraft(key: string): Draft {
  const empty = { text: "" };
  const raw = sessionStorage.getItem(key);
  if (!raw) return empty;
  try {
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== "object") return empty;
    const draft = value as Partial<Draft>;
    // a draft saved before the questions moved into the session may also hold answers; only the text matters
    return { text: typeof draft.text === "string" ? draft.text.slice(0, 12000) : "" };
  } catch {
    return empty;
  }
}

/** Where the learner is in a topic: its start card, the practice session, or the open task (speaking, writing). */
type Phase = "start" | "session" | "task";

const startSteps: Record<Skill, Copy[]> = {
  reading: [topicsCopy.stepRead, topicsCopy.stepQuestionsRead, topicsCopy.stepRevealRead],
  listening: [topicsCopy.stepListen, topicsCopy.stepQuestionsListen, topicsCopy.stepRevealListen],
  speaking: [topicsCopy.stepWarmUp, topicsCopy.stepTask],
  writing: [topicsCopy.stepWarmUp, topicsCopy.stepTask],
};

/**
 * One topic. Reading and listening open on a start card, then run as a practice session (the passage, then the
 * questions one at a time; the server decides what counts). Speaking and writing open on a start card with a
 * warm-up on the topic's words, or go straight to the open task, whose submission completes the topic; a learner
 * sent to the task (a coach's link, a conversation, a draft already begun) arrives at it directly.
 */
function TopicReader({
  stageId,
  skill,
  learnerKey,
  maxSeconds,
  topicId,
  entry,
  onActivityChange,
  onCompleted,
  onBack,
}: Props & { topicId: string; entry: "list" | "task"; onBack: () => void }) {
  const receptive = skill === "reading" || skill === "listening";
  const draftKey = storageKeys.topicDraft(learnerKey, stageId, skill, topicId);
  const [initialDraft] = useState(() => {
    try {
      return { draft: loadDraft(draftKey), failed: false };
    } catch {
      return { draft: { text: "" } as Draft, failed: true };
    }
  });
  const [phase, setPhase] = useState<Phase>(() =>
    receptive ? "start" : entry === "task" || initialDraft.draft.text.trim() ? "task" : "start",
  );
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
  const [sessionBusy, setSessionBusy] = useState(false);
  const submitKey = useRef<{ fingerprint: string; key: string } | null>(null);
  const [audioId, setAudioId] = useState("");
  const [feedback, setFeedback] = useState<TopicFeedback | null>(null);
  const [error, setError] = useState("");
  const activityRef = useRef(onActivityChange);
  const completedRef = useRef(onCompleted);
  const submitRef = useRef<AbortController | null>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const taskRef = useRef<HTMLHeadingElement>(null);
  const focusTitle = useRef(false);
  const focusTask = useRef(false);
  const startId = useId();
  const busy = submitBusy || recordingBusy || coachBusy || conversationBusy || sessionBusy;
  const endpoint = `curriculum/${stageId}/topics/${encodeURIComponent(topicId)}`;
  useEffect(() => {
    activityRef.current = onActivityChange;
    completedRef.current = onCompleted;
  });
  useEffect(() => {
    activityRef.current(busy);
  }, [busy]);
  useEffect(
    () => () => {
      submitRef.current?.abort();
      activityRef.current(false);
    },
    [],
  );
  useEffect(() => {
    const controller = new AbortController();
    apiJson<TopicDetail>(`${endpoint}?skill=${skill}`, { signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted) {
          focusTitle.current = true;
          setTopic(value);
          setLoadError("");
        }
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setLoadError(friendlyError(cause, "load"));
      });
    return () => controller.abort();
  }, [endpoint, skill, retry]);
  // Keyboard focus moves to the topic title once the loaded topic is on the page. An animation frame
  // scheduled from the fetch callback could run before React had committed the heading.
  useEffect(() => {
    if (focusTitle.current && titleRef.current) {
      focusTitle.current = false;
      titleRef.current.focus();
    }
  }, [topic]);
  // the task heading takes focus when the learner moves on to the task by a button
  useEffect(() => {
    if (focusTask.current && phase === "task" && taskRef.current) {
      focusTask.current = false;
      taskRef.current.focus();
    }
  }, [phase]);
  function go(next: Phase) {
    setSessionBusy(false);
    focusTask.current = next === "task";
    setPhase(next);
  }
  /** The session's summary: only what the server counted moves the topic on (never a retry or a warm-up). */
  function finished(summary: Summary) {
    const completion = summary.completion;
    if (!completion?.counted) return;
    setTopic(
      (current) =>
        current && {
          ...current,
          progress: { attempted: true, completed: current.progress.completed || completion.completed },
        },
    );
    if (completion.completed) completedRef.current();
  }
  function updateDraft(next: Draft) {
    setDraft(next);
    setFeedback(null);
    setError("");
    try {
      sessionStorage.setItem(draftKey, JSON.stringify(next));
      setStorageError(false);
    } catch {
      setStorageError(true);
    }
  }
  async function submit() {
    if (!topic || busy || submitRef.current || receptive) return;
    const controller = new AbortController();
    submitRef.current = controller;
    setSubmitBusy(true);
    setError("");
    try {
      const payload = {
        skill,
        ...(skill === "writing" ? { text: draft.text } : {}),
        ...(skill === "speaking" ? { audio_asset_id: audioId } : {}),
      };
      const fingerprint = JSON.stringify(payload);
      if (submitKey.current?.fingerprint !== fingerprint)
        submitKey.current = { fingerprint, key: newRequestId() };
      const response = await apiJson<TopicFeedback>(`${endpoint}/practice`, {
        method: "POST",
        signal: controller.signal,
        body: { ...payload, request_id: submitKey.current.key },
      });
      if (!controller.signal.aborted) {
        submitKey.current = null;
        setFeedback(response);
        playTone(response.passed ? "correct" : "almost");
        setTopic(
          (current) =>
            current && {
              ...current,
              progress: { attempted: true, completed: current.progress.completed || response.completed },
            },
        );
        if (response.completed) completedRef.current();
      }
    } catch (cause) {
      if (!controller.signal.aborted) setError(friendlyError(cause));
    } finally {
      if (submitRef.current === controller) {
        submitRef.current = null;
        setSubmitBusy(false);
      }
    }
  }
  const task = topic?.activity;
  const words = countWords(draft.text);
  const ready =
    topic &&
    (skill === "speaking" ? !!audioId : words >= (task?.min_words ?? 1) && words <= (task?.max_words ?? 1));
  const review = topic?.review_of ? stageLabel(topic.review_of.stage_id) : null;
  return (
    <section className="topic-reader" aria-label="Oefenen met een onderwerp">
      <button className="back-link" disabled={busy} onClick={onBack}>
        ← Alle onderwerpen
      </button>
      {!topic ? (
        loadError ? (
          <div className="error" role="alert">
            <p>{loadError}</p>
            <button className="button secondary" onClick={() => setRetry((value) => value + 1)}>
              Opnieuw proberen
            </button>
          </div>
        ) : (
          <p role="status">Je opdracht laden…</p>
        )
      ) : (
        <>
          <header className="topic-detail-heading">
            <div className="topic-detail-kicker">
              <span className="eyebrow">{topic.category.nl}</span>
              {review && (
                <span className="quiet-badge topic-review">
                  <UiText text={fill(topicsCopy.reviewOf, { stage: review })} inline />
                </span>
              )}
              {topic.progress.completed && (
                <span className="practice-complete">
                  <Icon name="check" size={16} />
                  Al geoefend
                </span>
              )}
            </div>
            <h3 tabIndex={-1} ref={titleRef}>
              <LearningText text={topic.title} />
            </h3>
            <p className="topic-language-focus">
              <LearningText text={topic.language_focus} />
            </p>
          </header>
          {phase !== "session" && (
            <details className="topic-goals">
              <summary>Wat oefen je hier?</summary>
              <ul>
                {topic.objectives.map((goal, index) => (
                  <li key={index}>
                    <LearningText text={goal} />
                  </li>
                ))}
              </ul>
            </details>
          )}
          {skill === "speaking" && phase !== "session" && (
            <TopicConversation
              stageId={stageId}
              topicId={topicId}
              learnerKey={learnerKey}
              disabled={submitBusy || recordingBusy || coachBusy}
              onActivityChange={setConversationBusy}
              onOpenChange={setConversationOpen}
            />
          )}
          {!conversationOpen && (
            <>
              {phase === "start" && (
                <section className="topic-start" aria-labelledby={startId}>
                  <h4 id={startId}>
                    <UiText text={topicsCopy.startTitle} />
                  </h4>
                  {review && (
                    <p>
                      <UiText text={fill(topicsCopy.reviewLead, { stage: review })} tier="guide" />
                    </p>
                  )}
                  {topic.progress.completed && (
                    <p>
                      <UiText text={topicsCopy.alreadyDone} tier="guide" />
                    </p>
                  )}
                  <ol className="topic-steps">
                    {startSteps[skill].map((step) => (
                      <li key={step.nl}>
                        <UiText text={step} tier="guide" />
                      </li>
                    ))}
                  </ol>
                  {receptive && (
                    <p className="small-text">
                      <UiText text={topicsCopy.countsReceptive} tier="guide" />
                    </p>
                  )}
                  <div className="topic-start-actions">
                    {receptive ? (
                      <Button icon={icons[skill]} onClick={() => go("session")}>
                        <UiText
                          text={skill === "reading" ? topicsCopy.beginReading : topicsCopy.beginListening}
                          inline
                        />
                      </Button>
                    ) : (
                      <>
                        <Button icon="sparkles" onClick={() => go("session")}>
                          <UiText text={topicsCopy.warmUp} inline />
                        </Button>
                        <Button variant="secondary" icon="arrow" iconEnd onClick={() => go("task")}>
                          <UiText text={topicsCopy.skipToTask} inline />
                        </Button>
                      </>
                    )}
                  </div>
                </section>
              )}
              {phase === "session" && (
                <>
                  {!receptive && (
                    <div className="topic-start-actions">
                      <Button
                        variant="secondary"
                        size="small"
                        icon="arrow"
                        iconEnd
                        disabled={busy}
                        onClick={() => go("task")}
                      >
                        <UiText text={topicsCopy.skipToTask} inline />
                      </Button>
                    </div>
                  )}
                  <ExerciseSession
                    source="topic"
                    stageId={stageId}
                    topicId={topicId}
                    skill={skill}
                    headingLevel={4}
                    embedded={{
                      label: receptive ? topicsCopy.toTopics : topicsCopy.toTask,
                      onExit: receptive ? onBack : () => go("task"),
                    }}
                    onActivityChange={setSessionBusy}
                    onFinished={finished}
                  />
                </>
              )}
              {phase === "task" && (
                <>
                  <h4 className="topic-task-heading" tabIndex={-1} ref={taskRef}>
                    <UiText text={topicsCopy.taskTitle} />
                  </h4>
                  {!audioId && !busy && (
                    <Button variant="ghost" size="small" icon="sparkles" onClick={() => go("session")}>
                      <UiText text={topicsCopy.warmUp} inline />
                    </Button>
                  )}
                  {topic.context && (
                    <details className="topic-scene" open>
                      <summary>De situatie</summary>
                      <p className="small-text">
                        Gebruik deze informatie voor jouw antwoord. Je hoeft geen andere oefening te openen.
                      </p>
                      <h4>Wat je leest</h4>
                      <SpokenPassage text={topic.context.reading} />
                      <h4>Het gesproken bericht</h4>
                      <SpokenPassage text={topic.context.listening} />
                    </details>
                  )}
                  {task?.prompt && (
                    <>
                      <div className="productive-task">
                        <p>
                          <LearningText text={task.prompt} />
                          <PhraseAudio text={task.prompt.nl} disabled={busy} />
                        </p>
                        <h4>Dit probeer je te doen</h4>
                        <ul className="task-criteria">
                          {task.criteria.map((criterion, index) => (
                            <li key={index}>
                              <LearningText text={criterion} />
                            </li>
                          ))}
                        </ul>
                      </div>
                      {skill === "speaking" ? (
                        <CurriculumRecorder
                          onReady={(asset) => {
                            setAudioId(asset);
                            setFeedback(null);
                          }}
                          onActivityChange={setRecordingBusy}
                          disabled={submitBusy}
                          minWords={task.min_words}
                          maxWords={task.max_words}
                          maxSeconds={topic.policy?.recording_max_seconds ?? maxSeconds}
                        />
                      ) : (
                        <>
                          <div className="writing-workspace">
                            <label htmlFor="topic-writing">Jouw tekst bij dit onderwerp</label>
                            <textarea
                              id="topic-writing"
                              value={draft.text}
                              disabled={submitBusy}
                              rows={9}
                              maxLength={12000}
                              placeholder="Schrijf hier in het Nederlands…"
                              onChange={(event) => updateDraft({ ...draft, text: event.target.value })}
                            />
                            <div className="writing-meta">
                              <span>
                                {words} woorden · doel: {task.min_words}–{task.max_words}
                              </span>
                              <span>Concept per onderwerp in dit tabblad</span>
                            </div>
                          </div>
                          <WritingCoach
                            stageId={stageId}
                            text={draft.text}
                            disabled={submitBusy}
                            onActivityChange={setCoachBusy}
                            onApply={(text) => updateDraft({ ...draft, text })}
                          />
                        </>
                      )}
                      {task.sample && (
                        <details className="sample-help">
                          <summary>
                            {task.sample_is_excerpt
                              ? "Bekijk een voorbeeldbegin"
                              : "Bekijk een voorbeeld als je vastzit"}
                          </summary>
                          {task.sample_is_excerpt && (
                            <p>
                              Dit is alleen een begin. Werk je eigen antwoord verder uit tot de gevraagde
                              lengte.
                            </p>
                          )}
                          <p className="story-copy">
                            <LearningText text={task.sample} />
                            <PhraseAudio text={task.sample.nl} disabled={busy} />
                          </p>
                        </details>
                      )}
                    </>
                  )}
                </>
              )}
              {phase !== "session" && (
                <details className="topic-vocabulary">
                  <summary>Woorden voor deze situatie</summary>
                  <div>
                    {topic.vocabulary.map((word) => (
                      <article key={word.id}>
                        <div className="word-card-heading">
                          <h4 lang="nl">{word.term}</h4>
                          <PhraseAudio text={word.term} disabled={busy} />
                        </div>
                        <LearningText text={word.meaning} />
                        <p>
                          <LearningText text={word.example} />
                          <PhraseAudio text={word.example.nl} disabled={busy} />
                        </p>
                      </article>
                    ))}
                  </div>
                </details>
              )}
              {phase === "task" && (
                <>
                  {storageError && (
                    <p className="practice-hint" role="status">
                      Je browser kan dit concept niet bewaren. Je tekst blijft hier staan; kopieer hem voordat
                      je dit onderwerp verlaat.
                    </p>
                  )}
                  {error && (
                    <p className="error" role="alert">
                      {error}
                    </p>
                  )}
                  <div className="practice-submit">
                    <button className="button" disabled={busy || !ready} onClick={() => void submit()}>
                      {submitBusy ? "Even nakijken…" : `Rond ${skillNames[skill].toLowerCase()} af`}
                      <Icon name="check" size={17} />
                    </button>
                  </div>
                  {feedback && (
                    <div
                      className={`practice-feedback ${feedback.completed ? "complete" : "retry"}`}
                      role="status"
                    >
                      <h4>
                        {feedback.passed === false
                          ? "Je hebt geoefend. Bekijk je volgende stap."
                          : feedback.completed
                            ? "Een onderwerp verder."
                            : "Probeer het nog eens."}
                      </h4>
                      <LearningText text={feedback.feedback} />
                      {feedback.criteria && (
                        <ul className="topic-feedback-criteria">
                          {feedback.criteria.map((item, index) => (
                            <li key={index}>
                              <strong>
                                <LearningText text={item.criterion} />
                              </strong>
                              <span className="quiet-badge">{item.met ? "Gelukt" : "Verder oefenen"}</span>
                              <LearningText text={item.feedback} />
                            </li>
                          ))}
                        </ul>
                      )}
                      <button className="button secondary" disabled={busy} onClick={onBack}>
                        Kies een ander onderwerp
                        <Icon name="arrow" size={17} />
                      </button>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
