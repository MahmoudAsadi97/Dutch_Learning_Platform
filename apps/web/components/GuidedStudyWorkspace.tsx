"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AlphabetPractice } from "@/components/AlphabetPractice";
import { StudyGrammar } from "@/components/study/StudyGrammar";
import { StudyPersonalLibrary } from "@/components/StudyPersonalLibrary";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { apiJson } from "@/lib/client/api";
import { friendlyError } from "@/lib/client/curriculum";
import { useNavigationCheck } from "@/lib/client/navigation";
import { rememberStudyStage } from "@/lib/client/study-stage";
import { studyHref, studySkillCopy, type StudyCatalog, type StudyStep } from "@/lib/client/study";
import { SKILLS, STAGE_IDS, stageLabel, stageNames, type Skill } from "@/lib/domain/registry";
import { studyCopy, studyLabels, studyStarterTopics } from "@/lib/copy/study";
import { StudyError, WordReference } from "@/components/study/StudyShared";
import { GuidedLesson } from "@/components/study/GuidedLesson";
import { StudyDeepPractice } from "@/components/study/StudyDeepPractice";

export function GuidedStudyWorkspace({
  stageId,
  skill,
  topicId,
  activityId,
  initialStep = "prepare",
  initialPart,
  initialView,
}: {
  stageId: string;
  skill: Skill;
  topicId?: string;
  activityId?: string;
  initialStep?: StudyStep;
  initialPart?: string;
  initialView?: string;
}) {
  const router = useRouter();
  const canLeave = useNavigationCheck();
  const [catalog, setCatalog] = useState<StudyCatalog | null>(null);
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState("");
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [reference, setReference] = useState(initialView === "vocabulary");
  const [alphabet, setAlphabet] = useState(initialView === "alphabet");
  const [grammar, setGrammar] = useState(initialView === "grammar");
  const [personal, setPersonal] = useState<"words" | "stories" | null>(
    initialView === "personal-words" ? "words" : initialView === "personal-stories" ? "stories" : null,
  );
  const [showPlanned, setShowPlanned] = useState(false);
  const [topicPage, setTopicPage] = useState({ key: "", index: 0 });
  const deepPractice = initialView === "conversation" || initialView === "extended";
  useEffect(() => rememberStudyStage(stageId), [stageId]);
  useEffect(() => {
    if (topicId || deepPractice) return;
    const controller = new AbortController();
    apiJson<StudyCatalog>(`study/${stageId}/topics?skill=${skill}`, { signal: controller.signal })
      .then((value) => {
        setCatalog(value);
        setError("");
      })
      .catch((cause) => {
        if (cause?.name !== "AbortError") setError(friendlyError(cause, "load"));
      });
    return () => controller.abort();
  }, [stageId, skill, topicId, retry, deepPractice]);
  const activeView = personal
    ? `personal-${personal}`
    : alphabet
      ? "alphabet"
      : grammar
        ? "grammar"
        : reference
          ? "vocabulary"
          : initialView === "conversation"
            ? "conversation"
            : undefined;
  const filtered =
    catalog?.topics.filter(
      (topic) =>
        (showPlanned || topic.available) &&
        (!group || topic.group === group) &&
        `${topic.title.nl} ${topic.title.en ?? ""}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()),
    ) ?? [];
  const pageKey = JSON.stringify([stageId, skill, query, group, showPlanned]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / 12));
  const pageIndex = topicPage.key === pageKey ? Math.min(topicPage.index, pageCount - 1) : 0;
  const visibleTopics = filtered.slice(pageIndex * 12, (pageIndex + 1) * 12);
  return (
    <div className="study-workspace" data-testid="guided-study-workspace">
      <nav className="study-breadcrumb" aria-label={studyCopy.breadcrumb.nl}>
        <Link href="/">
          {" "}
          <LearningText text={studyCopy.dashboard} />{" "}
        </Link>
        <Icon name="chevron" size={14} />
        <Link href="/leerpad">
          {" "}
          <LearningText text={studyCopy.levels} />{" "}
        </Link>
        <Icon name="chevron" size={14} />
        <span>{stageLabel(stageId)}</span>
        {topicId && (
          <>
            <Icon name="chevron" size={14} />
            <Link href={studyHref(stageId, skill)}>
              {" "}
              <LearningText text={studyCopy.topics} />{" "}
            </Link>
          </>
        )}
      </nav>
      <div className="study-workspace-bar">
        <div className="study-stage-picker">
          <label htmlFor="study-stage">
            {" "}
            <LearningText text={studyCopy.level} />{" "}
          </label>
          <select
            id="study-stage"
            value={stageId}
            onChange={async (event) => {
              const nextStage = event.target.value;
              if (await canLeave())
                router.push(studyHref(nextStage, skill, activeView ? { view: activeView } : {}));
            }}
          >
            {STAGE_IDS.map((stage) => (
              <option key={stage} value={stage}>
                {stageLabel(stage)} · {stageNames[stage]}
              </option>
            ))}
          </select>
        </div>
        <div className="study-workspace-tools">
          <button className="study-tool-button" onClick={() => setGrammar(!grammar)} aria-expanded={grammar}>
            <Icon name="pen" size={17} /> <LearningText text={studyCopy.grammar} />{" "}
          </button>
          <button
            className="study-tool-button"
            onClick={() => setReference(!reference)}
            aria-expanded={reference}
          >
            <Icon name="book" size={17} />
            <LearningText text={studyCopy.wordReference} />
          </button>
          {stageId === "pre-a1" && (
            <button
              className="study-tool-button"
              aria-expanded={alphabet}
              onClick={() => setAlphabet(!alphabet)}
            >
              <Icon name="volume" size={17} />
              <LearningText text={studyCopy.alphabetNumbers} />{" "}
            </button>
          )}
        </div>
      </div>
      <nav className="study-skill-tabs" aria-label={studyCopy.chooseSkill.nl}>
        {SKILLS.map((key) => (
          <Link
            key={key}
            href={studyHref(stageId, key, {
              ...(topicId && !deepPractice ? { topic: topicId } : {}),
              ...(activeView && !deepPractice ? { view: activeView } : {}),
            })}
            aria-current={skill === key ? "page" : undefined}
          >
            <Icon name={studySkillCopy[key].icon} size={19} />
            <LearningText text={studySkillCopy[key].title} />
          </Link>
        ))}
      </nav>
      {reference && (
        <details className="study-tool-panel" open>
          <summary
            onClick={(event) => {
              event.preventDefault();
              setReference(false);
            }}
          >
            <LearningText text={studyCopy.referenceHeading} /> {stageLabel(stageId)}{" "}
            <Icon name="close" size={17} />
          </summary>
          <button className="study-text-button" onClick={() => setPersonal("words")}>
            {" "}
            <LearningText text={studyCopy.savedWords} />{" "}
          </button>
          <WordReference stageId={stageId} />
        </details>
      )}
      {grammar && (
        <section className="study-tool-panel">
          <div className="study-section-heading">
            <h2>
              {" "}
              <LearningText text={studyCopy.grammarInUse} />{" "}
            </h2>
            <button className="study-text-button" onClick={() => setGrammar(false)}>
              {" "}
              <LearningText text={studyCopy.close} />{" "}
            </button>
          </div>
          <StudyGrammar stageId={stageId} />
        </section>
      )}
      {personal && (
        <section className="study-tool-panel">
          <div className="study-section-heading">
            <h2>{personal === "words" ? studyCopy.savedWords.nl : studyCopy.personalStories.nl}</h2>
            <button className="study-text-button" onClick={() => setPersonal(null)}>
              {" "}
              <LearningText text={studyCopy.close} />{" "}
            </button>
          </div>
          <StudyPersonalLibrary kind={personal} />
        </section>
      )}
      {alphabet && stageId === "pre-a1" && (
        <div className="study-tool-panel">
          <div className="study-section-heading">
            <h2>
              {" "}
              <LearningText text={studyCopy.firstWordsSounds} />{" "}
            </h2>
            <button className="study-text-button" onClick={() => setAlphabet(false)}>
              <LearningText text={studyCopy.close} />{" "}
            </button>
          </div>
          <AlphabetPractice />
        </div>
      )}
      {deepPractice ? (
        <StudyDeepPractice
          key={`${stageId}.${skill}.${topicId ?? ""}`}
          stageId={stageId}
          skill={skill}
          topicId={topicId}
          conversation={initialView === "conversation" && skill === "speaking"}
        />
      ) : topicId ? (
        <GuidedLesson
          key={`${stageId}.${skill}.${topicId}.${activityId ?? ""}`}
          stageId={stageId}
          skill={skill}
          topicId={topicId}
          activityId={activityId}
          initialStep={initialStep}
          initialPart={initialPart}
        />
      ) : (
        <section className="study-topic-library" aria-labelledby="study-topic-title">
          <header className="study-page-heading">
            <p className="study-kicker">
              {stageLabel(stageId)} · {studySkillCopy[skill].title.nl}
            </p>
            <h1 id="study-topic-title">
              <LearningText text={studyCopy.whatWouldYouLikeToLearn} />
            </h1>
            <p>
              <LearningText text={studyLabels.topicIntroduction(skill === "reading")} />
            </p>
          </header>
          {skill === "speaking" && (
            <details className="study-optional-practice">
              <summary>
                <LearningText text={studyCopy.situationConversations} />
              </summary>
              <p>
                <LearningText text={studyCopy.conversationInvitation} />
              </p>
              <Link className="button secondary" href={studyHref(stageId, skill, { view: "conversation" })}>
                <LearningText text={studyCopy.openConversations} />
              </Link>
            </details>
          )}
          {stageId === "pre-a1" && (
            <section className="study-starter-topics" aria-label={studyCopy.firstPractice.nl}>
              <h2>
                <LearningText text={studyCopy.firstPractice} />
              </h2>
              <div className="study-part-tabs">
                {studyStarterTopics.map((item) => (
                  <Link
                    className="button secondary"
                    key={item.topic}
                    href={studyHref(stageId, skill, { topic: item.topic })}
                  >
                    <LearningText text={item.title} />
                  </Link>
                ))}
              </div>
            </section>
          )}
          <div className="study-topic-filters">
            <label className="study-search">
              <Icon name="search" size={18} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={studyCopy.topicSearchPlaceholder.nl}
                aria-label={studyCopy.topicSearchLabel.nl}
                maxLength={120}
              />
            </label>
            <label className="study-group-filter">
              <span className="sr-only">
                {" "}
                <LearningText text={studyCopy.filterTheme} />{" "}
              </span>
              <select value={group} onChange={(event) => setGroup(event.target.value)}>
                <option value="">
                  {" "}
                  <LearningText text={studyCopy.allThemes} />{" "}
                </option>
                {catalog?.groups.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title.nl}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {skill === "reading" && (
            <button className="study-text-button" onClick={() => setPersonal("stories")}>
              {" "}
              <LearningText text={studyCopy.openPersonalStories} />{" "}
            </button>
          )}
          {error ? (
            <StudyError message={error} retry={() => setRetry((value) => value + 1)} />
          ) : !catalog ? (
            <div className="study-loading" role="status">
              <LearningText text={studyCopy.loadingTopics} />{" "}
            </div>
          ) : (
            <>
              <div className="study-topic-grid">
                {visibleTopics.map((topic) =>
                  topic.available ? (
                    <Link
                      key={topic.id}
                      href={studyHref(stageId, skill, { topic: topic.id })}
                      className="study-topic-card"
                    >
                      <span className="study-topic-mark">
                        <Icon name={studySkillCopy[skill].icon} size={20} />
                      </span>
                      <span>
                        <strong>
                          <LearningText text={topic.title} />
                        </strong>
                        <small>
                          <LearningText
                            text={
                              catalog.groups.find((item) => item.id === topic.group)?.title ?? studyCopy.topic
                            }
                          />
                        </small>
                      </span>
                      <Icon name="chevron" size={17} />
                    </Link>
                  ) : (
                    <div key={topic.id} className="study-topic-card is-planned">
                      <span>
                        <strong>
                          <LearningText text={topic.title} />
                        </strong>
                        <small>
                          <LearningText text={topic.availability_note} />
                        </small>
                      </span>
                    </div>
                  ),
                )}
              </div>
              {pageCount > 1 && (
                <nav className="study-pagination" aria-label={studyCopy.browseTopics.nl}>
                  <button
                    className="button secondary"
                    disabled={pageIndex === 0}
                    onClick={() => setTopicPage({ key: pageKey, index: pageIndex - 1 })}
                  >
                    <LearningText text={studyCopy.previous} />
                  </button>
                  <span role="status" aria-live="polite">
                    {pageIndex + 1} / {pageCount}
                  </span>
                  <button
                    className="button secondary"
                    disabled={pageIndex + 1 >= pageCount}
                    onClick={() => setTopicPage({ key: pageKey, index: pageIndex + 1 })}
                  >
                    <LearningText text={studyCopy.nextTopics} />
                  </button>
                </nav>
              )}
              {filtered.length === 0 && (
                <div className="study-empty">
                  <Icon name="search" size={26} />
                  <h2>
                    {" "}
                    <LearningText text={studyCopy.noTopics} />{" "}
                  </h2>
                  <p>
                    {" "}
                    <LearningText text={studyCopy.changeTopicSearch} />{" "}
                  </p>
                  <button
                    className="button secondary"
                    onClick={() => {
                      setQuery("");
                      setGroup("");
                    }}
                  >
                    <LearningText text={studyCopy.clearFilters} />{" "}
                  </button>
                </div>
              )}
              <label className="study-planned-toggle">
                <input
                  type="checkbox"
                  checked={showPlanned}
                  onChange={(event) => setShowPlanned(event.target.checked)}
                />
                <LearningText text={studyCopy.includePlanned} />{" "}
              </label>
            </>
          )}
        </section>
      )}
    </div>
  );
}
