import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { PracticePart } from "@/components/study/StudyPracticePart";
import { apiJson } from "@/lib/client/api";
import type { StudyFeedback, StudyLesson, StudyPart } from "@/lib/client/study";
import type { Recording } from "@/lib/client/recorder";

const recorder = vi.hoisted(() => ({
  callback: null as ((recording: Recording) => Promise<void>) | null,
  start: vi.fn(),
  stop: vi.fn(),
}));
vi.mock("@/lib/client/api", () => ({
  apiJson: vi.fn(),
  apiFetch: vi.fn(),
  ApiError: class extends Error {},
}));
vi.mock("@/components/LanguageSupport", () => ({
  LearningText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));
vi.mock("@/components/SpokenPassage", () => ({
  SpokenText: ({ text }: { text: { nl: string } }) => (
    <span>
      <span lang="nl">{text.nl}</span>
      <button aria-label={`Luister: ${text.nl}`} />
    </span>
  ),
}));
vi.mock("@/components/PhraseAudio", () => ({
  PhraseAudio: ({ text }: { text: string }) => <button aria-label={`Luister: ${text}`} />,
}));
vi.mock("@/lib/client/recorder", () => ({
  STOP_TAIL_MS: 400,
  useRecorder: (callback: (recording: Recording) => Promise<void>) => {
    recorder.callback = callback;
    return { phase: "idle", error: null, start: recorder.start, stop: recorder.stop };
  },
}));
vi.mock("@/lib/client/navigation", () => ({ useNavigationGuard: () => vi.fn() }));
vi.mock("@/lib/client/audio-focus", () => ({ observeNativeAudioFocus: () => vi.fn() }));

const original = "Ik woont in Gent.";
const corrected = "Ik woon in Gent.";
const review: StudyFeedback = {
  status: "evaluated",
  score: 5,
  dimensions: { task: 6, grammar: 3, vocabulary: 6, organisation: 5, pronunciation: null },
  summary: { nl: "Je woonplaats is duidelijk. Bekijk de werkwoordsvorm." },
  corrections: [
    {
      original: "Ik woont",
      replacement: "Ik woon",
      category: "grammar",
      explanation: { nl: "Gebruik bij ik de stam.", en: "Use the stem with ik." },
    },
  ],
  corrected_text: corrected,
  checks: [],
  pronunciation_note: { nl: "Uitspraak is niet beoordeeld." },
  ephemeral: true,
};
const part: StudyPart = {
  id: "write-short",
  title: { nl: "Schrijf een antwoord" },
  instructions: { nl: "Vertel waar je woont." },
  prompt: { nl: "Waar woon je?" },
  sample: null,
  text: [],
  questions: [],
  min_words: 1,
  max_words: 100,
};
function lesson(skill: StudyLesson["skill"] = "writing", stage = "a1", task = part): StudyLesson {
  return {
    stage_id: stage,
    topic_id: "housing",
    skill,
    title: { nl: "Een woonplaats" },
    review_status: "unreviewed",
    preparation: { words: [], grammar: [] },
    activities: [{ id: "housing-scene", title: { nl: "Een woonplaats" } }],
    activity_id: "housing-scene",
    parts: [task],
    policy: { ephemeral: true, pronunciation_assessed: false },
  };
}
function show(skill: StudyLesson["skill"] = "writing", stage = "a1", task = part) {
  const onAssisted = vi.fn();
  return {
    ...render(
      <PracticePart
        lesson={lesson(skill, stage, task)}
        part={task}
        mode="check"
        assisted={false}
        onAssisted={onAssisted}
        onNext={vi.fn()}
      />,
    ),
    onAssisted,
  };
}
async function checkDraft(draft = original) {
  await userEvent.type(screen.getByRole("textbox"), draft);
  await userEvent.click(screen.getByRole("button", { name: "Bekijk mijn feedback" }));
  await screen.findByRole("region", { name: "Tijdelijke oefenfeedback" });
}
beforeEach(() => {
  vi.mocked(apiJson).mockReset();
  recorder.start.mockReset();
  recorder.stop.mockReset();
  recorder.callback = null;
  Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn(() => "blob:voice") });
  Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
});

test("the complete grounded suggestion is opt-in, audible, and never replaces the learner's text", async () => {
  vi.mocked(apiJson).mockResolvedValue(review);
  const { onAssisted } = show();
  await checkDraft();
  expect(screen.queryByTestId("study-corrected-draft")).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Toon je tekst met deze correcties" }));
  const suggestion = screen.getByTestId("study-corrected-draft");
  expect(within(suggestion).getByText(corrected)).toBeVisible();
  expect(within(suggestion).getByRole("button", { name: `Luister: ${corrected}` })).toBeVisible();
  expect(screen.getByRole("textbox")).toHaveValue(original);
  expect(onAssisted).toHaveBeenCalledOnce();
  expect(apiJson).toHaveBeenCalledOnce();
});

