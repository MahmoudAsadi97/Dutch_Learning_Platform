"use client";

import { useId, useRef, useState } from "react";

import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import type { StudyLesson } from "@/lib/client/study";
import { studyCopy } from "@/lib/copy/study";

const PAGE_SIZE = 6;
const searchText = (value: string) =>
  value.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase("nl-BE");

/** Browse one topic's stories without opening another library or losing the current activity. */
export function StudyActivityPicker({
  activities,
  selected,
  onChoose,
}: {
  activities: StudyLesson["activities"];
  selected: string;
  onChoose: (id: string) => Promise<boolean>;
}) {
  const panelId = useId();
  const headingId = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const current = activities.find((item) => item.id === selected);
  const filtered = activities.filter((item) =>
    searchText(`${item.title.nl} ${item.title.en ?? ""}`).includes(searchText(query.trim())),
  );
  const lastPage = Math.max(0, Math.ceil(filtered.length / PAGE_SIZE) - 1);
  const activePage = Math.min(page, lastPage);
  const visible = filtered.slice(activePage * PAGE_SIZE, (activePage + 1) * PAGE_SIZE);

  function close() {
    setOpen(false);
    trigger.current?.focus();
  }

  async function choose(id: string) {
    if (busy) return;
    if (id === selected) return close();
    setBusy(true);
    setError(false);
    try {
      if (await onChoose(id)) close();
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="study-story-picker"
      onKeyDown={(event) => {
        if (event.key === "Escape" && open && !busy) {
          event.preventDefault();
          event.stopPropagation();
          close();
        }
      }}
    >
      <button
        type="button"
        className="study-story-trigger"
        ref={trigger}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => {
          if (!open) {
            setQuery("");
            setPage(
              Math.max(0, Math.floor(activities.findIndex((item) => item.id === selected) / PAGE_SIZE)),
            );
          }
          setOpen(!open);
        }}
      >
        <span>
          <small>
            <LearningText text={studyCopy.chooseStory} />
          </small>
          <strong>
            <LearningText text={current?.title ?? studyCopy.storiesInTopic} />
          </strong>
        </span>
        <Icon name={open ? "chevron-up" : "chevron-down"} size={18} />
      </button>
      {open && (
        <section className="study-story-panel" id={panelId} aria-labelledby={headingId} aria-busy={busy}>
          <h2 id={headingId}>
            <LearningText text={studyCopy.storiesInTopic} />
          </h2>
          <label className="study-story-search">
            <span className="visually-hidden">
              <LearningText text={studyCopy.searchStories} />
            </span>
            <Icon name="search" size={16} />
            <input
              type="search"
              value={query}
              placeholder={studyCopy.searchStories.nl}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(0);
              }}
            />
          </label>
          <ul className="study-story-options">
            {visible.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  aria-current={item.id === selected ? "true" : undefined}
                  data-activity-id={item.id}
                  disabled={busy}
                  onClick={() => void choose(item.id)}
                >
                  <LearningText text={item.title} />
                  <Icon name={item.id === selected ? "check" : "arrow"} size={16} />
                </button>
              </li>
            ))}
          </ul>
          {visible.length === 0 && (
            <p role="status">
              <LearningText text={studyCopy.noStoriesFound} />
            </p>
          )}
          {lastPage > 0 && (
            <nav className="study-story-pages" aria-label={studyCopy.browseStories.nl}>
              <button type="button" disabled={activePage === 0} onClick={() => setPage(activePage - 1)}>
                <Icon name="arrow-left" size={16} />
                <LearningText text={studyCopy.previous} />
              </button>
              <span aria-live="polite">
                {activePage + 1} / {lastPage + 1}
              </span>
              <button
                type="button"
                disabled={activePage === lastPage}
                onClick={() => setPage(activePage + 1)}
              >
                <LearningText text={studyCopy.nextTopics} />
                <Icon name="chevron" size={16} />
              </button>
            </nav>
          )}
          {error && (
            <p role="alert">
              <LearningText text={studyCopy.storyChoiceFailed} />
            </p>
          )}
        </section>
      )}
    </div>
  );
}
