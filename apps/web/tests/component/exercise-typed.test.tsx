import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";

import { ExerciseSession } from "@/components/exercise/ExerciseSession";
import { ShadowItem } from "@/components/exercise/ShadowItem";
import { TypedItem } from "@/components/exercise/TypedItem";
import type { AnswerResult, SessionView } from "@/lib/client/exercises";

const client = vi.hoisted(() => ({
  create: vi.fn(),
  get: vi.fn(),
  answer: vi.fn(),
  skip: vi.fn(),
  override: vi.fn(),
  report: vi.fn(),
  finish: vi.fn(),
  audio: vi.fn(),
  record: vi.fn(),
}));
vi.mock("@/lib/client/exercises", () => ({ exercises: client }));

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    this.removeAttribute("open");
  };
  window.matchMedia ??= ((query: string) => ({
    matches: false,
    media: query,
    addEventListener() {},
    removeEventListener() {},
  })) as unknown as typeof window.matchMedia;
});

const recall = { kind: "typed_recall", cue: { en: "the house" }, hint: { first: "h", length: 4 } } as const;

describe("TypedItem", () => {
  it("is a Dutch field the device leaves alone, with a hint on request and Enter to check", () => {
    const onDraft = vi.fn();
    const onHint = vi.fn();
    const onSubmit = vi.fn();
    render(
      <TypedItem
        prompt={recall}
        sessionId="s1"
        itemId="i1"
        feedback={null}
        onDraft={onDraft}
        onHint={onHint}
        onSubmit={onSubmit}
      />,
    );
    const field = screen.getByRole("textbox", { name: /Jouw antwoord/ });
    expect(field).toHaveAttribute("lang", "nl");
    expect(field).toHaveAttribute("autocapitalize", "off");
    expect(field).toHaveAttribute("autocorrect", "off");
    expect(field).toHaveAttribute("spellcheck", "false");
    expect(field).toHaveAttribute("autocomplete", "off");
    fireEvent.change(field, { target: { value: "het huis" } });
    expect(onDraft).toHaveBeenLastCalledWith({ text: "het huis" });
    fireEvent.change(field, { target: { value: "  " } });
    expect(onDraft).toHaveBeenLastCalledWith(null);
    fireEvent.click(screen.getByRole("button", { name: /Toon een hint/ }));
    expect(onHint).toHaveBeenCalledOnce();
    expect(screen.getByText(/Het begint met h en heeft 4 letters/)).toBeInTheDocument();
    fireEvent.keyDown(field, { key: "Enter" });
    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it("shows what was typed against the answer, word by word, and what the check forgave", () => {
    render(
      <TypedItem
        prompt={recall}
        sessionId="s1"
        itemId="i1"
        feedback={{
          outcome: "almost",
          typed: "het hius",
          expected: "het huis",
          notes: ["spelling"],
          diff: [
            { op: "same", expected: "het", given: "het" },
            { op: "changed", expected: "huis", given: "hius" },
          ],
        }}
        onDraft={() => {}}
        onHint={() => {}}
        onSubmit={() => {}}
      />,
    );
    expect(screen.getByRole("textbox", { name: /Jouw antwoord/ })).toHaveAttribute("readonly");
    expect(screen.getByRole("deletion")).toHaveTextContent(/jij typte:.*hius/);
    expect(screen.getByRole("insertion")).toHaveTextContent(/juist:.*huis/);
    expect(screen.getByText("Een kleine tikfout.")).toBeInTheDocument();
  });
});

describe("ShadowItem", () => {
  it("says when the browser cannot record, and shows the words heard without a score", () => {
    const { rerender } = render(
      <ShadowItem
        prompt={{ kind: "shadow", sentence: "Ik woon in Gent." }}
        sessionId="s1"
        itemId="i1"
        feedback={null}
        busy={false}
        onRecording={() => {}}
      />,
    );
    // jsdom has no MediaRecorder
    expect(screen.getByText(/Deze browser kan niet opnemen/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Luister/ })).toBeInTheDocument();
    rerender(
      <ShadowItem
        prompt={{ kind: "shadow", sentence: "Ik woon in Gent." }}
        sessionId="s1"
        itemId="i1"
        feedback={{ outcome: "heard", transcript: "ik woon in gent", matched_words: 4, target_words: 4 }}
        busy={false}
        onRecording={() => {}}
      />,
    );
    expect(screen.getByText(/Wat we hoorden/).closest("p")).toHaveTextContent("ik woon in gent");
    expect(document.body.textContent).not.toMatch(/4\s*\/\s*4|score|%/);
  });
});

function typedSession(): SessionView {
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
        id: "t1",
        position: 0,
        kind: "typed_recall",
        skill: "vocabulary",
        state: "open",
        attempts_left: 2,
        prompt: recall,
        feedback: null,
      },
    ],
    next_item_id: "t1",
    progress: { closed: 0, total: 1, queued: 0 },
    summary: null,
  };
}

describe("ExerciseSession with a typed answer", () => {
  it("sends the hint with the answer, and the learner may say the answer is right too", async () => {
    client.create.mockResolvedValue(typedSession());
    const verdict = (overrides: Partial<AnswerResult>): AnswerResult => ({
      item_id: "t1",
      attempt: 1,
      outcome: "incorrect",
      closed: false,
      requeue: true,
      attempts_left: 1,
      feedback: { outcome: "incorrect", typed: "de woning", expected: "het huis", overridable: true },
      points: 1,
      progress: { closed: 0, total: 1, queued: 1 },
      next_item_id: "t1",
      ...overrides,
    });
    client.answer.mockResolvedValue(verdict({}));
    client.override.mockResolvedValue(
      verdict({
        outcome: "accepted",
        closed: true,
        requeue: false,
        attempts_left: 0,
        feedback: { outcome: "accepted", typed: "de woning", expected: "het huis", overridable: false },
        progress: { closed: 1, total: 1, queued: 0 },
        next_item_id: null,
      }),
    );
    render(<ExerciseSession source="stage_skill" />);
    const field = await screen.findByRole("textbox", { name: /Jouw antwoord/ });
    fireEvent.click(screen.getByRole("button", { name: /Toon een hint/ }));
    fireEvent.change(field, { target: { value: "de woning" } });
    fireEvent.keyDown(field, { key: "Enter" });
    await screen.findByRole("region", { name: /Nog niet/ });
    expect(client.answer).toHaveBeenLastCalledWith(
      "s1",
      "t1",
      { text: "de woning" },
      expect.any(String),
      true,
    );
    fireEvent.click(screen.getByRole("button", { name: /Mijn antwoord klopt ook/ }));
    await screen.findByRole("region", { name: /Je antwoord telt/ });
    expect(client.override).toHaveBeenCalledWith("s1", "t1", expect.any(String));
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: /Mijn antwoord klopt ook/ })).not.toBeInTheDocument(),
    );
  });
});