test.each([
  ["writing", "pre-a1", "write-short"],
  ["speaking", "b2", "describe"],
  ["reading", "c2", "retell"],
] as const)("%s at %s keeps feedback beside an editable aided revision", async (skill, stage, id) => {
  vi.mocked(apiJson).mockResolvedValue(review);
  const { onAssisted, container } = show(skill, stage, { ...part, id });
  await checkDraft();
  await userEvent.click(screen.getByRole("button", { name: "Verbeter mijn antwoord" }));
  const editor = screen.getByRole("textbox");
  expect(editor).toHaveFocus();
  expect(editor).toHaveValue(original);
  const reference = screen.getByRole("complementary", { name: "Feedback op je vorige versie" });
  expect(within(reference).getByText("Gebruik bij ik de stam.")).toBeVisible();
  expect(within(reference).getByText("5/10")).toBeVisible();
  expect(container.querySelector(".study-score")).toBeNull();
  expect(screen.queryByRole("region", { name: "Tijdelijke oefenfeedback" })).not.toBeInTheDocument();
  await userEvent.clear(editor);
  await userEvent.type(editor, corrected);
  expect(apiJson).toHaveBeenCalledOnce();
  expect(onAssisted).toHaveBeenCalled();
  await userEvent.click(screen.getByRole("button", { name: "Bekijk mijn feedback" }));
  await screen.findByRole("region", { name: "Tijdelijke oefenfeedback" });
  expect(apiJson).toHaveBeenLastCalledWith(
    expect.stringContaining(`study/${stage}/`),
    expect.objectContaining({
      body: expect.objectContaining({ text: corrected, skill, assistance_used: true, kind: "response" }),
    }),
  );
  expect(screen.getByText("Feedback op je herwerkte antwoord · met hulp")).toBeVisible();
});

test("editing directly invalidates a current mark while retaining the reference feedback", async () => {
  vi.mocked(apiJson).mockResolvedValue(review);
  const { container } = show();
  await checkDraft();
  await userEvent.type(screen.getByRole("textbox"), " Mijn broer ook.");
  expect(container.querySelector(".study-score")).toBeNull();
  expect(screen.getByRole("complementary", { name: "Feedback op je vorige versie" })).toBeVisible();
  expect(apiJson).toHaveBeenCalledOnce();
});

test("a failed explicit recheck keeps the revised draft and the previous corrections", async () => {
  vi.mocked(apiJson).mockResolvedValueOnce(review).mockRejectedValueOnce(new Error("Unavailable"));
  show();
  await checkDraft();
  await userEvent.click(screen.getByRole("button", { name: "Verbeter mijn antwoord" }));
  await userEvent.clear(screen.getByRole("textbox"));
  await userEvent.type(screen.getByRole("textbox"), corrected);
  await userEvent.click(screen.getByRole("button", { name: "Bekijk mijn feedback" }));
  await screen.findByRole("alert");
  expect(screen.getByRole("textbox")).toHaveValue(corrected);
  expect(screen.getByText("Gebruik bij ik de stam.")).toBeVisible();
  expect(screen.queryByRole("region", { name: "Tijdelijke oefenfeedback" })).not.toBeInTheDocument();
  expect(apiJson).toHaveBeenCalledTimes(2);
});

test("the first draft survives repeated revisions and all comparison data clears on unmount", async () => {
  const secondDraft = "Ik woon in Gent. Mijn broer woont ook in Gent.";
  vi.mocked(apiJson)
    .mockResolvedValueOnce(review)
    .mockResolvedValueOnce({ ...review, score: 8, corrected_text: secondDraft, corrections: [] });
  const view = show();
  await checkDraft();
  await userEvent.click(screen.getByRole("button", { name: "Verbeter mijn antwoord" }));
  await userEvent.clear(screen.getByRole("textbox"));
  await userEvent.type(screen.getByRole("textbox"), secondDraft);
  await userEvent.click(screen.getByRole("button", { name: "Bekijk mijn feedback" }));
  await screen.findByRole("region", { name: "Tijdelijke oefenfeedback" });
  await userEvent.click(screen.getByRole("button", { name: "Verbeter mijn antwoord" }));
  await userEvent.click(screen.getByText("Vergelijk met je eerste versie"));
  expect(screen.getByText(original)).toBeVisible();
  await userEvent.click(screen.getByText("Bekijk je vorige versie"));
  expect(within(screen.getByRole("complementary")).getByText(secondDraft)).toBeVisible();
  expect(screen.getByText("8/10")).toBeVisible();
  view.unmount();
  show();
  expect(screen.getByRole("textbox")).toHaveValue("");
  expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  expect(screen.queryByText(original)).not.toBeInTheDocument();
});

