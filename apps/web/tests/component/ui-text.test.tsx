import { render } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UiText } from "@/components/ui/UiText";
import { fill, uiCopy } from "@/lib/ui-copy";

/** Persian glosses wait for a fluent reader (owner decision O2); English stands in for those who chose it. */
const flags: Record<string, boolean> = {};
const support = { showEnglish: true, showPersian: true };

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
  support.showPersian = true;
});

describe("UiText and the Persian review", () => {
  it("shows English instead of Persian while the batch is not reviewed", () => {
    const { container } = render(<UiText text={uiCopy.nav.today} />);
    expect(languages(container)).toEqual(["en"]);
  });

  it("shows Persian, right to left, once the batch is reviewed", () => {
    flags.nav = true;
    const { container } = render(<UiText text={uiCopy.nav.today} />);
    expect(languages(container)).toEqual(["fa"]);
    expect(container.querySelector('.ui-gloss[lang="fa"]')).toHaveAttribute("dir", "rtl");
  });

  it("gives guides every selected language that is allowed", () => {
    flags.welcome = true;
    const { container } = render(<UiText text={uiCopy.welcome.levelNote} tier="guide" />);
    expect(languages(container)).toEqual(["en", "fa"]);
  });

  it("keeps the batch of a filled copy", () => {
    flags.today = true;
    const { container } = render(<UiText text={fill(uiCopy.today.goalLeft, { points: 5 })} tier="guide" />);
    expect(languages(container)).toEqual(["en", "fa"]);
    expect(container.textContent).toContain("Nog 5 punten");
  });

  it("shows only Dutch to a Persian-only learner until the batch is reviewed", () => {
    support.showEnglish = false;
    const { container } = render(<UiText text={uiCopy.nav.today} />);
    expect(languages(container)).toEqual([]);
    expect(container.textContent).toBe("Vandaag");
  });
});
