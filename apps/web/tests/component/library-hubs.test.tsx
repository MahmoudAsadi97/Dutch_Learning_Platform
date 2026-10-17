import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";
import { LibraryHub } from "@/components/LibraryHub";
import { SpeakHub } from "@/components/speak/SpeakHub";
import { apiJson } from "@/lib/client/api";

const navigation = vi.hoisted(() => ({ query: "", pathname: "/verhalen", replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(navigation.query),
  usePathname: () => navigation.pathname,
  useRouter: () => ({ replace: navigation.replace }),
}));
vi.mock("@/lib/client/api", () => ({ apiJson: vi.fn() }));
vi.mock("@/components/ui/UiText", () => ({
  UiText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));
vi.mock("@/components/LanguageSupport", () => ({
  LearningText: ({ text }: { text: { nl: string } }) => <span>{text.nl}</span>,
}));
vi.mock("@/components/LearningLibrary", () => ({
  StoryTime: ({ stageId }: { stageId: string }) => <section data-testid="course-stories">{stageId}</section>,
  WordLibrary: ({ stageId }: { stageId: string }) => <section data-testid="course-words">{stageId}</section>,
}));
vi.mock("@/components/StoryLibrary", () => ({
  StoryLibrary: () => <section data-testid="personal-stories">Mijn afleveringen</section>,
}));
vi.mock("@/components/WordReview", () => ({
  WordReview: () => <section data-testid="personal-review">Mijn herhaling</section>,
}));
vi.mock("@/components/MissionCatalog", () => ({
  MissionCatalog: () => <section data-testid="missions">Praktijkgesprekken</section>,
}));

const catalogue = {
  stages: ["pre-a1", "pre-a2", "c2"].map((id, index) => ({
    id,
    coverage: {
      words: 515 + index,
      productive_core: 150,
      eligible_authored_stories: 52 - index,
      legacy_stories: 102,
      targets: { authored_stories: 200 },
      skill_topics: { speaking: 104 - index },
    },
  })),
};

beforeEach(() => {
  navigation.query = "";
  navigation.pathname = "/verhalen";
  navigation.replace.mockReset();
  vi.mocked(apiJson).mockReset();
  vi.mocked(apiJson).mockImplementation(async (path) =>
    path === "curriculum"
      ? catalogue
      : {
          items: [{ id: "partner-a1", stage_id: "a1", topic_id: "a1-intro", title: { nl: "Kennismaken" } }],
        },
  );
});

test("the story landing opens the course library and shows actual eligible counts, not a completed target", async () => {
  render(<LibraryHub kind="stories" />);
  expect(screen.getByTestId("course-stories")).toHaveTextContent("pre-a1");
  expect(screen.queryByTestId("personal-stories")).not.toBeInTheDocument();
  expect(await screen.findByText("52 uitgewerkte verhalen · doel: 200")).toBeVisible();
  expect(screen.getByText(/Daarnaast 102 korte oefenteksten/)).toBeVisible();
  expect(screen.getByRole("link", { name: "Mijn afleveringen" })).toHaveAttribute(
    "href",
    "/verhalen?stage=pre-a1&view=personal",
  );
  expect(screen.getAllByRole("option")).toHaveLength(12);
});

test("choosing pre-A2 updates the URL and the actual library, with a direct path to all its skills", async () => {
  const { rerender } = render(<LibraryHub kind="stories" />);
  await userEvent.selectOptions(screen.getByLabelText("Kies je niveau"), "pre-a2");
  expect(navigation.replace).toHaveBeenCalledWith("/verhalen?stage=pre-a2", { scroll: false });
  navigation.query = "stage=pre-a2";
  rerender(<LibraryHub kind="stories" />);
  expect(screen.getByTestId("course-stories")).toHaveTextContent("pre-a2");
  expect(await screen.findByText("51 uitgewerkte verhalen · doel: 200")).toBeVisible();
  expect(screen.getByRole("link", { name: "Alles op dit niveau" })).toHaveAttribute("href", "/learn/pre-a2");
});

test("word discovery remains available when the learner has no saved cards", async () => {
  navigation.pathname = "/woorden";
  render(<LibraryHub kind="words" />);
  expect(screen.getByTestId("course-words")).toHaveTextContent("pre-a1");
  expect(screen.queryByTestId("personal-review")).not.toBeInTheDocument();
  expect(await screen.findByText("515 woordkaarten · 150 kernwoorden")).toBeVisible();
  expect(apiJson).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("link", { name: "Mijn herhaling" })).toHaveAttribute(
    "href",
    "/woorden?stage=pre-a1&view=personal",
  );
});

test("personal views are explicit and do not mix saved counts into the course bank", () => {
  navigation.pathname = "/woorden";
  navigation.query = "stage=c2&view=personal";
  render(<LibraryHub kind="words" />);
  expect(screen.getByTestId("personal-review")).toBeVisible();
  expect(screen.queryByTestId("course-words")).not.toBeInTheDocument();
  expect(screen.getByText(/Hier herhaal je alleen woorden/)).toBeVisible();
  expect(screen.getByRole("link", { name: "Woordkaarten per niveau" })).toHaveAttribute(
    "href",
    "/woorden?stage=c2",
  );
});

test("a catalogue failure offers retry and never fabricates counts", async () => {
  vi.mocked(apiJson).mockRejectedValueOnce(new Error("offline"));
  render(<LibraryHub kind="stories" />);
  expect(await screen.findByRole("alert")).toBeVisible();
  expect(screen.queryByText(/uitgewerkte verhalen · doel/)).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Opnieuw proberen" }));
  expect(await screen.findByText("52 uitgewerkte verhalen · doel: 200")).toBeVisible();
});

test("speaking reaches every level's full bank while keeping microphone setup secondary", async () => {
  navigation.pathname = "/spreken";
  navigation.query = "stage=c2";
  render(<SpeakHub />);
  expect(await screen.findByText("102 spreekonderwerpen")).toBeVisible();
  expect(screen.getByRole("link", { name: "Kies een spreekonderwerp" })).toHaveAttribute(
    "href",
    "/learn/c2?skill=speaking",
  );
  expect(screen.getAllByRole("option")).toHaveLength(12);
  expect(screen.queryByRole("link", { name: "Kennismaken" })).not.toBeInTheDocument();
  expect(await screen.findByText(/Voor dit niveau staan hier nog geen extra gesprekken/)).toBeVisible();
  expect(screen.getByRole("link", { name: "Open de spraakstudio" })).toHaveAttribute("href", "/speech-check");
  expect(screen.getByTestId("missions")).toBeVisible();
  await waitFor(() => expect(apiJson).toHaveBeenCalledTimes(2));
});
