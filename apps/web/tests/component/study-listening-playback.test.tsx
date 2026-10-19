import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { PracticePart } from "@/components/study/StudyPracticePart";
import { apiFetch } from "@/lib/client/api";
import type { StudyLesson, StudyPart } from "@/lib/client/study";

vi.mock("@/lib/client/api", async (load) => ({
  ...(await load<typeof import("@/lib/client/api")>()),
  apiFetch: vi.fn(),
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

const part: StudyPart = {
  id: "listen-choice",
  title: { nl: "Luister naar de afspraak" },
  instructions: { nl: "Kies de dag." },
  prompt: { nl: "Wanneer spreken ze af?" },
  sample: null,
  text: [{ nl: "We spreken woensdag af." }],
  questions: [{ id: "day", kind: "choice", prompt: { nl: "Welke dag?" }, options: [{ nl: "Woensdag" }] }],
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

function show() {
  return render(
    <PracticePart
      lesson={lesson}
      part={part}
      mode="practise"
      assisted={false}
      onAssisted={vi.fn()}
      onNext={vi.fn()}
    />,
  );
}
function clip() {
  return new Response("audio", {
    headers: { "Content-Type": "audio/wav" },
  });
}
beforeEach(() => {
  vi.mocked(apiFetch).mockReset().mockResolvedValue(clip());
  vi.stubGlobal(
    "URL",
    class extends URL {
      static createObjectURL = vi.fn(() => "blob:listening");
      static revokeObjectURL = vi.fn();
    },
  );
  vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

test("the first asynchronous clip plays without a later render reloading the pending player", async () => {
  const { container } = show();
  const player = container.querySelector("audio")!;
  let pending = false;
  let started = false;
  let rejectPlay: (cause: DOMException) => void = () => {};
  const observer = new MutationObserver((changes) => {
    if (pending && changes.some((change) => change.attributeName === "src"))
      rejectPlay(new DOMException("The media source was replaced during play", "AbortError"));
  });
  observer.observe(player, { attributes: true, attributeFilter: ["src"] });
  vi.mocked(player.play).mockImplementation(
    () =>
      new Promise<void>((resolve, reject) => {
        // Source assignment before play is fine. A subsequent source change aborts a real pending play.
        observer.takeRecords();
        pending = true;
        rejectPlay = reject;
        setTimeout(() => {
          pending = false;
          started = true;
          resolve();
        }, 50);
      }),
  );
  try {
    await userEvent.click(screen.getByRole("button", { name: "Start de opname" }));
    await waitFor(() => expect(started).toBe(true));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledOnce();
    expect(player).toHaveAttribute("src", "blob:listening");
  } finally {
    observer.disconnect();
  }
});

test("a browser gesture restriction offers a cached replay without another synthesis call", async () => {
  vi.mocked(HTMLMediaElement.prototype.play)
    .mockRejectedValueOnce(new DOMException("A user gesture is required", "NotAllowedError"))
    .mockResolvedValueOnce();
  show();
  await userEvent.click(screen.getByRole("button", { name: "Start de opname" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Tik nog eens op afspelen");
  await userEvent.click(screen.getByRole("button", { name: "Start de opname" }));
  await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
  expect(apiFetch).toHaveBeenCalledOnce();
  expect(HTMLMediaElement.prototype.play).toHaveBeenCalledTimes(2);
});

test("leaving during synthesis cancels the request and never plays or allocates the late response", async () => {
  let finish!: (response: Response) => void;
  vi.mocked(apiFetch).mockImplementationOnce(() => new Promise<Response>((resolve) => (finish = resolve)));
  const { unmount } = show();
  await userEvent.dblClick(screen.getByRole("button", { name: "Start de opname" }));
  expect(apiFetch).toHaveBeenCalledOnce();
  const signal = vi.mocked(apiFetch).mock.calls[0][1]?.signal;
  unmount();
  expect(signal?.aborted).toBe(true);
  await act(async () => finish(clip()));
  expect(HTMLMediaElement.prototype.play).not.toHaveBeenCalled();
  expect(URL.createObjectURL).not.toHaveBeenCalled();
});

test("a failed audio request leaves the selected answer intact and can be retried", async () => {
  vi.mocked(apiFetch).mockResolvedValueOnce(new Response(null, { status: 503 }));
  show();
  await userEvent.click(screen.getByRole("radio"));
  await userEvent.click(screen.getByRole("button", { name: "Start de opname" }));
  expect(await screen.findByRole("alert")).toBeVisible();
  expect(screen.getByRole("radio")).toBeChecked();
  await userEvent.click(screen.getByRole("button", { name: "Start de opname" }));
  await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
  expect(screen.getByRole("radio")).toBeChecked();
  expect(apiFetch).toHaveBeenCalledTimes(2);
});
