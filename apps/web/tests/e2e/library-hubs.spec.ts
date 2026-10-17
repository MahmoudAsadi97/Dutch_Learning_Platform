import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "./fixtures/test";

/** These journeys use the real course endpoints so a displayed count has a browsable bank behind it. */
for (const width of [1440, 390]) {
  test(`word discovery opens the selected stage instead of an empty review queue at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/woorden?stage=pre-a2");
    await expect(page.getByTestId("words-hub")).toBeVisible();
    await expect(page.getByTestId("word-review")).toHaveCount(0);
    await expect(page.locator("#library-hub-stage")).toHaveValue("pre-a2");
    await expect(page.locator("#library-hub-stage option")).toHaveCount(12);
    await expect(page.locator(".vocabulary-card").first()).toBeVisible();
    const bank = await page.evaluate(async () => {
      const response = await fetch("/api/library/pre-a2");
      if (!response.ok) throw new Error(`Library answered ${response.status}`);
      return response.json();
    });
    await expect(page.locator(".library-hub-counts")).toContainText(`${bank.vocabulary_count} woordkaarten`);
    await page.locator("#library-hub-stage").selectOption("c2");
    await expect(page).toHaveURL(/stage=c2/);
    await expect(page.getByRole("link", { name: "Alles op dit niveau" })).toHaveAttribute(
      "href",
      "/learn/c2",
    );
    await expect(page.locator(".vocabulary-card").first()).toBeVisible();
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      .toBe(true);
  });
}

test("story discovery exposes the authored bank while personal episodes remain a separate view", async ({
  page,
}) => {
  await page.goto("/verhalen?stage=pre-a2");
  await expect(page.getByTestId("story-library")).toHaveCount(0);
  await expect(page.locator(".story-tile").first()).toBeVisible();
  const coverage = await page.evaluate(async () => {
    const response = await fetch("/api/curriculum");
    if (!response.ok) throw new Error(`Catalogue answered ${response.status}`);
    return (await response.json()).stages.find((stage: { id: string }) => stage.id === "pre-a2").coverage;
  });
  await expect(page.locator(".library-hub-counts")).toContainText(
    `${coverage.eligible_authored_stories} uitgewerkte verhalen`,
  );
  await expect(page.getByRole("link", { name: "Mijn afleveringen" })).toHaveAttribute(
    "href",
    "/verhalen?stage=pre-a2&view=personal",
  );
  await page.locator(".story-tile button").first().click();
  await expect(page.locator(".story-lines li").first()).toBeVisible();
  const lines = await page.locator(".story-lines li").count();
  expect(lines).toBeGreaterThanOrEqual(8);
  expect(lines).toBeLessThanOrEqual(12);
  const results = await new AxeBuilder({ page }).include("#main").analyze();
  expect(results.violations.filter((issue) => ["critical", "serious"].includes(issue.impact ?? ""))).toEqual(
    [],
  );
});

for (const width of [1440, 390]) {
  test(`grammar stays selected when changing to pre-A2 and after reloading at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/learn/a1?section=grammar");
    const navigation = page.getByRole("navigation", { name: "Onderdelen van dit niveau" });
    await expect(navigation.getByRole("button", { name: /^Grammatica(?:\s|$)/ })).toHaveAttribute(
      "aria-current",
      "step",
    );
    await expect(page.locator("#workspace-stage option")).toHaveCount(12);
    await expect(page.locator(".grammar-practice .curriculum-question")).toHaveCount(1);
    await page.locator("#workspace-stage").selectOption("pre-a2");
    await expect(page).toHaveURL(/\/learn\/pre-a2\?section=grammar$/);
    await expect(page.locator("#workspace-stage")).toHaveValue("pre-a2");
    await expect(navigation.getByRole("button", { name: /^Grammatica(?:\s|$)/ })).toHaveAttribute(
      "aria-current",
      "step",
    );
    await expect(page.locator(".grammar-practice .curriculum-question")).toHaveCount(1);
    await expect(page.locator(".grammar-position")).toContainText("Vraag 1 van 10");
    await page.reload();
    await expect(navigation.getByRole("button", { name: /^Grammatica(?:\s|$)/ })).toHaveAttribute(
      "aria-current",
      "step",
    );
    await expect(page.locator("#workspace-stage")).toHaveValue("pre-a2");
    await expect(page.locator(".grammar-practice .curriculum-question")).toHaveCount(1);
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      .toBe(true);
  });
}

