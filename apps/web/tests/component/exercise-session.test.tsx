import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import { ChoiceItem } from "@/components/exercise/ChoiceItem";
import { ExerciseSession } from "@/components/exercise/ExerciseSession";
import { AnswerOption } from "@/components/ui/AnswerOption";
import type { AnswerResult, SessionView } from "@/lib/client/exercises";

const client = vi.hoisted(() => ({
  create: vi.fn(),
  get: vi.fn(),
  answer: vi.fn(),
  skip: vi.fn(),
  report: vi.fn(),
  finish: vi.fn(),
}));
vi.mock("@/lib/client/exercises", () => ({ exercises: client }));

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    if (!this.hasAttribute("open")) return;
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
  window.matchMedia ??= ((query: string) => ({
    matches: false,
    media: query,
    addEventListener() {},
    removeEventListener() {},
  })) as unknown as typeof window.matchMedia;
});

const options = [
  { id: "aaaa", nl: "de deur" },
  { id: "bbbb", nl: "het raam" },
  { id: "cccc", nl: "de sleutel" },
  { id: "dddd", nl: "de trap" },
];
const support = options.map((option, index) => ({ ...option, en: `gloss ${index}`, fa: "" }));

function session(overrides: Partial<SessionView> = {}): SessionView {
  return {
    id: "s1",
    source: "stage_skill",
    stage_id: "a1",
    focus: "words",
    library_topic: null,
    status: "active",
    content_status: "unreviewed",
    resumed: false,
    items: [
      {
        id: "intro",
        position: 0,
        kind: "intro",
        skill: "",
        state: "open",
        attempts_left: 2,
        prompt: {
          kind: "intro",
          words: [{ term: "de deur", meaning: { en: "the door" }, example: { nl: "De deur is open." } }],
        },
        feedback: null,
      },
      {
        id: "i1",
        position: 1,
        kind: "choice",
        skill: "vocabulary",
        state: "open",
        attempts_left: 2,
        prompt: { kind: "choice", direction: "term", stem: { en: "the window" }, options },
        feedback: null,
      },
    ],
    next_item_id: "intro",
    progress: { closed: 0, total: 1, queued: 0 },
    summary: null,
    ...overrides,
  };
}

function result(overrides: Partial<AnswerResult>): AnswerResult {
  return {
    item_id: "i1",
    attempt: 1,
    outcome: "incorrect",
    closed: true,
    requeue: false,
    attempts_left: 0,
    feedback: { outcome: "incorrect", correct: "bbbb", given: "aaaa", support },
    points: 1,
    progress: { closed: 1, total: 1, queued: 0 },
    next_item_id: null,
    ...overrides,
  };
}

describe("AnswerOption", () => {
  it("shows its state in words and an icon, and is read-only after the verdict", () => {
    const { rerender } = render(
      <AnswerOption name="q" value="a" checked onSelect={() => {}}>
        de deur
      </AnswerOption>,
    );
    const radio = screen.getByRole("radio", { name: /de deur/ });
    expect(radio.closest("label")).toHaveAttribute("data-state", "selected");
    expect(radio).toBeEnabled();
    rerender(
      <AnswerOption name="q" value="a" checked onSelect={() => {}} verdict="incorrect">
        de deur
      </AnswerOption>,
    );
    expect(screen.getByRole("radio", { name: /de deur Jouw antwoord/ })).toBeDisabled();
    rerender(
      <AnswerOption name="q" value="a" checked={false} onSelect={() => {}} verdict="reveal">
        de deur
      </AnswerOption>,
    );
    expect(screen.getByRole("radio", { name: /Het juiste antwoord/ }).closest("label")).toHaveAttribute(
      "data-state",
      "reveal",
    );
  });
});

describe("ChoiceItem", () => {
  it("shows Dutch options without glosses before the answer and their meanings after it", () => {
    const prompt = { kind: "choice", direction: "term", stem: { en: "the window" }, options } as const;
    const { rerender } = render(
      <ChoiceItem prompt={prompt} selected={null} onSelect={() => {}} feedback={null} />,
    );
    expect(screen.getAllByRole("radio")).toHaveLength(4);
    expect(screen.queryByText("gloss 1")).not.toBeInTheDocument();
    expect(screen.getByText("het raam")).toHaveAttribute("lang", "nl");
    rerender(
      <ChoiceItem
        prompt={prompt}
        selected="aaaa"
        onSelect={() => {}}
        feedback={{ outcome: "incorrect", correct: "bbbb", given: "aaaa", support }}
      />,
    );
    expect(screen.getByText("gloss 1")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /het raam/ }).closest("label")).toHaveAttribute(
      "data-state",
      "reveal",
    );
  });
});

