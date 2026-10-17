import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { StoryTime } from "@/components/LearningLibrary";
import { apiJson } from "@/lib/client/api";

vi.mock("@/lib/client/api", () => ({ apiJson: vi.fn() }));
vi.mock("@/components/PhraseAudio", () => ({
  PhraseAudio: ({ text }: { text: string }) => <button aria-label={`Luister: ${text}`}>Luister</button>,
}));
vi.mock("@/components/LanguageSupport", () => ({
  LearningText: ({ text, supportOnly }: { text?: { nl: string; en?: string }; supportOnly?: boolean }) =>
    text ? (
      <span>
        {!supportOnly && text.nl}
        {text.en && <span lang="en">{text.en}</span>}
      </span>
    ) : null,
}));
vi.mock("@/components/StoryPractice", () => ({ StoryPractice: () => <section>Gebruik de woorden</section> }));
vi.mock("@/components/CurriculumControls", () => ({ CurriculumQuestions: () => <div>Begripsvraag</div> }));

const lines = [
  "Sara staat bij de deur.",
  "Zij heeft een brief.",
  "De brief is voor Omar.",
  "Omar is in de tuin.",
  "Sara roept zijn naam.",
  "Omar komt naar de deur.",
  "Hij leest de brief.",
  "Het is een uitnodiging.",
];
function fixture(authoredLines: boolean) {
  return {
    id: "a1-s021",
    title: { nl: "De brief" },
    topic: { nl: "Vriendschap" },
    preview: { nl: lines[0] },
    word_count: 42,
    paragraph_count: 2,
    paragraphs: [{ nl: lines.slice(0, 4).join(" ") }, { nl: lines.slice(4).join(" ") }],
    ...(authoredLines ? { lines: lines.map((nl, i) => ({ nl, en: `Translation line ${i + 1}` })) } : {}),
    vocabulary: [],
    question: {
      id: "a1-q021",
      prompt: { nl: "Wat staat er in de brief?" },
      options: [{ nl: "Een uitnodiging" }, { nl: "Een prijs" }],
    },
  };
}

beforeEach(() => {
  vi.mocked(apiJson).mockReset();
  localStorage.clear();
});

function mockLibrary(authoredLines: boolean, highlightNew = false) {
  const story = fixture(authoredLines);
  vi.mocked(apiJson).mockImplementation(async (path) => {
    if (path === "library/a1")
      return {
        stage_id: "a1",
        learner_key: "learner",
        story_count: 200,
        vocabulary_count: 500,
        topics: highlightNew
          ? [
              {
                key: "Verhaal naar gesprek",
                label: { nl: "Verhaal naar gesprek" },
                vocabulary_count: 4,
                story_count: 2,
              },
            ]
          : [],
        ...(highlightNew ? { authored_story_count: 2, target_story_count: 200 } : {}),
      };
    if (String(path).startsWith("library/a1/stories?"))
      return { items: [story], total: 200, offset: 0, limit: 12 };
    if (path === "library/a1/stories/a1-s021") return story;
    throw new Error(`Unexpected request: ${path}`);
  });
}

test("authored lines stay explicit with individual audio and optional translation", async () => {
  mockLibrary(true);
  render(<StoryTime stageId="a1" />);
  await userEvent.click(await screen.findByRole("button", { name: "Lees De brief" }));
  const authored = await screen.findByRole("list", { name: "Regels van het verhaal" });
  expect(within(authored).getAllByRole("listitem")).toHaveLength(8);
  expect(within(authored).getAllByRole("button")).toHaveLength(8);
  expect(screen.queryByText("Translation line 1")).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Vertaling tonen" }));
  expect(screen.getByText("Translation line 1")).toBeVisible();
  expect(within(authored).getAllByRole("listitem")).toHaveLength(8);
  await userEvent.click(screen.getByRole("button", { name: "Markeer als gelezen" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Gelezen" })).toBeDisabled());
});

test("legacy paragraphs remain readable without pretending they have authored line metadata", async () => {
  mockLibrary(false);
  render(<StoryTime stageId="a1" />);
  await userEvent.click(await screen.findByRole("button", { name: "Lees De brief" }));
  const story = await screen.findByRole("article", { name: "Leesverhaal" });
  expect(within(story).getAllByRole("button")).toHaveLength(8);
  expect(screen.queryByRole("list", { name: "Regels van het verhaal" })).not.toBeInTheDocument();
});

test("new authored stories open first and the learner can still choose all topics", async () => {
  mockLibrary(true, true);
  render(<StoryTime stageId="a1" />);
  await screen.findByRole("button", { name: "Lees De brief" });
  await waitFor(() =>
    expect(screen.getByRole("combobox", { name: "Onderwerp" })).toHaveValue("Verhaal naar gesprek"),
  );
  expect(
    vi.mocked(apiJson).mock.calls.some(([path]) => String(path).includes("topic=Verhaal+naar+gesprek")),
  ).toBe(true);
  await userEvent.selectOptions(screen.getByRole("combobox", { name: "Onderwerp" }), "");
  await waitFor(() => expect(screen.getByRole("combobox", { name: "Onderwerp" })).toHaveValue(""));
  expect(screen.getByText("2 nieuwe verhalen met korte regels en gebruiksoefeningen")).toBeVisible();
  expect(screen.queryByText("200 nieuwe verhalen")).not.toBeInTheDocument();
});
