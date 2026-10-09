"use client";

import { Illustration, type IllustrationName } from "@/components/illustrations";
import { UiText } from "@/components/ui/UiText";
import { uiCopy, type Copy } from "@/lib/ui-copy";

const SECTIONS: { id: string; illustration: IllustrationName; title: Copy; body: Copy }[] = [
  { id: "lessen", illustration: "quiet", title: uiCopy.about.lessonsTitle, body: uiCopy.about.lessons },
  { id: "taalmodel", illustration: "writer", title: uiCopy.about.modelTitle, body: uiCopy.about.model },
  { id: "stemmen", illustration: "stories", title: uiCopy.about.voiceTitle, body: uiCopy.about.voices },
  { id: "meten", illustration: "goal", title: uiCopy.about.measureTitle, body: uiCopy.about.measure },
  { id: "bewaren", illustration: "words", title: uiCopy.about.dataTitle, body: uiCopy.about.data },
];

/** /over: how the content is made, what it says and what it does not; one page the chips link to. */
export function AboutContent() {
  return (
    <div className="about-content" data-accent="neutral" data-testid="about-content">
      <header className="page-heading">
        <div>
          <h1>
            <UiText text={uiCopy.about.title} tier="always" />
          </h1>
          <p>
            <UiText text={uiCopy.about.intro} tier="always" />
          </p>
        </div>
      </header>
      <div className="about-sections">
        {SECTIONS.map((section) => (
          <section
            key={section.id}
            id={section.id}
            className="about-section"
            aria-labelledby={`${section.id}-title`}
          >
            <Illustration name={section.illustration} size={56} />
            <div>
              <h2 id={`${section.id}-title`}>
                <UiText text={section.title} tier="always" />
              </h2>
              <p>
                <UiText text={section.body} tier="always" />
              </p>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