describe("ExerciseSession", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.create.mockResolvedValue(session());
    client.answer.mockImplementation(async (_session: string, item: string) =>
      item === "intro"
        ? result({
            item_id: "intro",
            outcome: "done",
            points: 0,
            next_item_id: "i1",
            feedback: { outcome: "done" },
          })
        : result({}),
    );
    client.finish.mockResolvedValue({
      id: "s1",
      status: "finished",
      points: 0,
      summary: {
        items_total: 1,
        answered: 1,
        first_try_correct: 0,
        fixed_on_retry: 0,
        skipped: 0,
        overridden: 0,
        points_earned: 1,
        session_bonus: 0,
        by_kind: {},
        missed: [{ ref: "word:1", term: "het raam", expected: "het raam" }],
        suggestions: [],
      },
    });
  });

  it("runs from the intro card through an answer chosen by key to the summary", async () => {
    render(<ExerciseSession source="stage_skill" />);
    const start = await screen.findByRole("button", { name: /Begin met oefenen/ });
    expect(client.create).toHaveBeenCalledWith(
      expect.objectContaining({ source: "stage_skill", kinds: ["choice", "cloze_choice", "odd_one_out"] }),
      expect.any(String),
    );
    fireEvent.click(start);
    await screen.findByRole("heading", { name: /Welk Nederlands woord past/ });
    expect(document.activeElement).toHaveTextContent(/Welk Nederlands woord past/);

    act(() => {
      fireEvent.keyDown(document.body, { key: "2" });
    });
    expect(screen.getByRole("radio", { name: /het raam/ })).toBeChecked();
    act(() => {
      fireEvent.keyDown(document.body, { key: "Enter" });
    });
    const next = await screen.findByRole("button", { name: /^Verder/ });
    expect(client.answer).toHaveBeenLastCalledWith("s1", "i1", { option: "bbbb" }, expect.any(String));
    await waitFor(() => expect(next).toHaveFocus());
    const feedback = screen.getByRole("region", { name: /Nog niet/ });
    expect(within(feedback).getByText(/\+1 punt/)).toBeInTheDocument();

    fireEvent.click(next);
    await screen.findByRole("heading", { name: /Je oefening is klaar/ });
    expect(client.finish).toHaveBeenCalledWith("s1", expect.any(String), false);
    expect(screen.getByText("het raam")).toBeInTheDocument();
  });

  it("asks before stopping, and finishing early closes the session", async () => {
    render(<ExerciseSession source="while_you_wait" />);
    fireEvent.click(await screen.findByRole("button", { name: /Begin met oefenen/ }));
    await screen.findByRole("heading", { name: /Welk Nederlands woord past/ });
    act(() => {
      fireEvent.keyDown(document.body, { key: "Escape" });
    });
    const dialog = await screen.findByRole("dialog", { name: /Stoppen met oefenen/ });
    fireEvent.click(within(dialog).getByRole("button", { name: /Rond nu af/ }));
    await screen.findByRole("heading", { name: /Je oefening is klaar/ });
    expect(client.finish).toHaveBeenCalledWith("s1", expect.any(String), true);
  });

  it("asks for a missed item again, in the order the server reshuffled it", async () => {
    client.answer.mockImplementation(async (_session: string, item: string) =>
      item === "intro"
        ? result({
            item_id: "intro",
            outcome: "done",
            points: 0,
            next_item_id: "i1",
            feedback: { outcome: "done" },
          })
        : result({
            closed: false,
            requeue: true,
            attempts_left: 1,
            next_item_id: "i1",
            progress: { closed: 0, total: 1, queued: 1 },
          }),
    );
    const reshuffled = session({ next_item_id: "i1", progress: { closed: 0, total: 1, queued: 1 } });
    reshuffled.items[0] = { ...reshuffled.items[0], state: "closed" };
    reshuffled.items[1] = {
      ...reshuffled.items[1],
      attempts_left: 1,
      prompt: {
        kind: "choice",
        direction: "term",
        stem: { en: "the window" },
        options: [...options].reverse(),
      },
    };
    client.get.mockResolvedValue(reshuffled);
    render(<ExerciseSession source="stage_skill" />);
    fireEvent.click(await screen.findByRole("button", { name: /Begin met oefenen/ }));
    fireEvent.click(await screen.findByRole("radio", { name: /de deur/ }));
    fireEvent.click(screen.getByRole("button", { name: /Controleer/ }));
    expect(await screen.findByText(/komt aan het einde nog één keer terug/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^Verder/ }));
    await waitFor(() => expect(client.get).toHaveBeenCalledWith("s1"));
    await waitFor(() => expect(screen.getAllByRole("radio")[0]).toHaveAccessibleName(/de trap/));
    expect(screen.getAllByRole("radio").every((radio) => !(radio as HTMLInputElement).checked)).toBe(true);
  });

  it("sends a failed answer again under the same request id", async () => {
    client.answer.mockImplementation(async (_session: string, item: string) => {
      if (item === "intro")
        return result({
          item_id: "intro",
          outcome: "done",
          points: 0,
          next_item_id: "i1",
          feedback: { outcome: "done" },
        });
      throw new TypeError("network");
    });
    render(<ExerciseSession source="stage_skill" />);
    fireEvent.click(await screen.findByRole("button", { name: /Begin met oefenen/ }));
    fireEvent.click(await screen.findByRole("radio", { name: /de trap/ }));
    fireEvent.click(screen.getByRole("button", { name: /Controleer/ }));
    const again = await screen.findByRole("button", { name: /Verstuur opnieuw/ });
    fireEvent.click(again);
    await waitFor(() => expect(client.answer).toHaveBeenCalledTimes(3));
    const ids = client.answer.mock.calls.filter((call) => call[1] === "i1").map((call) => call[3]);
    expect(ids[0]).toBe(ids[1]);
  });
});