test("grammar shows one real question, preserves an answer when moving back and resets position for another topic", async ({
  page,
}) => {
  await page.goto("/learn/pre-a2?section=grammar");
  const stage = await page.evaluate(async () => {
    const response = await fetch("/api/curriculum/pre-a2");
    if (!response.ok) throw new Error(`Stage answered ${response.status}`);
    return response.json();
  });
  const round = stage.grammar.find((topic: { id: string }) => topic.id.startsWith("practice-"));
  expect(round.practice).toHaveLength(10);
  const first = round.practice[0];
  const second = round.practice[1];
  const grammar = page.locator(".grammar-practice");
  await expect(grammar.locator(".curriculum-question")).toHaveCount(1);
  await expect(grammar.getByRole("button", { name: /^Vorige vraag(?:\s|$)/ })).toBeDisabled();
  await expect(grammar.getByRole("button", { name: /^Controleer je antwoord(?:\s|$)/ })).toBeDisabled();
  const choice = grammar.locator(`input[name="q-${first.id}"]`).nth(first.answer_index);
  await choice.check();
  await grammar.getByRole("button", { name: /^Controleer je antwoord(?:\s|$)/ }).click();
  await expect(grammar.locator(".practice-correct")).toContainText("Goed gedaan.");
  await grammar.getByRole("button", { name: /^Volgende vraag(?:\s|$)/ }).click();
  await expect(grammar.locator(".grammar-position")).toContainText("Vraag 2 van 10");
  await expect(grammar.locator(`input[name="q-${first.id}"]`)).toHaveCount(0);
  await expect(grammar.locator(`input[name="q-${second.id}"]`).first()).toBeVisible();
  await expect(grammar.locator(".practice-correct")).toHaveCount(0);
  await grammar.getByRole("button", { name: /^Vorige vraag(?:\s|$)/ }).click();
  await expect(choice).toBeChecked();
  await expect(grammar.locator(".practice-correct")).toContainText("Goed gedaan.");
  await grammar.getByRole("button", { name: /^Volgende vraag(?:\s|$)/ }).click();
  await grammar.getByRole("button", { name: /^Volgend onderwerp(?:\s|$)/ }).click();
  await expect(grammar.locator(".grammar-position")).toContainText("Vraag 1 van 10");
  await expect(grammar.locator(".curriculum-question")).toHaveCount(1);
  await expect(grammar.getByRole("button", { name: /^Vorige vraag(?:\s|$)/ })).toBeDisabled();
});

test("the level directory exposes every activity directly and opens pre-A2 stories", async ({ page }) => {
  await page.goto("/leerpad");
  await expect(page.locator("#directory-stage option")).toHaveCount(12);
  const cards = page.getByTestId("curriculum-path").locator(":scope > li");
  await expect(cards).toHaveCount(12);
  const target = cards.filter({ has: page.locator(".stage-level").filter({ hasText: /^pre-A2$/ }) });
  await expect(target).toHaveCount(1);
  for (const [label, query] of [
    ["Lezen", "skill=reading"],
    ["Luisteren", "skill=listening"],
    ["Spreken", "skill=speaking"],
    ["Schrijven", "skill=writing"],
    ["Woorden", "section=words"],
    ["Grammatica", "section=grammar"],
    ["Verhalen", "section=stories"],
  ]) {
    await expect(target.getByRole("link", { name: new RegExp(`^${label}(?:\\s|$)`) })).toHaveAttribute(
      "href",
      `/learn/pre-a2?${query}`,
    );
  }
  await target.getByRole("link", { name: /^Verhalen(?:\s|$)/ }).click();
  await expect(page).toHaveURL(/\/learn\/pre-a2\?section=stories$/);
  await expect(page.locator("#workspace-stage")).toHaveValue("pre-a2");
  await expect(
    page
      .getByRole("navigation", { name: "Onderdelen van dit niveau" })
      .getByRole("button", { name: /^Verhalen(?:\s|$)/ }),
  ).toHaveAttribute("aria-current", "step");
  await expect(page.locator(".story-tile").first()).toBeVisible();
});

test("320px level cards keep translated counts and skill labels apart", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto("/leerpad");
  await expect(page.locator("#directory-stage")).toBeVisible();
  await expect(page.locator("#directory-stage option")).toHaveCount(12);
  const target = page
    .getByTestId("curriculum-path")
    .locator(":scope > li")
    .filter({
      has: page.locator(".stage-level").filter({ hasText: /^C2$/ }),
    });
  await expect(target).toHaveCount(1);
  await target.scrollIntoViewIfNeeded();
  await expect(target.locator(".coverage-summary dt")).toHaveCount(3);
  await expect
    .poll(async () =>
      target.evaluate((card) => {
        const problems: string[] = [];
        for (const element of card.querySelectorAll<HTMLElement>(
          ".coverage-summary dt, .coverage-summary dd, .stage-activity-grid a",
        )) {
          if (element.scrollWidth > element.clientWidth + 1)
            problems.push(`overflow: ${element.textContent}`);
        }
        for (const link of card.querySelectorAll<HTMLElement>(".stage-activity-grid a")) {
          const children = [...link.children]
            .map((child) => child.getBoundingClientRect())
            .filter((box) => box.width > 0);
          for (let i = 1; i < children.length; i += 1) {
            if (children[i - 1].right > children[i].left + 1) problems.push(`overlap: ${link.textContent}`);
          }
        }
        return problems;
      }),
    )
    .toEqual([]);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
