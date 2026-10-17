import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { WordLibrary } from "@/components/LearningLibrary";
import { apiJson } from "@/lib/client/api";

vi.mock("@/lib/client/api", () => ({ apiJson: vi.fn() }));
vi.mock("@/components/PhraseAudio", () => ({
  PhraseAudio: ({ text }: { text: string }) => <button aria-label={`Luister: ${text}`}>Luister</button>,
}));
vi.mock("@/components/LanguageSupport", () => ({
  LearningText: ({ text }: { text?: { nl: string } }) => (text ? <span>{text.nl}</span> : null),
}));

const copy = (nl: string) => ({ nl, en: nl, fa: nl });
beforeEach(() => {
  vi.mocked(apiJson).mockReset();
});

test("the productive core is discoverable, preserves all cards and resets unrelated topic filters", async () => {
  const requests: string[] = [];
  vi.mocked(apiJson).mockImplementation(async (path) => {
    const value = String(path);
    requests.push(value);
    if (value === "library/a1")
      return {
        stage_id: "a1",
        learner_key: "core-reader",
        vocabulary_count: 510,
        story_count: 120,
        productive_core_count: 150,
        topics: [
          {
            key: "Eten",
            label: copy("Eten"),
            vocabulary_count: 40,
            story_count: 4,
            productive_core_count: 20,
          },
          {
            key: "Overig",
            label: copy("Overig"),
            vocabulary_count: 12,
            story_count: 2,
            productive_core_count: 0,
          },
        ],
      };
    if (value.startsWith("library/a1/vocabulary?")) {
      const params = new URLSearchParams(value.split("?")[1]);
      const isCore = params.get("core_only") === "true";
      return {
        total: isCore ? 150 : 510,
        offset: 0,
        limit: 20,
        items: [
          {
            id: "a1-v1",
            term: "helpen",
            topic: copy("Eten"),
            meaning: copy("Iemand iets laten lukken."),
            example: copy("Ik help mijn buur."),
            productive_core: isCore,
          },
        ],
      };
    }
    throw new Error(`Unexpected request: ${value}`);
  });
  render(<WordLibrary stageId="a1" />);
  await screen.findByRole("heading", { name: "150 woorden om zelf te gebruiken" });
  await waitFor(() => expect(screen.getByText("1–20 van 150")).toBeVisible());
  expect(screen.queryByRole("option", { name: "Overig" })).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Bekijk alle woordkaarten" }));
  await waitFor(() => expect(screen.getByText("1–20 van 510")).toBeVisible());
  expect(screen.getByRole("option", { name: "Overig" })).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByRole("combobox", { name: "Onderwerp" }), "Eten");
  await userEvent.click(screen.getByRole("button", { name: "Oefen de 150 kernwoorden" }));
  await waitFor(() => expect(screen.getByText("1–20 van 150")).toBeVisible());
  expect(screen.getByRole("combobox", { name: "Onderwerp" })).toHaveValue("");
  expect(screen.getByRole("button", { name: "Bekijk alle woordkaarten" })).not.toHaveAttribute(
    "aria-pressed",
  );
  expect(requests.some((path) => path.includes("core_only=true"))).toBe(true);
  await userEvent.click(screen.getByRole("button", { name: "Bekijk alle woordkaarten" }));
  await waitFor(() => expect(screen.getByText("1–20 van 510")).toBeVisible());
  expect(screen.getByRole("button", { name: "Oefen de 150 kernwoorden" })).not.toHaveAttribute(
    "aria-pressed",
  );
});
