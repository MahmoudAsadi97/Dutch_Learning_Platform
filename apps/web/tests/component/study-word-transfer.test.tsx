import { useState } from "react";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { CompactWords, WordReference } from "@/components/study/StudyShared";
import { GuidedLesson } from "@/components/study/GuidedLesson";
import { WordTransferPractice } from "@/components/study/WordTransferPractice";
import { apiJson } from "@/lib/client/api";
import type { StudyLesson, StudyWord } from "@/lib/client/study";

const state = vi.hoisted(() => ({ english: true, email: "learner-one@example.test" }));

vi.mock("@/components/LanguageSupport", () => ({
  useLanguageSupport: () => ({ showEnglish: state.english }),
  LearningText: ({
    text,
    supportOnly = false,
  }: {
    text?: { nl: string; en?: string };
    supportOnly?: boolean;
  }) =>
    text ? (
      <span>
        {!supportOnly && <span lang="nl">{text.nl}</span>}
        {state.english && text.en && <span lang="en">{text.en}</span>}
      </span>
    ) : null,
}));
vi.mock("@/components/PhraseAudio", () => ({
  PhraseAudio: ({ text }: { text: string }) => (
    <button type="button" aria-label={`Luister: ${text}`}>
      Luister
    </button>
  ),
}));
vi.mock("@/lib/client/profile", () => ({
  useProfile: () => ({ data: { learner: { email: state.email } } }),
}));
vi.mock("@/lib/client/api", () => ({ apiJson: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock("@/lib/client/navigation", () => ({
  useNavigationCheck: () => async () => true,
}));
vi.mock("@/components/study/StudyPracticePart", () => ({
  PracticePart: function PracticePart() {
    const [draft, setDraft] = useState("");
    return (
      <input aria-label="Hoofdoefening" value={draft} onChange={(event) => setDraft(event.target.value)} />
    );
  },
}));

const word: StudyWord = {
  id: "a2-word-komen",
  term: "komen",
  part_of_speech: "verb",
  meaning: { nl: "ergens aankomen", en: "to come" },
  example: { nl: "Ik kom morgen.", en: "I am coming tomorrow." },
  forms: [
    { label: { nl: "Nu", en: "Now" }, text: { nl: "Ik kom.", en: "I am coming." } },
    { label: { nl: "Gisteren", en: "Yesterday" }, text: { nl: "Ik kwam.", en: "I came." } },
  ],
  contexts: [
    {
      id: "visit",
      setting: { nl: "Bij een vriend", en: "Visiting a friend" },
      sentence: { nl: "Ik kom zaterdag bij jou.", en: "I am coming to see you on Saturday." },
      production_prompt: {
        nl: "Vertel wanneer je op bezoek komt.",
        en: "Say when you are coming to visit.",
      },
    },
    {
      id: "class",
      setting: { nl: "Naar de les", en: "Going to class" },
      sentence: { nl: "Ik kom met de bus naar de les.", en: "I come to class by bus." },
      production_prompt: {
        nl: "Vertel hoe je naar de les komt.",
        en: "Say how you get to class.",
      },
    },
  ],
};

beforeEach(() => {
  state.english = true;
  state.email = "learner-one@example.test";
  vi.mocked(apiJson).mockReset();
});
afterEach(() => vi.restoreAllMocks());

async function openTransfer() {
  await userEvent.click(screen.getByText("Gebruik in een andere situatie"));
  return screen.getByRole("textbox", { name: /Jouw zin met/ });
}

test("compact cards reveal authored forms and let the learner try before the context example", async () => {
  const storage = vi.spyOn(Storage.prototype, "setItem");
  const view = render(<CompactWords words={[word]} />);
  expect(screen.getByText("Ik kom morgen.")).toBeVisible();
  expect(screen.getByText("Gisteren")).not.toBeVisible();
  expect(view.container.querySelector("details")).not.toHaveAttribute("open");
  const input = await openTransfer();
  expect(screen.getByRole("button", { name: "Luister: Ik kwam." })).toBeVisible();
  expect(screen.getByText("Bij een vriend")).toBeVisible();
  expect(screen.queryByText("Ik kom zaterdag bij jou.")).not.toBeInTheDocument();
  await userEvent.type(input, "Ik kom zondag.");
  await userEvent.tab();
  expect(screen.getByRole("button", { name: /Toon een mogelijk voorbeeld/ })).toHaveFocus();
  await userEvent.keyboard("{Enter}");
  expect(screen.getByRole("button", { name: "Luister: Ik kom zaterdag bij jou." })).toBeVisible();
  expect(input).toHaveValue("Ik kom zondag.");
  expect(screen.getByText("Your practice sentence is not saved or assessed.")).toBeVisible();
  expect(screen.queryByText(/beheerst|geslaagd|score/)).not.toBeInTheDocument();
  expect(storage).not.toHaveBeenCalled();
  expect(apiJson).not.toHaveBeenCalled();
});

test("another situation clears the attempt and reveal while keeping keyboard navigation available", async () => {
  render(<CompactWords words={[word]} />);
  const input = await openTransfer();
  await userEvent.type(input, "Ik kom zondag.");
  await userEvent.click(screen.getByRole("button", { name: /Toon een mogelijk voorbeeld/ }));
  const next = screen.getByRole("button", { name: /Volgende situatie/ });
  next.focus();
  await userEvent.keyboard("{Enter}");
  expect(next).toHaveFocus();
  expect(screen.getByText("Naar de les")).toBeVisible();
  expect(screen.getByRole("textbox", { name: /Jouw zin met/ })).toHaveValue("");
  expect(screen.queryByText("Ik kom met de bus naar de les.")).not.toBeInTheDocument();
  await userEvent.click(next);
  expect(screen.getByText("Bij een vriend")).toBeVisible();
  expect(screen.getByRole("textbox", { name: /Jouw zin met/ })).toHaveValue("");
});

test("word-set and activity scopes discard scratch state even when the retained word ID is unchanged", async () => {
  const view = render(<CompactWords words={[word]} resetKey="a2:story-one:learner-one" />);
  await userEvent.type(await openTransfer(), "Ik kom zondag.");
  view.rerender(<CompactWords words={[word]} resetKey="a2:story-two:learner-one" />);
  expect(await openTransfer()).toHaveValue("");
  await userEvent.type(screen.getByRole("textbox"), "Ik kom maandag.");
  view.rerender(
    <CompactWords
      words={[
        word,
        { id: "a2-word-gaan", term: "gaan", meaning: { nl: "bewegen" }, example: { nl: "Ik ga." } },
      ]}
      resetKey="a2:story-two:learner-one"
    />,
  );
  expect(await openTransfer()).toHaveValue("");
  await userEvent.type(screen.getByRole("textbox"), "Ik kom dinsdag.");
  view.unmount();
  render(<CompactWords words={[word]} resetKey="a2:story-two:learner-one" />);
  expect(await openTransfer()).toHaveValue("");
});

test("only a persisted pageshow clears scratch and revealed examples", async () => {
  render(<CompactWords words={[word]} />);
  await userEvent.type(await openTransfer(), "Ik kom zondag.");
  await userEvent.click(screen.getByRole("button", { name: /Toon een mogelijk voorbeeld/ }));
  act(() => window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: false })));
  expect(screen.getByRole("textbox")).toHaveValue("Ik kom zondag.");
  act(() => window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true })));
  expect(await openTransfer()).toHaveValue("");
  expect(screen.queryByText("Ik kom zaterdag bij jou.")).not.toBeInTheDocument();
});

