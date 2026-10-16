import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { SpokenText } from "@/components/SpokenPassage";
import { StoryPractice } from "@/components/StoryPractice";
import { WordUsage } from "@/components/WordUsage";
import type { LibraryWord } from "@/lib/client/library";
import { CurriculumQuestions } from "@/components/CurriculumControls";
import { clearLearnerStorage, storageKeys } from "@/lib/client/storage";
import { topicHref } from "@/lib/client/learning-agents";

vi.mock("@/components/PhraseAudio", () => ({
  PhraseAudio: ({ text, disabled }: { text: string; disabled?: boolean }) => (
    <button disabled={disabled} aria-label={`Luister: ${text}`}>
      Luister
    </button>
  ),
}));
vi.mock("@/components/LanguageSupport", () => ({
  LearningText: ({
    text,
    supportOnly,
  }: {
    text?: { nl: string; en?: string; fa?: string };
    supportOnly?: boolean;
  }) =>
    text ? (
      <span>
        {!supportOnly && text.nl}
        {text.en && <span lang="en">{text.en}</span>}
      </span>
    ) : null,
}));
vi.mock("@/components/WritingCoach", () => ({
  WritingCoach: ({
    text,
    stageId,
    onApply,
  }: {
    text: string;
    stageId: string;
    onApply: (text: string) => void;
  }) => (
    <section aria-label={`Schrijfhulp ${stageId}`}>
      <span>{text}</span>
      <button onClick={() => onApply("Ik kom morgen.")}>Gebruik correctie</button>
    </section>
  ),
}));

beforeEach(() => sessionStorage.clear());

test("each target sentence has its own replay without changing appointment times or translations", () => {
  render(
    <SpokenText
      text={{
        nl: "De afspraak is om 14.00 uur. Kom je morgen?",
        en: "The appointment is at 2 pm. Are you coming tomorrow?",
      }}
      disabled
    />,
  );
  const buttons = screen.getAllByRole("button");
  expect(buttons).toHaveLength(2);
  expect(buttons[0]).toHaveAccessibleName("Luister: De afspraak is om 14.00 uur.");
  expect(buttons[1]).toHaveAccessibleName("Luister: Kom je morgen?");
  for (const button of buttons) expect(button).toBeDisabled();
  expect(screen.getByText("The appointment is at 2 pm. Are you coming tomorrow?")).toHaveAttribute(
    "lang",
    "en",
  );
});

const word: LibraryWord = {
  id: "a2-v-transfer",
  term: "komen",
  topic: { nl: "Een afspraak" },
  meaning: { nl: "ergens aankomen" },
  example: { nl: "Ik kom morgen." },
  forms: [
    { label: { nl: "Nu" }, text: { nl: "Ik kom." } },
    { label: { nl: "Gisteren" }, text: { nl: "Ik kwam." } },
  ],
  contexts: [
    {
      id: "visit",
      setting: { nl: "Bij een vriend" },
      sentence: { nl: "Ik kom morgen bij jou." },
      production_prompt: { nl: "Vertel wanneer je op bezoek komt." },
      structure: "present",
    },
    {
      id: "class",
      setting: { nl: "In de les" },
      sentence: { nl: "Ik kom met de bus naar school." },
      production_prompt: { nl: "Vertel hoe je naar de les komt." },
      structure: "present",
    },
  ],
};

test("word forms and changing situations require a personal response without inventing mastery", async () => {
  render(<WordUsage word={word} />);
  await userEvent.click(screen.getByText("Woordvormen en zinsbouw"));
  expect(screen.getByRole("button", { name: "Luister: Ik kwam." })).toBeVisible();
  const input = screen.getByRole("textbox");
  await userEvent.type(input, "Ik kom dinsdag.");
  expect(input).toHaveValue("Ik kom dinsdag.");
  await userEvent.click(screen.getByRole("button", { name: /Nog een situatie/ }));
  expect(screen.getByText("In de les")).toBeVisible();
  expect(screen.getByRole("button", { name: "Luister: Ik kom met de bus naar school." })).toBeVisible();
  expect(input).toHaveValue("");
  expect(screen.getByText(/niet bewaard of beoordeeld/)).toBeVisible();
  expect(screen.queryByText(/beheerst|geslaagd/)).not.toBeInTheDocument();
});

