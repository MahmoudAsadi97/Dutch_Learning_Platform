import { StrictMode } from "react";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import { CurriculumQuestions } from "@/components/CurriculumControls";
import { ExerciseSession } from "@/components/exercise/ExerciseSession";
import { ApiError } from "@/lib/client/api";
import type { AnswerResult, Completion, SessionView, Summary } from "@/lib/client/exercises";
import { exerciseCopy } from "@/lib/copy/exercise";

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

const passageText = { nl: "Sam wacht op de bus. De bus is laat." };
const question = (id: string, position: number, nl: string, first: string, second: string) => ({
  id,
  position,
  kind: "choice" as const,
  skill: "reading",
  state: "open" as const,
  attempts_left: 2,
  prompt: {
    kind: "choice" as const,
    direction: "question" as const,
    stem: { nl, en: `${nl} (en)` },
    options: [
      { id: `${id}a`, nl: first },
      { id: `${id}b`, nl: second },
    ],
  },
  feedback: null,
});

function topicSession(skill: "reading" | "listening" | "writing" = "reading"): SessionView {
  const passage =
    skill === "reading"
      ? {
          kind: "read_passage" as const,
          text: passageText,
          vocabulary: [{ term: "de bus", meaning: { en: "the bus" } }],
        }
      : { kind: "listen_passage" as const, parts: 1, transcript: null, vocabulary: [] };
  const items =
    skill === "writing"
      ? [{ ...question("w1", 0, "Wat betekent 'de bus'?", "the bus", "the train"), skill: "" }]
      : [
          {
            id: "p",
            position: 0,
            kind: passage.kind,
            skill,
            state: "open" as const,
            attempts_left: 1,
            prompt: passage,
            feedback: null,
          },
          question("q1", 1, "Waar wacht Sam?", "Thuis", "Aan de halte"),
          question("q2", 2, "Wat is laat?", "De bus", "De trein"),
        ];
  return {
    id: "s1",
    source: "topic",
    stage_id: "pre-a1",
    focus: "words",
    library_topic: null,
    topic_id: "pre-a1-t001",
    skill,
    retry: false,
    status: "active",
    content_status: "unreviewed",
    resumed: false,
    items,
    next_item_id: items[0].id,
    progress: { closed: 0, total: items.length - (skill === "writing" ? 0 : 1), queued: 0 },
    summary: null,
  };
}

function verdict(itemId: string, next: string | null, overrides: Partial<AnswerResult> = {}): AnswerResult {
  return {
    item_id: itemId,
    attempt: 1,
    outcome: "correct",
    closed: true,
    requeue: false,
    attempts_left: 0,
    feedback: { outcome: "correct", correct: `${itemId}b`, given: `${itemId}b` },
    points: 1,
    progress: { closed: 1, total: 2, queued: 0 },
    next_item_id: next,
    ...overrides,
  };
}

function summary(completion: Partial<Completion> = {}): Summary {
  return {
    items_total: 2,
    answered: 2,
    first_try_correct: 2,
    fixed_on_retry: 0,
    skipped: 0,
    overridden: 0,
    points_earned: 2,
    session_bonus: 0,
    by_kind: {},
    missed: [],
    suggestions: [],
    completion: {
      scope: "topic",
      skill: "reading",
      topic_id: "pre-a1-t001",
      counted: true,
      reason: null,
      passed: true,
      correct: 2,
      total: 2,
      required: 2,
      completed: true,
      to_retry: 0,
      ...completion,
    },
  };
}

function wire(finished: Summary = summary()) {
  client.answer.mockImplementation(async (_session: string, item: string) =>
    item === "p"
      ? verdict("p", "q1", { outcome: "done", points: 0, feedback: { outcome: "done" } })
      : verdict(item, item === "q1" ? "q2" : null, {
          progress: { closed: item === "q1" ? 1 : 2, total: 2, queued: 0 },
        }),
  );
  client.finish.mockResolvedValue({ id: "s1", status: "finished", points: 0, summary: finished });
  const revealed = topicSession();
  revealed.status = "finished";
  revealed.items[0] = {
    ...revealed.items[0],
    state: "closed",
    prompt: { kind: "read_passage", text: { ...passageText, en: "Sam waits for the bus." }, vocabulary: [] },
  };
  client.get.mockResolvedValue(revealed);
}