test("Dutch-only hides English without clearing the attempt when support is switched back on", async () => {
  state.english = false;
  const view = render(<CompactWords words={[word]} />);
  await userEvent.type(await openTransfer(), "Ik kom zondag.");
  await userEvent.click(screen.getByRole("button", { name: "Toon een mogelijk voorbeeld" }));
  expect(screen.queryByText("I am coming to see you on Saturday.")).not.toBeInTheDocument();
  state.english = true;
  view.rerender(<CompactWords words={[word]} />);
  expect(screen.getByText("I am coming to see you on Saturday.")).toHaveAttribute("lang", "en");
  expect(screen.getByRole("textbox")).toHaveValue("Ik kom zondag.");
});

test("missing authored prompts show examples without inventing tasks, while empty enrichment stays absent", async () => {
  const view = render(
    <WordTransferPractice
      word={{ ...word, forms: [], contexts: [{ ...word.contexts![0], production_prompt: undefined }] }}
    />,
  );
  await userEvent.click(screen.getByText("Gebruik in een andere situatie"));
  expect(screen.getByRole("button", { name: "Luister: Ik kom zaterdag bij jou." })).toBeVisible();
  expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  expect(screen.queryByText("Toon een mogelijk voorbeeld")).not.toBeInTheDocument();
  view.rerender(<WordTransferPractice word={{ ...word, forms: [], contexts: [] }} />);
  expect(view.container).toBeEmptyDOMElement();
});

