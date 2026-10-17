"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { StageLibraryPicker, useLibraryStages } from "@/components/LibraryStagePicker";
import { StoryTime, WordLibrary } from "@/components/LearningLibrary";
import { StoryLibrary } from "@/components/StoryLibrary";
import { WordReview } from "@/components/WordReview";
import { UiText } from "@/components/ui/UiText";
import { isStageId, stageLabel } from "@/lib/domain/registry";
import { libraryHubsCopy as copy } from "@/lib/copy/libraryHubs";
import { fill } from "@/lib/ui-copy";

/** Course content is the primary library. Saved material is a separate, explicitly chosen view. */
export function LibraryHub({ kind }: { kind: "stories" | "words" }) {
  const params = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const requested = params.get("stage") ?? "pre-a1";
  const stageId = isStageId(requested) ? requested : "pre-a1";
  const personal = params.get("view") === "personal";
  const { stages, failed, retry } = useLibraryStages();
  const coverage = stages?.find((stage) => stage.id === stageId)?.coverage;
  const title = kind === "stories" ? copy.storiesTitle : copy.wordsTitle;
  const intro = kind === "stories" ? copy.storiesIntro : copy.wordsIntro;
  const href = `${pathname}?stage=${stageId}`;
  return (
    <div className="library-hub" data-testid={`${kind}-hub`}>
      <header className="page-heading">
        <div>
          <h1>
            <UiText text={title} />
          </h1>
          <p>
            <UiText text={intro} tier="guide" />
          </p>
        </div>
      </header>
      <nav className="library-hub-views" aria-label={title.nl}>
        <Link href={href} aria-current={!personal ? "page" : undefined}>
          <UiText text={kind === "stories" ? copy.courseStories : copy.courseWords} inline />
        </Link>
        <Link href={`${href}&view=personal`} aria-current={personal ? "page" : undefined}>
          <UiText text={kind === "stories" ? copy.personalStories : copy.personalWords} inline />
        </Link>
      </nav>
      {personal ? (
        <section className="library-hub-personal">
          <p className="muted">
            <UiText
              text={kind === "stories" ? copy.personalStoriesNote : copy.personalWordsNote}
              tier="guide"
            />
          </p>
          {kind === "stories" ? <StoryLibrary embedded /> : <WordReview embedded />}
        </section>
      ) : (
        <>
          <StageLibraryPicker
            stageId={stageId}
            onChange={(stage) => router.replace(`${pathname}?stage=${stage}`, { scroll: false })}
          />
          {failed ? (
            <p className="error" role="alert">
              <UiText text={copy.failed} inline />{" "}
              <button className="linklike" onClick={retry}>
                <UiText text={copy.retry} inline />
              </button>
            </p>
          ) : !stages ? (
            <p role="status">
              <UiText text={copy.loading} />
            </p>
          ) : null}
          {coverage && (
            <aside className="library-hub-counts" aria-label={stageLabel(stageId)}>
              <p>
                <strong>
                  <UiText
                    text={
                      kind === "stories"
                        ? fill(copy.storiesCount, {
                            stories: coverage.eligible_authored_stories,
                            target: coverage.targets.authored_stories,
                          })
                        : fill(copy.wordsCount, { words: coverage.words, core: coverage.productive_core })
                    }
                  />
                </strong>
              </p>
              {kind === "stories" && coverage.legacy_stories > 0 && (
                <p className="small-text muted">
                  <UiText text={fill(copy.shortTexts, { count: coverage.legacy_stories })} tier="guide" />
                </p>
              )}
              <p className="small-text muted">
                <UiText text={copy.reviewNote} tier="guide" />
              </p>
            </aside>
          )}
          {kind === "stories" ? (
            <StoryTime key={stageId} stageId={stageId} />
          ) : (
            <WordLibrary key={stageId} stageId={stageId} />
          )}
        </>
      )}
    </div>
  );
}
