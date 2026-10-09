import { Illustration, type IllustrationName } from "@/components/illustrations";
import { UiText } from "@/components/ui/UiText";
import type { Accent } from "@/lib/design/identity";
import { uiCopy, type Copy } from "@/lib/ui-copy";

const CARDS: { illustration: IllustrationName; accent: Accent; title: Copy; body: Copy }[] = [
  {
    illustration: "stories",
    accent: "stories",
    title: uiCopy.welcome.howStoryTitle,
    body: uiCopy.welcome.howStory,
  },
  {
    illustration: "words",
    accent: "words",
    title: uiCopy.welcome.howWordsTitle,
    body: uiCopy.welcome.howWords,
  },
  {
    illustration: "writer",
    accent: "speaking",
    title: uiCopy.welcome.howSpeakTitle,
    body: uiCopy.welcome.howSpeak,
  },
  { illustration: "goal", accent: "today", title: uiCopy.welcome.howGoalTitle, body: uiCopy.welcome.howGoal },
];

/** "Zo werkt Taalstudio": the method in four cards, in Dutch with every selected support language. */
export function HowItWorks() {
  return (
    <section className="how-it-works" aria-labelledby="how-title" data-testid="how-it-works">
      <h2 id="how-title">
        <UiText text={uiCopy.welcome.howTitle} tier="always" />
      </h2>
      <ul className="how-grid">
        {CARDS.map((card) => (
          <li key={card.illustration} className="how-card" data-accent={card.accent}>
            <Illustration name={card.illustration} size={64} />
            <h3>
              <UiText text={card.title} tier="always" />
            </h3>
            <p>
              <UiText text={card.body} tier="always" />
            </p>
          </li>
        ))}
      </ul>
      <p className="how-note">
        <UiText text={uiCopy.honesty.generated} tier="always" />
      </p>
    </section>
  );
}
