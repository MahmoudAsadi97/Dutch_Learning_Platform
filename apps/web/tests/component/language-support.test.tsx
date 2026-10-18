import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LanguageProvider, LanguageSwitcher, LearningText } from "@/components/LanguageSupport";
import { UiText } from "@/components/ui/UiText";
import { Trilingual } from "@/components/welcome/Trilingual";
import { Meaning } from "@/components/exercise/ContentText";
import type { Me } from "@/lib/client/profile";
import { storageKeys } from "@/lib/client/storage";

const state = vi.hoisted(() => ({ profile: null as Me | null, update: vi.fn() }));
vi.mock("@/lib/client/profile", () => ({
  useProfile: () => ({ data: state.profile }),
  updateProfile: (...args: unknown[]) => state.update(...args),
}));

const copy = { nl: "Goedemorgen", en: "Good morning", fa: "صبح بخیر" };
const profile = (mode: unknown): Me =>
  ({
    learner: { email: "learner@example.com", display_name: "Learner" },
    profile: { stage_id: "a1", support_mode: mode, gloss_mode: "on" },
    features: {},
  }) as Me;

function mount(mode: unknown = "nl-en") {
  state.profile = profile(mode);
  state.update.mockResolvedValue(profile("nl"));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <LanguageProvider>
        <LanguageSwitcher />
        <LearningText text={copy} />
        <UiText text={copy} tier="always" />
        <Trilingual text={copy} autonym="فارسی" />
        <Meaning text={copy} />
      </LanguageProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
  state.update.mockReset();
});

describe("Dutch and optional English support", () => {
  it("offers only the two supported choices and never renders stored Persian translations", () => {
    const { container } = mount();
    const choices = screen.getAllByRole("option");
    expect(choices.map((choice) => (choice as HTMLOptionElement).value)).toEqual(["nl", "nl-en"]);
    expect(container.querySelectorAll('[lang="fa"]')).toHaveLength(0);
    expect(screen.getAllByText("Good morning")).toHaveLength(4);
  });

  it("turns off support translations for Dutch-only practice and saves that preference", async () => {
    const { container } = mount();
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "nl" } });
    expect(screen.queryByText("Good morning")).not.toBeInTheDocument();
    expect(container.querySelectorAll('[lang="fa"]')).toHaveLength(0);
    expect(localStorage.getItem(storageKeys.languageSupport)).toBe("nl");
    await waitFor(() => expect(state.update).toHaveBeenCalledWith({ support_mode: "nl" }));
  });

  it("normalizes a retired device and profile preference without exposing it as an option", () => {
    localStorage.setItem(storageKeys.languageSupport, "nl-fa-en");
    const { container } = mount("nl-fa");
    expect(screen.getByRole("combobox")).toHaveValue("nl-en");
    expect(container.querySelectorAll('[lang="fa"]')).toHaveLength(0);
    expect(state.update).not.toHaveBeenCalled();
  });
});
