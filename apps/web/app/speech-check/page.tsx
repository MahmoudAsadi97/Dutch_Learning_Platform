"use client";

// A client page, so the copy entries reach UiText as the same objects the Persian review registered.
import { SpeechCheck } from "@/components/SpeechCheck";
import { UiText } from "@/components/ui/UiText";
import { speechCopy } from "@/lib/copy/speech";

export default function SpeechCheckPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">
            <UiText text={speechCopy.pageEyebrow} />
          </p>
          <h1>
            <UiText text={speechCopy.pageTitle} />
          </h1>
          <p>
            <UiText text={speechCopy.pageIntro} tier="guide" />
          </p>
        </div>
        <span className="quiet-badge">
          <UiText text={speechCopy.pageBadge} inline />
        </span>
      </header>
      <aside className="information-callout">
        <div>
          <h3>
            <UiText text={speechCopy.quietPlaceTitle} />
          </h3>
          <p>
            <UiText text={speechCopy.quietPlaceBody} tier="guide" />
          </p>
        </div>
      </aside>
      <SpeechCheck />
    </>
  );
}
