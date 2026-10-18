import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { PracticePart } from "@/components/study/StudyPracticePart";
import { apiJson } from "@/lib/client/api";
import type { StudyFeedback, StudyLesson, StudyPart } from "@/lib/client/study";

vi.mock("@/lib/client/api", () => ({
  apiJson: vi.fn(),
  apiFetch: vi.fn(),
  ApiError: class extends Error {},
}));
vi.mock("@/components/LanguageSupport", () => ({
  LearningText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));
vi.mock("@/components/SpokenPassage", () => ({
  SpokenText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));
vi.mock("@/components/PhraseAudio", () => ({ PhraseAudio: () => null }));
vi.mock("@/lib/client/recorder", () => ({
  useRecorder: () => ({ phase: "idle", error: null, start: vi.fn(), stop: vi.fn() }),
}));
vi.mock("@/lib/client/navigation", () => ({ useNavigationGuard: () => vi.fn() }));
vi.mock("@/lib/client/audio-focus", () => ({ observeNativeAudioFocus: () => vi.fn() }));

const part: StudyPart = {
  id: "short-answer",
  title: { nl: "Luister en antwoord" },
  instructions: { nl: "Geef de dag." },
  prompt: { nl: "Wanneer spreken ze af?" },
  sample: null,
  text: [],
  questions: [{ id: "day", kind: "short", prompt: { nl: "Op welke dag?" }, options: [] }],
  min_words: 1,
  max_words: 10,
};
const lesson: StudyLesson = {
  stage_id: "a1",
  topic_id: "friends",
  skill: "listening",
  title: { nl: "Een afspraak" },
  review_status: "unreviewed",
  preparation: { words: [], grammar: [] },
  activities: [{ id: "friends-scene", title: { nl: "Een afspraak" } }],
  activity_id: "friends-scene",
  parts: [part],
  policy: { ephemeral: true, pronunciation_assessed: false },
};
const reference: StudyFeedback = {
  status: "needs_review",
  score: null,
  dimensions: { task: null, grammar: null, vocabulary: null, organisation: null, pronunciation: null },
  summary: { nl: "Vergelijk je antwoord." },
  corrections: [],
  checks: [
    {
      id: "day",
      correct: null,
      review_required: true,
      answer: { nl: "Woensdag" },
      explanation: { nl: "Een andere formulering vraagt beoordeling." },
    },
  ],
  pronunciation_note: { nl: "Geen uitspraakscore." },
  ephemeral: true,
};
const reviewed: StudyFeedback = {
  ...reference,
  status: "evaluated",
  score: 8,
  checks: [],
  summary: { nl: "De dag is begrijpelijk genoemd." },
};

beforeEach(() => vi.mocked(apiJson).mockReset());

function showPart() {
  render(
    <PracticePart
      lesson={lesson}
      part={part}
      mode="check"
      assisted={false}
      onAssisted={vi.fn()}
      onNext={vi.fn()}
    />,
  );
}

test("unkeyed free answers request one semantic review only after an explicit action", async () => {
  vi.mocked(apiJson).mockResolvedValueOnce(reference).mockResolvedValueOnce(reviewed);
  showPart();
  await userEvent.type(screen.getByRole("textbox"), "Op woensdag");
  expect(apiJson).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Bekijk mijn feedback" }));
  expect(await screen.findByText("Vergelijk met het voorbeeld")).toBeVisible();
  expect(apiJson).toHaveBeenCalledTimes(1);
  await userEvent.click(screen.getByRole("button", { name: "Beoordeel mijn antwoord" }));
  expect(await screen.findByText("Begripsfeedback voor vraag 1")).toBeVisible();
  expect(apiJson).toHaveBeenCalledTimes(2);
  expect(apiJson).toHaveBeenLastCalledWith(
    expect.stringContaining("/feedback"),
    expect.objectContaining({
      method: "POST",
      body: expect.objectContaining({
        kind: "response",
        question_id: "day",
        text: "Op woensdag",
        activity_id: "friends-scene",
        part: "short-answer",
      }),
    }),
  );
  expect(screen.getByText(/geen score voor de volledige oefening/)).toBeVisible();
  await userEvent.type(screen.getByRole("textbox"), " in de namiddag");
  expect(screen.queryByText("Begripsfeedback voor vraag 1")).not.toBeInTheDocument();
  expect(apiJson).toHaveBeenCalledTimes(2);
});

test("repeated clicks cannot dispatch duplicate reviews while the request is pending", async () => {
  let finish!: (value: StudyFeedback) => void;
  vi.mocked(apiJson)
    .mockResolvedValueOnce(reference)
    .mockImplementationOnce(
      () =>
        new Promise<StudyFeedback>((resolve) => {
          finish = resolve;
        }),
    );
  showPart();
  await userEvent.type(screen.getByRole("textbox"), "Woensdagmiddag");
  await userEvent.click(screen.getByRole("button", { name: "Bekijk mijn feedback" }));
  const action = await screen.findByRole("button", { name: "Beoordeel mijn antwoord" });
  await userEvent.dblClick(action);
  await waitFor(() => expect(apiJson).toHaveBeenCalledTimes(2));
  expect(action).toBeDisabled();
  finish(reviewed);
  expect(await screen.findByText("Begripsfeedback voor vraag 1")).toBeVisible();
});