const exit = {
  label: { nl: "Kies een ander onderwerp", en: "Choose another topic", fa: "موضوع دیگر" },
  onExit: vi.fn(),
};

function topic(skill: "reading" | "listening" | "writing" = "reading", extra = {}) {
  return (
    <ExerciseSession
      source="topic"
      stageId="pre-a1"
      topicId="pre-a1-t001"
      skill={skill}
      headingLevel={4}
      embedded={exit}
      {...extra}
    />
  );
}

async function answerBoth() {
  fireEvent.click(await screen.findByRole("button", { name: /Naar de vragen/ }));
  for (const [heading, option] of [
    ["Waar wacht Sam?", /Aan de halte/],
    ["Wat is laat?", /De trein/],
  ] as const) {
    await screen.findByText(heading);
    fireEvent.click(screen.getByRole("radio", { name: option }));
    fireEvent.click(screen.getByRole("button", { name: /Controleer/ }));
    fireEvent.click(await screen.findByRole("button", { name: /^Verder/ }));
  }
}

beforeEach(() => {
  vi.clearAllMocks();
  client.create.mockResolvedValue(topicSession());
  wire();
});

describe("a session inside a practice topic", () => {
  it("reads the passage, keeps it beside each question, and reports what counted", async () => {
    const onFinished = vi.fn();
    const onActivityChange = vi.fn();
    render(topic("reading", { onFinished, onActivityChange }));
    const passageHeading = await screen.findByRole("heading", { level: 4, name: /Lees eerst de tekst/ });
    expect(client.create.mock.calls[0][0]).toEqual({
      source: "topic",
      stage_id: "pre-a1",
      topic_id: "pre-a1-t001",
      skill: "reading",
      kinds: expect.arrayContaining(["choice"]),
    });
    // inside a topic: no page title or second honesty chip; the passage in Dutch only
    expect(screen.queryByRole("heading", { level: 1 })).not.toBeInTheDocument();
    expect(document.querySelector("[data-honesty]")).toBeNull();
    await waitFor(() => expect(passageHeading).toHaveFocus());
    const text = document.querySelector(".exercise-passage-text");
    expect(text).toHaveTextContent("Sam wacht op de bus.");
    expect(text?.querySelector("[lang=en]")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /Naar de vragen/ }));
    expect(client.answer).toHaveBeenCalledWith("s1", "p", { done: true }, expect.any(String), false);
    const first = await screen.findByRole("heading", { level: 4, name: /Kies het juiste antwoord/ });
    await waitFor(() => expect(first).toHaveFocus());
    // the passage stays, the same node, now as a reference above the question
    expect(document.querySelector(".exercise-passage-text")).toBe(text);
    expect(document.querySelector(".exercise-passage")).toHaveAttribute("data-mode", "reference");
    // the question's own gloss helps; the options' glosses wait for the answer
    expect(screen.getByText("Waar wacht Sam? (en)")).toBeInTheDocument();
    // the question is part of the group's name, as the old form's legend was (its Dutch, not its play button)
    expect(
      screen.getByRole("group", { name: /^Kies het juiste antwoord.* Waar wacht Sam\?$/ }),
    ).toBeInTheDocument();
    expect(document.querySelector(".answer-option .exercise-meaning")).toBeNull();

    fireEvent.click(screen.getByRole("radio", { name: /Aan de halte/ }));
    fireEvent.click(screen.getByRole("button", { name: /Controleer/ }));
    fireEvent.click(await screen.findByRole("button", { name: /^Verder/ }));
    await screen.findByText("Wat is laat?");
    fireEvent.click(screen.getByRole("radio", { name: /De trein/ }));
    fireEvent.click(screen.getByRole("button", { name: /Controleer/ }));
    fireEvent.click(await screen.findByRole("button", { name: /^Verder/ }));
    await screen.findByRole("heading", { level: 4, name: /Je oefening is klaar/ });
    expect(onFinished).toHaveBeenCalledTimes(1);
    expect(onFinished.mock.calls[0][0].completion.completed).toBe(true);
    expect(screen.getByText(exerciseCopy.completionPassed.nl)).toBeInTheDocument();
    expect(document.querySelector(".summary-completion")).toHaveAttribute("data-state", "done");
    // read again, now with its translation on request
    await waitFor(() => expect(client.get).toHaveBeenCalledWith("s1"));
    const translate = await screen.findByRole("button", { name: /Vertaling tonen/ });
    fireEvent.click(translate);
    // an action that says what it does, not a toggle whose state and name contradict each other
    expect(screen.getByRole("button", { name: /Vertaling verbergen/ })).not.toHaveAttribute("aria-pressed");
    expect(
      within(document.querySelector(".summary-passage") as HTMLElement).getByText("Sam waits for the bus."),
    ).toBeInTheDocument();
    // the host's own way out leads on; nothing links to Today
    expect(screen.queryByRole("link", { name: /Vandaag/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Kies een ander onderwerp/ }));
    expect(exit.onExit).toHaveBeenCalledTimes(1);
  });

  it("reads the passage again after finishing also in StrictMode", async () => {
    render(<StrictMode>{topic()}</StrictMode>);
    await answerBoth();
    await screen.findByRole("button", { name: /Vertaling tonen/ });
  });

  it("takes Escape only inside the session, and the way out is the host's", async () => {
    render(topic());
    fireEvent.click(await screen.findByRole("button", { name: /Naar de vragen/ }));
    const heading = await screen.findByRole("heading", { name: /Kies het juiste antwoord/ });
    act(() => {
      fireEvent.keyDown(document.body, { key: "Escape" });
    });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    act(() => {
      fireEvent.keyDown(heading, { key: "Escape" });
    });
    const dialog = await screen.findByRole("dialog", { name: /Stoppen met oefenen/ });
    expect(dialog).toHaveTextContent(exerciseCopy.exitLeadActivity.nl);
    expect(within(dialog).queryByRole("link")).not.toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole("button", { name: /Kies een ander onderwerp/ }));
    expect(exit.onExit).toHaveBeenCalledTimes(1);
  });

  it("offers the missed questions again, which asks with retry; with nothing left, all questions again", async () => {
    wire(summary({ passed: false, completed: false, correct: 1, to_retry: 1 }));
    render(topic());
    await answerBoth();
    const retry = await screen.findByRole("button", { name: /Oefen de gemiste vragen/ });
    const actions = retry.closest(".exercise-actions") as HTMLElement;
    expect(within(actions).getAllByRole("button")[0]).toBe(retry);
    expect(screen.getByText(exerciseCopy.completionRuleAll.nl)).toBeInTheDocument();
    expect(document.querySelector(".summary-completion")).toHaveAttribute("data-state", "open");
    client.create.mockRejectedValueOnce(new ApiError(409, "nothing", "r", "nothing_to_retry"));
    fireEvent.click(retry);
    await waitFor(() => expect(client.create).toHaveBeenCalledTimes(2));
    const [body, id] = client.create.mock.calls[1];
    expect(body).toMatchObject({ source: "topic", retry: true });
    expect(id).not.toBe(client.create.mock.calls[0][1]);
    await screen.findByText(/geen gemiste vraag meer/);
    // the button that started it has gone: the notice takes the focus, next to its way on
    await waitFor(() => expect(document.querySelector(".exercise-load-error")).toHaveFocus());
    fireEvent.click(screen.getByRole("button", { name: /Doe alle vragen opnieuw/ }));
    await waitFor(() => expect(client.create).toHaveBeenCalledTimes(3));
    expect(client.create.mock.calls[2][0]).not.toHaveProperty("retry");
  });

  it("says in a retry that stopping keeps the answers and that the round does not count", async () => {
    wire(summary({ passed: false, completed: false, correct: 1, to_retry: 1 }));
    render(topic());
    await answerBoth();
    fireEvent.click(await screen.findByRole("button", { name: /Oefen de gemiste vragen/ }));
    await waitFor(() => expect(client.create).toHaveBeenCalledTimes(2));
    fireEvent.click(await screen.findByRole("button", { name: /Naar de vragen/ }));
    const heading = await screen.findByRole("heading", { name: /Kies het juiste antwoord/ });
    act(() => {
      fireEvent.keyDown(heading, { key: "Escape" });
    });
    const dialog = await screen.findByRole("dialog", { name: /Stoppen met oefenen/ });
    expect(dialog).toHaveTextContent(exerciseCopy.exitLeadRetry.nl);
    expect(dialog).not.toHaveTextContent(/later verdergaan/);
  });

  it("keeps the host busy only while the session is being closed, not while an answer is checked", async () => {
    const onActivityChange = vi.fn();
    let finish: (value: unknown) => void = () => {};
    client.finish.mockReturnValue(new Promise((resolve) => (finish = resolve)));
    const { unmount } = render(topic("reading", { onActivityChange }));
    await answerBoth();
    await waitFor(() => expect(onActivityChange).toHaveBeenLastCalledWith(true));
    expect(onActivityChange.mock.calls.filter(([busy]) => busy)).toHaveLength(1);
    await act(async () => finish({ id: "s1", status: "finished", points: 0, summary: summary() }));
    await waitFor(() => expect(onActivityChange).toHaveBeenLastCalledWith(false));
    unmount();
    expect(onActivityChange).toHaveBeenLastCalledWith(false);
  });

  it("hears a listening passage from the topic's own route, and lets it pass when sound cannot play", async () => {
    client.create.mockResolvedValue(topicSession("listening"));
    client.skip.mockResolvedValue(
      verdict("p", "q1", { outcome: "done", points: 0, feedback: { outcome: "done" } }),
    );
    render(topic("listening"));
    await screen.findByRole("heading", { level: 4, name: /Luister eerst naar het fragment/ });
    expect(screen.getByRole("button", { name: /Luister naar het fragment/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Ik kan nu niet luisteren/ }));
    expect(client.skip).toHaveBeenCalledWith("s1", "p", expect.any(String), "no_audio");
    await screen.findByText("Waar wacht Sam?");
  });

  it("ends a warm-up with the way to the task", async () => {
    client.create.mockResolvedValue(topicSession("writing"));
    client.answer.mockResolvedValue(verdict("w1", null, { progress: { closed: 1, total: 1, queued: 0 } }));
    client.finish.mockResolvedValue({
      id: "s1",
      status: "finished",
      points: 0,
      summary: summary({
        skill: "writing",
        counted: false,
        reason: "open_task",
        passed: null,
        completed: false,
      }),
    });
    const toTask = { label: { nl: "Naar de opdracht", en: "To the task", fa: "تکلیف" }, onExit: vi.fn() };
    render(topic("writing", { embedded: toTask }));
    fireEvent.click(await screen.findByRole("radio", { name: /the bus/ }));
    fireEvent.click(screen.getByRole("button", { name: /Controleer/ }));
    fireEvent.click(await screen.findByRole("button", { name: /^Verder/ }));
    await screen.findByText(exerciseCopy.completionWarmUp.nl);
    const first = (
      document.querySelector(".exercise-summary .exercise-actions") as HTMLElement
    ).querySelector("button");
    expect(first).toHaveTextContent(/Naar de opdracht/);
    fireEvent.click(first as HTMLElement);
    expect(toTask.onExit).toHaveBeenCalledTimes(1);
    expect(client.get).not.toHaveBeenCalled();
  });
});

describe("CurriculumQuestions", () => {
  const questions = [
    {
      id: "q1",
      prompt: { nl: "Waar wacht Sam?", en: "Where does Sam wait?" },
      options: [
        { nl: "Thuis", en: "At home" },
        { nl: "Aan de halte", en: "At the stop" },
      ],
      answer_index: 1,
    },
  ];

  it("keeps an option's gloss for after the check, and the exam Dutch only", () => {
    const { rerender } = render(
      <CurriculumQuestions questions={questions} answers={{}} onAnswer={() => {}} />,
    );
    expect(screen.queryByText("At home")).not.toBeInTheDocument();
    expect(screen.getByText("Where does Sam wait?")).toBeInTheDocument();
    rerender(<CurriculumQuestions questions={questions} answers={{ q1: 1 }} onAnswer={() => {}} checked />);
    expect(screen.getByText("At home")).toBeInTheDocument();
    rerender(
      <CurriculumQuestions questions={questions} answers={{ q1: 1 }} onAnswer={() => {}} exam checked />,
    );
    expect(screen.queryByText("At home")).not.toBeInTheDocument();
    expect(screen.queryByText("Where does Sam wait?")).not.toBeInTheDocument();
  });
});
