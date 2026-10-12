import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { AlignmentPanel } from "@/components/AlignmentPanel";
import { ExamPreparation } from "@/components/ExamPreparation";
import { apiJson } from "@/lib/client/api";

vi.mock("@/lib/client/api", () => ({ apiJson: vi.fn() }));
vi.mock("@/components/ui/UiText", () => ({
  UiText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));
vi.mock("@/components/LanguageSupport", () => ({
  LearningText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));

beforeEach(() => vi.mocked(apiJson).mockReset());

test("learning targets load only when requested and never make a certification claim", async () => {
  vi.mocked(apiJson).mockResolvedValue({
    id: "pre-b1",
    reference_status: "internal_bridge",
    skills: {
      speaking: {
        target: { nl: "Vraag om verduidelijking.", en: "Ask for clarification.", fa: "درخواست توضیح کنید." },
      },
    },
    source_details: [{ id: "source", title: "CEFR", url: "https://www.coe.int/" }],
  });
  render(<AlignmentPanel stageId="pre-b1" skill="speaking" />);
  expect(apiJson).not.toHaveBeenCalled();
  await userEvent.click(screen.getByText("Wat oefen je op dit niveau?"));
  await waitFor(() => expect(apiJson).toHaveBeenCalledTimes(1));
  expect(await screen.findByText("Vraag om verduidelijking.")).toBeVisible();
  expect(screen.getByText("Een tussenstap naar het volgende niveau")).toBeVisible();
  expect(screen.getByText(/nog niet door een taalexpert/)).toBeVisible();
  expect(screen.getByRole("link", { name: "Kies je examenrichting" })).toHaveAttribute("href", "/examens");
});

test("a failed reference request can be retried without blocking the lesson", async () => {
  vi.mocked(apiJson)
    .mockRejectedValueOnce(new Error("offline"))
    .mockResolvedValueOnce({
      id: "a1",
      reference_status: "cefr_level",
      skills: { reading: { target: { nl: "Zoek de datum." } } },
      source_details: [],
    });
  render(<AlignmentPanel stageId="a1" skill="reading" />);
  await userEvent.click(screen.getByText("Wat oefen je op dit niveau?"));
  await userEvent.click(await screen.findByRole("button", { name: /kon niet worden geladen/ }));
  expect(await screen.findByText("Zoek de datum.")).toBeVisible();
  expect(apiJson).toHaveBeenCalledTimes(2);
});

test("exam exploration filters by level and preserves the C2 coverage limit", async () => {
  vi.mocked(apiJson).mockResolvedValue({
    profiles: [
      { id: "info", title: "CNaVT INFO", family: "cnavt", levels: ["A2"], source_ids: [] },
      { id: "itna", title: "ITNA B2", family: "itna", levels: ["B2"], source_ids: [] },
    ],
    sources: [],
  });
  render(<ExamPreparation />);
  expect(await screen.findByText("CNaVT INFO")).toBeVisible();
  expect(screen.queryByText("ITNA B2")).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "B2" }));
  expect(screen.getByText("ITNA B2")).toBeVisible();
  expect(screen.queryByText("CNaVT INFO")).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "C2" }));
  expect(screen.getByText(/geen CNaVT- of ITNA-C2-profiel/)).toBeVisible();
  expect(screen.getByRole("link", { name: "Schrijven" })).toHaveAttribute("href", "/learn/c2?skill=writing");
});
