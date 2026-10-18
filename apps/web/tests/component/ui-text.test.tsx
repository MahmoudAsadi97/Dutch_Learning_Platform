import { render } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UiText } from "@/components/ui/UiText";
import { fill, uiCopy } from "@/lib/ui-copy";
import { persianReviewed } from "@/lib/client/persian-review";

/** Only the supported Dutch and Dutch/English modes are supplied by the workspace context. */
const flags: Record<string, boolean> = {};
const support = { showEnglish: true, showPersian: false };

vi.mock("@/lib/copy/review", () => ({
  PERSIAN_REVIEWED: new Proxy({}, { get: (_target, key: string) => flags[key] ?? false }),
}));
vi.mock("@/components/LanguageSupport", () => ({
  useLanguageSupport: () => ({ glossLevel: "chrome", ...support }),
}));

function languages(container: HTMLElement) {
  return [...container.querySelectorAll(".ui-gloss")].map((node) => node.getAttribute("lang"));
}

beforeEach(() => {
  for (const key of Object.keys(flags)) delete flags[key];
  support.showEnglish = true;
  support.showPersian = false;
});

describe("UiText support language", () => {
  it("shows English help when selected", () => {
    const { container } = render(<UiText text={uiCopy.nav.today} />);
    expect(languages(container)).toEqual(["en"]);
  });

  it("keeps retired translations hidden even when their source batch is reviewed", () => {
    flags.nav = true;
    const { container } = render(<UiText text={uiCopy.nav.today} />);
    expect(languages(container)).toEqual(["en"]);
    expect(container.querySelector('[lang="fa"]')).toBeNull();
  });

  it("gives guides English explanations without restoring a retired language", () => {
    flags.welcome = true;
    const { container } = render(<UiText text={uiCopy.welcome.levelNote} tier="guide" />);
    expect(languages(container)).toEqual(["en"]);
  });

  it("keeps the batch of a filled copy", () => {
    flags.today = true;
    const { container } = render(<UiText text={fill(uiCopy.today.goalLeft, { points: 5 })} tier="guide" />);
    expect(languages(container)).toEqual(["en"]);
    expect(persianReviewed(fill(uiCopy.today.goalLeft, { points: 5 }))).toBe(true);
    expect(container.textContent).toContain("Nog 5 punten");
  });

  it("shows only Dutch when English help is off", () => {
    support.showEnglish = false;
    const { container } = render(<UiText text={uiCopy.nav.today} />);
    expect(languages(container)).toEqual([]);
    expect(container.textContent).toBe("Dashboard");
  });
});

describe("layout", () => {
  it("marks sentences, so they keep their paragraph's line height; labels stay compact", () => {
    const { container } = render(
      <>
        <UiText text={uiCopy.nav.today} />
        <UiText text={uiCopy.welcome.levelNote} tier="guide" />
      </>,
    );
    const [label, sentence] = container.querySelectorAll(".ui-text");
    expect(label).not.toHaveClass("is-sentence");
    expect(sentence).toHaveClass("is-sentence");
  });
});

describe("a copy that crossed from a server component", () => {
  it("is still recognised by its text", async () => {
    flags.nav = true;
    const serialized = JSON.parse(JSON.stringify(uiCopy.nav.today));
    const { container } = render(<UiText text={serialized} />);
    expect(persianReviewed(serialized)).toBe(true);
    expect(languages(container)).toEqual(["en"]);
  });
});