test("recording a new spoken version keeps previous feedback and does not auto-evaluate its transcript", async () => {
  vi.mocked(apiJson)
    .mockResolvedValueOnce(review)
    .mockResolvedValueOnce({ transcript: { text: corrected } })
    .mockResolvedValueOnce({ ...review, score: 8, corrected_text: corrected, corrections: [] });
  recorder.start.mockImplementation(() =>
    recorder.callback?.({ blob: new Blob(["voice"]), mimeType: "audio/wav", fileName: "recording.wav" }),
  );
  show("speaking", "c1", { ...part, id: "describe" });
  await checkDraft();
  await userEvent.click(screen.getByRole("button", { name: "Neem je antwoord op" }));
  await waitFor(() => expect(screen.getByRole("textbox")).toHaveValue(corrected));
  expect(screen.getByRole("complementary")).toBeVisible();
  expect(screen.queryByRole("region", { name: "Tijdelijke oefenfeedback" })).not.toBeInTheDocument();
  expect(apiJson).toHaveBeenCalledTimes(2);
  expect(vi.mocked(apiJson).mock.calls[1][0]).toContain("/transcribe");
  await userEvent.click(screen.getByRole("button", { name: "Bekijk mijn feedback" }));
  await screen.findByRole("region", { name: "Tijdelijke oefenfeedback" });
  expect(apiJson).toHaveBeenLastCalledWith(
    expect.any(String),
    expect.objectContaining({ body: expect.objectContaining({ text: corrected, assistance_used: true }) }),
  );
});

test("restoring a page from the browser cache clears private drafts and revision feedback", async () => {
  vi.mocked(apiJson).mockResolvedValue(review);
  show();
  await checkDraft();
  await userEvent.click(screen.getByRole("button", { name: "Verbeter mijn antwoord" }));
  const restore = new Event("pageshow");
  Object.defineProperty(restore, "persisted", { value: true });
  act(() => window.dispatchEvent(restore));
  expect(screen.getByRole("textbox")).toHaveValue("");
  expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  expect(screen.queryByRole("region", { name: "Tijdelijke oefenfeedback" })).not.toBeInTheDocument();
});

test("a late recheck cannot restore private feedback after a cached page is reset", async () => {
  let finish!: (value: StudyFeedback) => void;
  vi.mocked(apiJson)
    .mockResolvedValueOnce(review)
    .mockImplementationOnce(
      () =>
        new Promise<StudyFeedback>((resolve) => {
          finish = resolve;
        }),
    );
  show();
  await checkDraft();
  await userEvent.click(screen.getByRole("button", { name: "Verbeter mijn antwoord" }));
  await userEvent.type(screen.getByRole("textbox"), " Mijn broer ook.");
  await userEvent.click(screen.getByRole("button", { name: "Bekijk mijn feedback" }));
  const request = vi.mocked(apiJson).mock.calls[1][1];
  const restore = new Event("pageshow");
  Object.defineProperty(restore, "persisted", { value: true });
  act(() => window.dispatchEvent(restore));
  expect(request?.signal?.aborted).toBe(true);
  await act(async () => finish(review));
  expect(screen.getByRole("textbox")).toHaveValue("");
  expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  expect(screen.queryByRole("region", { name: "Tijdelijke oefenfeedback" })).not.toBeInTheDocument();
});

test("a response without grounded changes offers no invented corrected version", async () => {
  vi.mocked(apiJson).mockResolvedValue({ ...review, corrected_text: null, corrections: [] });
  show();
  await checkDraft();
  expect(screen.queryByRole("button", { name: "Toon je tekst met deze correcties" })).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Verbeter mijn antwoord" }));
  expect(screen.queryByRole("button", { name: "Toon je tekst met deze correcties" })).not.toBeInTheDocument();
  expect(screen.getByRole("textbox")).toHaveValue(original);
});

test("objective answers retain their original flow and never open draft revision", async () => {
  const objective = {
    ...part,
    id: "read",
    questions: [{ id: "where", kind: "choice" as const, prompt: { nl: "Waar?" }, options: [{ nl: "Gent" }] }],
  };
  vi.mocked(apiJson).mockResolvedValue({ ...review, corrections: [], corrected_text: null });
  show("reading", "a2", objective);
  await userEvent.click(screen.getByRole("radio"));
  await userEvent.click(screen.getByRole("button", { name: "Bekijk mijn feedback" }));
  await screen.findByRole("region", { name: "Tijdelijke oefenfeedback" });
  await userEvent.click(screen.getByRole("button", { name: "Verbeter mijn antwoord" }));
  expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  expect(screen.getByRole("radio")).toBeChecked();
  expect(apiJson).toHaveBeenLastCalledWith(
    expect.any(String),
    expect.objectContaining({ body: expect.objectContaining({ kind: "answers", answers: { where: 0 } }) }),
  );
});
