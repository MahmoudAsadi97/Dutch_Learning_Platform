import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { GrammarPractice } from "@/components/GrammarPractice";
import type { CurriculumStage } from "@/lib/client/curriculum";

vi.mock("@/components/LanguageSupport", () => ({
  LearningText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));
vi.mock("@/components/PhraseAudio", () => ({
  PhraseAudio: ({ label }: { label?: string }) => <button>{label ?? "Afspelen"}</button>,
}));
vi.mock("@/components/SpokenPassage", () => ({
  SpokenText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));
vi.mock("@/components/CurriculumControls", () => ({
  CurriculumQuestions: ({ questions }: { questions: { id: string }[] }) => (
    <div>
      {questions.map((q) => (
        <p key={q.id}>{q.id}</p>
      ))}
    </div>
  ),
}));
const topics: CurriculumStage["grammar"] = ["first", "second"].map((id) => ({
  id: `practice-${id}`,
  title: { nl: id, en: id, fa: id },
  explanation: { nl: "Regel", en: "Rule", fa: "قاعده" },
  examples: [{ nl: "Ik woon in Gent.", en: "I live in Ghent.", fa: "من در خنت زندگی می‌کنم." }],
  practice: Array.from({ length: 10 }, (_, n) => ({
    id: `${id}-${n}`,
    prompt: { nl: "Vraag", en: "Question", fa: "پرسش" },
    options: [
      { nl: "is", en: "is", fa: "is" },
      { nl: "ben", en: "ben", fa: "ben" },
    ],
    answer_index: 0,
    explanation: { nl: "Uitleg", en: "Reason", fa: "توضیح" },
  })),
}));

test("only the selected round appears; checking requires all ten answers", async () => {
  const onCheck = vi.fn();
  const props = { topics, answers: {}, onAnswer: vi.fn(), checked: {}, onCheck, onPractice: vi.fn() };
  const { rerender } = render(<GrammarPractice {...props} />);
  expect(screen.getByText("first-0")).toBeVisible();
  expect(screen.queryByText("second-0")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Controleer deze ronde" })).toBeDisabled();
  const answers = Object.fromEntries(topics[0].practice.map((q) => [q.id, 0]));
  rerender(<GrammarPractice {...props} answers={answers} />);
  await userEvent.click(screen.getByRole("button", { name: "Controleer deze ronde" }));
  expect(onCheck).toHaveBeenCalledWith("practice-first");
  await userEvent.selectOptions(screen.getByLabelText("Kies een onderwerp"), "practice-second");
  expect(screen.getByText("second-0")).toBeVisible();
  expect(screen.queryByText("first-0")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Controleer deze ronde" })).toBeDisabled();
});

test("listen first conceals the example and each skill is reachable", async () => {
  const onPractice = vi.fn();
  render(
    <GrammarPractice
      topics={topics}
      answers={{}}
      onAnswer={vi.fn()}
      checked={{}}
      onCheck={vi.fn()}
      onPractice={onPractice}
    />,
  );
  await userEvent.click(screen.getByRole("checkbox"));
  expect(screen.queryByText("Ik woon in Gent.")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Luister naar voorbeeld 1" })).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Toon de voorbeeldzin" }));
  expect(screen.getByText("Ik woon in Gent.")).toBeVisible();
  for (const [label, skill] of [
    ["Lezen", "reading"],
    ["Luisteren", "listening"],
    ["Spreken", "speaking"],
    ["Schrijven", "writing"],
  ]) {
    await userEvent.click(screen.getByRole("button", { name: label }));
    expect(onPractice).toHaveBeenLastCalledWith(skill);
  }
});