test("a noun with only an authored plural can expand to its plural label and Dutch audio", async () => {
  const noun: StudyWord = {
    id: "a1-word-tafel",
    term: "de tafel",
    part_of_speech: "noun",
    meaning: { nl: "een meubel met een blad en poten", en: "a table" },
    example: { nl: "De tafel staat hier.", en: "The table is here." },
    plural: "tafels",
    forms: [],
    contexts: [],
  };
  render(<WordTransferPractice word={noun} />);
  expect(screen.getByText("Meervoud")).not.toBeVisible();
  await userEvent.click(screen.getByText("Bekijk andere woordvormen"));
  expect(screen.getByText("Meervoud")).toBeVisible();
  expect(screen.getByText("Plural")).toBeVisible();
  expect(screen.getByRole("button", { name: "Luister: tafels" })).toBeVisible();
  expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  expect(screen.queryByText("Gebruik in een andere situatie")).not.toBeInTheDocument();
});

test("an existing authored plural form is not duplicated, and missing plurals stay absent", async () => {
  const view = render(
    <WordTransferPractice
      word={{
        ...word,
        plural: " tafels ",
        contexts: [],
        forms: [{ label: { nl: "Meervoud", en: "Plural" }, text: { nl: "tafels", en: "tables" } }],
      }}
    />,
  );
  await userEvent.click(screen.getByText("Bekijk andere woordvormen"));
  expect(screen.getAllByText("Meervoud")).toHaveLength(1);
  expect(screen.getAllByRole("button", { name: "Luister: tafels" })).toHaveLength(1);
  expect(screen.getByText("tables")).toBeVisible();
  view.rerender(<WordTransferPractice word={{ ...word, plural: " ", forms: [], contexts: [] }} />);
  expect(view.container).toBeEmptyDOMElement();
  view.rerender(<WordTransferPractice word={{ ...word, plural: null, forms: [], contexts: [] }} />);
  expect(view.container).toBeEmptyDOMElement();
});

test("the word reference clears its scratch when the signed-in identity changes", async () => {
  vi.mocked(apiJson).mockResolvedValue({ items: [word], offset: 0, limit: 18, total: 1 });
  const view = render(<WordReference stageId="a2" />);
  await screen.findByText("Gebruik in een andere situatie");
  await userEvent.type(await openTransfer(), "Ik kom zondag.");
  state.email = "learner-two@example.test";
  view.rerender(<WordReference stageId="a2" />);
  await screen.findByText("Gebruik in een andere situatie");
  expect(await openTransfer()).toHaveValue("");
});

test("guided activity and identity keys reset word practice and the main ephemeral activity", async () => {
  const lesson: StudyLesson = {
    stage_id: "a2",
    skill: "reading",
    topic_id: "friends",
    title: { nl: "Een bezoek" },
    review_status: "unreviewed",
    activity_id: "visit-one",
    preparation: { words: [word], grammar: [] },
    activities: [{ id: "visit-one", title: { nl: "Een bezoek" } }],
    parts: [
      {
        id: "retell",
        title: { nl: "Vertel" },
        instructions: { nl: "Vertel." },
        prompt: { nl: "Wie komt?" },
        sample: null,
        text: [],
        questions: [],
        min_words: 1,
        max_words: 20,
      },
    ],
    policy: { ephemeral: true, pronunciation_assessed: false },
  };
  vi.mocked(apiJson).mockResolvedValue(lesson);
  const props = {
    stageId: "a2",
    skill: "reading" as const,
    topicId: "friends",
    activityId: "visit-one",
    initialStep: "practise" as const,
  };
  const view = render(<GuidedLesson {...props} />);
  await userEvent.type(await screen.findByRole("textbox", { name: "Hoofdoefening" }), "Mijn eerste antwoord");
  await userEvent.click(screen.getByRole("button", { name: /Woorden erbij/ }));
  await userEvent.type(await openTransfer(), "Ik kom zondag.");
  state.email = "learner-two@example.test";
  view.rerender(<GuidedLesson {...props} />);
  expect(screen.getByRole("textbox", { name: "Hoofdoefening" })).toHaveValue("");
  expect(await openTransfer()).toHaveValue("");
  await userEvent.type(screen.getByRole("textbox", { name: "Hoofdoefening" }), "Tweede antwoord");
  view.rerender(<GuidedLesson {...props} activityId="visit-two" />);
  await waitFor(() => expect(screen.getByRole("textbox", { name: "Hoofdoefening" })).toHaveValue(""));
  expect(await openTransfer()).toHaveValue("");
});
