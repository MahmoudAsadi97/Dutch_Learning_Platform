import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";

import { StudyActivityPicker } from "@/components/study/StudyActivityPicker";

vi.mock("@/components/LanguageSupport", () => ({
  LearningText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));

const activities = Array.from({ length: 14 }, (_, index) => ({
  id: `story-${index + 1}`,
  title: {
    nl: index === 12 ? "Het café bij de brug" : `Verhaal ${index + 1}`,
    en: index === 12 ? "The quiet river" : `Story ${index + 1}`,
  },
}));

test("story search and paging keep the chooser compact and reset after a new query", async () => {
  const choose = vi.fn().mockResolvedValue(true);
  render(<StudyActivityPicker activities={activities} selected="story-1" onChoose={choose} />);
  await userEvent.click(screen.getByRole("button", { expanded: false }));
  const panel = screen.getByRole("region", { name: "Verhalen in dit onderwerp" });
  expect(within(panel).getAllByRole("listitem")).toHaveLength(6);
  await userEvent.click(within(panel).getByRole("button", { name: /Volgende/ }));
  expect(within(panel).getByRole("button", { name: "Verhaal 7" })).toBeVisible();
  const search = within(panel).getByRole("searchbox", { name: "Zoek een verhaal…" });
  await userEvent.type(search, "quiet river");
  expect(within(panel).getAllByRole("listitem")).toHaveLength(1);
  expect(within(panel).getByRole("button", { name: "Het café bij de brug" })).toBeVisible();
  await userEvent.clear(search);
  expect(within(panel).getByRole("button", { name: "Verhaal 1" })).toBeVisible();
  await userEvent.type(search, "CAFE");
  await userEvent.click(within(panel).getByRole("button", { name: "Het café bij de brug" }));
  expect(choose).toHaveBeenCalledExactlyOnceWith("story-13");
  expect(screen.queryByRole("region")).not.toBeInTheDocument();
});

test("a declined leave guard keeps the selected story and chooser in place", async () => {
  const choose = vi.fn().mockResolvedValue(false);
  render(<StudyActivityPicker activities={activities} selected="story-1" onChoose={choose} />);
  await userEvent.click(screen.getByRole("button", { expanded: false }));
  await userEvent.click(screen.getByRole("button", { name: "Verhaal 2" }));
  expect(choose).toHaveBeenCalledExactlyOnceWith("story-2");
  expect(screen.getByRole("button", { name: "Verhaal 1" })).toHaveAttribute("aria-current", "true");
  expect(screen.getByRole("region")).toBeVisible();
});

test("the picker opens on the current story's page and Escape restores trigger focus", async () => {
  render(<StudyActivityPicker activities={activities} selected="story-13" onChoose={vi.fn()} />);
  const trigger = screen.getByRole("button", { expanded: false });
  await userEvent.click(trigger);
  expect(screen.getByRole("button", { name: "Het café bij de brug" })).toHaveAttribute(
    "aria-current",
    "true",
  );
  const search = screen.getByRole("searchbox");
  await userEvent.click(search);
  await userEvent.keyboard("{Escape}");
  expect(trigger).toHaveFocus();
  expect(trigger).toHaveAttribute("aria-expanded", "false");
});