test("beginner story practice stays simple and opens correction only after the learner writes", async () => {
  render(<StoryPractice stageId="pre-a1" />);
  expect(screen.getByText(/Kies een persoon en een ding/)).toBeVisible();
  expect(screen.queryByRole("region", { name: /Schrijfhulp/ })).not.toBeInTheDocument();
  await userEvent.type(screen.getByRole("textbox"), "Ik kom morgen");
  expect(screen.getByRole("region", { name: "Schrijfhulp pre-a1" })).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Gebruik correctie" }));
  expect(screen.getByRole("textbox")).toHaveValue("Ik kom morgen.");
  expect(screen.queryAllByRole("link")).toHaveLength(0);
});

test("advanced story practice uses interpretation and genuine linked four-skill routes", () => {
  render(<StoryPractice stageId="c2" topicId="c2-t-source-02" />);
  expect(screen.getByText(/impliciete betekenis en stilistisch effect/)).toBeVisible();
  const links = screen.getAllByRole("link");
  expect(links).toHaveLength(4);
  expect(links.map((link) => link.getAttribute("href"))).toEqual([
    "/learn/c2?skill=reading&topic=c2-t-source-02",
    "/learn/c2?skill=listening&topic=c2-t-source-02",
    "/learn/c2?skill=speaking&topic=c2-t-source-02",
    "/learn/c2?skill=writing&topic=c2-t-source-02",
  ]);
});

test("story drafts survive navigation, stay scoped to their learner and are removed on sign-out", async () => {
  const view = render(<StoryPractice stageId="a1" storyId="a1-s001" learnerKey="learner-one" />);
  await userEvent.type(screen.getByRole("textbox"), "Ik kom morgen.");
  const key = storageKeys.topicDraft("learner-one", "a1", "story", "a1-s001");
  expect(sessionStorage.getItem(key)).toBe("Ik kom morgen.");
  view.rerender(<StoryPractice stageId="a1" storyId="a1-s001" learnerKey="learner-two" />);
  expect(screen.getByRole("textbox")).toHaveValue("");
  view.rerender(<StoryPractice stageId="a1" storyId="a1-s001" learnerKey="learner-one" />);
  expect(screen.getByRole("textbox")).toHaveValue("Ik kom morgen.");
  expect(clearLearnerStorage([sessionStorage])).toBe(1);
  expect(sessionStorage.getItem(key)).toBeNull();
});

test("practice questions replay each sentence while final-test questions do not gain playback", () => {
  const questions = [
    {
      id: "question",
      prompt: { nl: "Lees de brief. Wie komt morgen?" },
      options: [{ nl: "Sara komt. Zij neemt haar tas mee." }, { nl: "Omar komt." }],
    },
  ];
  const view = render(<CurriculumQuestions questions={questions} answers={{}} onAnswer={() => {}} />);
  expect(screen.getAllByRole("button")).toHaveLength(5);
  view.rerender(<CurriculumQuestions questions={questions} answers={{}} onAnswer={() => {}} exam />);
  expect(screen.queryAllByRole("button")).toHaveLength(0);
});

test("linked practice accepts stage-bound authored IDs and refuses cross-stage or external targets", () => {
  expect(topicHref("a1", "writing", "a1-t-unit-the-letter")).toBe(
    "/learn/a1?skill=writing&topic=a1-t-unit-the-letter",
  );
  expect(topicHref("a1", "listening", "a1-t-source-02")).toBe(
    "/learn/a1?skill=listening&topic=a1-t-source-02",
  );
  for (const id of ["a2-t-unit-the-letter", "https://example.com", "a1-t-unit-../settings", "a1-t-unit-"])
    expect(topicHref("a1", "writing", id)).toBeNull();
  expect(topicHref("a1", "invalid-skill", "a1-t001")).toBeNull();
});
