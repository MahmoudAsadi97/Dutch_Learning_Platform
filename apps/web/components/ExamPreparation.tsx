"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { UiText } from "@/components/ui/UiText";
import { apiJson } from "@/lib/client/api";
import type { ExamReferences } from "@/lib/client/alignment";
import { alignmentCopy as copy } from "@/lib/copy/alignment";

const levels = ["A1", "A2", "B1", "B2", "C1", "C2"];

export function ExamPreparation() {
  const [level, setLevel] = useState("A2");
  const [data, setData] = useState<ExamReferences | null>(null);
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void apiJson<ExamReferences>("curriculum/reference/exams", { signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted) setData(value);
      })
      .catch((cause) => {
        if (cause?.name !== "AbortError") setFailed(true);
      });
    return () => controller.abort();
  }, [retry]);
  const profiles = data?.profiles.filter((profile) => profile.levels.includes(level)) ?? [];
  return (
    <div className="exam-preparation">
      <header>
        <h1>
          <UiText text={copy.exams} />
        </h1>
        <p>
          <UiText text={copy.examIntro} tier="guide" />
        </p>
      </header>
      <div className="practice-source-switch" role="group" aria-label={copy.reference.nl}>
        {levels.map((value) => (
          <button
            key={value}
            className="button secondary"
            aria-pressed={level === value}
            onClick={() => setLevel(value)}
          >
            {value}
          </button>
        ))}
      </div>
      {failed ? (
        <button
          className="linklike"
          onClick={() => {
            setFailed(false);
            setRetry((value) => value + 1);
          }}
        >
          <UiText text={copy.failed} />
        </button>
      ) : !data ? (
        <p role="status">
          <UiText text={copy.loading} />
        </p>
      ) : (
        <div className="exam-profile-list">
          {profiles.map((profile) => (
            <article className="exam-profile" key={profile.id}>
              <p className="eyebrow">{profile.levels.join(" · ")}</p>
              <h2>{profile.title}</h2>
              <p>
                <UiText
                  text={
                    profile.family === "cnavt"
                      ? copy.cnavt
                      : profile.family === "itna"
                        ? copy.itna
                        : copy.other
                  }
                  tier="guide"
                />
              </p>
              <details>
                <summary>
                  <UiText text={copy.sources} />
                </summary>
                <ul>
                  {data.sources
                    .filter((source) => profile.source_ids.includes(source.id))
                    .map((source) => (
                      <li key={source.id}>
                        <a href={source.url} target="_blank" rel="noreferrer">
                          {source.title}
                        </a>
                      </li>
                    ))}
                </ul>
              </details>
            </article>
          ))}
          {level === "C2" && (
            <p>
              <UiText text={copy.noC2} tier="guide" />
            </p>
          )}
        </div>
      )}
      <nav className="exam-skill-links" aria-label={copy.target.nl}>
        {(["reading", "listening", "speaking", "writing"] as const).map((skill) => (
          <Link
            className="button secondary"
            href={`/learn/${level.toLowerCase()}?skill=${skill}`}
            key={skill}
          >
            <UiText text={copy[skill]} />
          </Link>
        ))}
      </nav>
    </div>
  );
}
