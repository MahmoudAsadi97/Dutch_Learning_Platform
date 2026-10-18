import { expect, test } from "./fixtures/test";
import { studyCatalog, exampleFeedback } from "./fixtures/study";
import { STAGE_IDS, SKILLS } from "../../lib/domain/registry";

test("every stage has at least fifty selectable real topic activities for each skill", async ({ page }) => {
  for (const stage of STAGE_IDS)
    for (const skill of SKILLS) {
      const catalogue = await studyCatalog(page, stage, skill);
      expect(
        catalogue.topics.filter((topic) => topic.available).length,
        `${stage} ${skill}`,
      ).toBeGreaterThanOrEqual(50);
      expect(catalogue.topics).toHaveLength(100);
      expect(new Set(catalogue.topics.map((topic) => topic.id)).size).toBe(100);
    }
  await page.goto("/learn/a2?skill=reading");
  await expect(page.locator(".study-topic-card").first()).toBeVisible();
  await page.getByLabel("Zoek een onderwerp").fill("familie");
  await expect(page.locator(".study-topic-card")).toHaveCount(1);
  await expect(page.locator(".study-topic-card")).toContainText("Familie");
  await page.getByLabel("Zoek een onderwerp").fill("geen-bestaand-onderwerp");
  await expect(page.getByRole("heading", { name: /^Geen onderwerp gevonden(?:\s|$)/ })).toBeVisible();
  await page.getByRole("button", { name: /^Wis filters(?:\s|$)/ }).click();
  expect(await page.locator(".study-topic-card").count()).toBeGreaterThanOrEqual(50);
});

test("parts advance in order and every speaking part offers a hidden example", async ({ page }) => {
  await page.goto("/learn/b2?skill=speaking&topic=job-interviews&step=practise");
  const parts = page.getByRole("navigation", { name: "Onderdelen van deze vaardigheid" }).getByRole("button");
  await expect(parts).toHaveCount(3);
  for (let index = 0; index < 3; index++) {
    await expect(parts.nth(index)).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator(".study-example-answer")).toHaveCount(0);
    await page.getByRole("button", { name: /^Bekijk een voorbeeldantwoord/ }).click();
    await expect(page.locator(".study-example-answer")).toBeVisible();
    await page.getByRole("button", { name: /^Voorbeeld verbergen/ }).click();
    if (index < 2) await page.locator(".study-check-actions button.secondary").click();
  }
});

test("a failed feedback request keeps the answer and a successful response explains corrections", async ({
  page,
}) => {
  let attempts = 0;
  await page.route("**/api/study/a2/topics/family/feedback", (route) => {
    const body = route.request().postDataJSON();
    expect(body.skill).toBe("writing");
    expect(body.text).toBe("Ik woont in Gent.");
    return attempts++ === 0
      ? route.fulfill({ status: 503, json: { detail: "temporary service failure" } })
      : route.fulfill({ json: exampleFeedback });
  });
  await page.goto("/learn/a2?skill=writing&topic=family&step=practise");
  const input = page.getByLabel(/^Jouw antwoord/);
  await input.fill("Ik woont in Gent.");
  await page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click();
  await expect(page.locator(".study-error")).toBeVisible();
  await expect(input).toHaveValue("Ik woont in Gent.");
  await page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click();
  const feedback = page.getByRole("region", { name: "Tijdelijke oefenfeedback" });
  await expect(feedback).toContainText("Ik woont");
  await expect(feedback).toContainText("Ik woon");
  await expect(feedback).toContainText("Bij ik gebruik je de stam.");
  await input.fill("Ik woon in Gent.");
  await expect(feedback).toHaveCount(0);
});

test("pending transcription protects the recording and uses only the temporary endpoint", async ({
  page,
}) => {
  let release = () => {};
  const ready = new Promise<void>((resolve) => {
    release = resolve;
  });
  let bodyType = "";
  await page.route("**/api/study/pre-a1/topics/family/transcribe", async (route) => {
    bodyType = route.request().headers()["content-type"];
    await ready;
    await route.fulfill({
      json: {
        transcript: { text: "Ik heet Noor." },
        audio: { stored: false, asset_id: null },
        ephemeral: true,
      },
    });
  });
  try {
    await page.goto("/learn/pre-a1?skill=speaking&topic=family&step=practise");
    await page.getByRole("button", { name: /^Neem je antwoord op(?:\s|$)/ }).click();
    await page.getByRole("button", { name: /^Stop opname(?:\s|$)/ }).click();
    await expect(page.getByLabel(/^Je herkende woorden/)).toBeDisabled();
    await page
      .getByRole("navigation", { name: "Kies een vaardigheid" })
      .getByRole("link", { name: /^Schrijven/ })
      .click();
    await expect(page).toHaveURL(/skill=speaking/);
    await expect(page.locator(".study-error")).toBeVisible();
    release();
    await expect(page.getByLabel(/^Je herkende woorden/)).toHaveValue("Ik heet Noor.");
    expect(bodyType).toContain("multipart/form-data");
    await page.getByRole("button", { name: /^Andere korte vraag/ }).click();
    await expect(page.getByLabel(/^Je herkende woorden/)).toHaveValue("");
    await expect(page.locator(".study-recorder audio")).toHaveCount(0);
  } finally {
    release();
  }
});

test("the previous stage's delayed catalogue cannot replace the newly chosen stage", async ({ page }) => {
  const a2 = await studyCatalog(page, "a2", "reading");
  let release = () => {};
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/study/a2/topics?skill=reading", async (route) => {
    await pending;
    await route.fulfill({
      json: { ...a2, topics: [{ ...a2.topics[0], title: { nl: "Vertraagd oud onderwerp" } }] },
    });
  });
  try {
    await page.goto("/learn/a2?skill=reading");
    await page.locator("#study-stage").selectOption("b1");
    await expect(page.locator(".study-topic-card").first()).toBeVisible();
    release();
    await expect(page.locator("#study-stage")).toHaveValue("b1");
    await expect(page.getByText("Vertraagd oud onderwerp")).toHaveCount(0);
  } finally {
    release();
  }
});

test("topic cards, stories and corrections fit at 320px and 390px", async ({ page }) => {
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/learn/a2?skill=reading&topic=family&step=practise");
    await expect(page.locator(".study-story-line").first()).toBeVisible();
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      .toBe(true);
    await page.goto("/learn/a2?skill=writing&topic=family&step=practise");
    await page.route("**/api/study/a2/topics/family/feedback", (route) =>
      route.fulfill({ json: exampleFeedback }),
    );
    await page.getByLabel(/^Jouw antwoord/).fill("Ik woont in Gent.");
    await page.getByRole("button", { name: /^Bekijk mijn feedback/ }).click();
    await expect(page.getByRole("region", { name: "Tijdelijke oefenfeedback" })).toBeVisible();
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      .toBe(true);
    await page.unroute("**/api/study/a2/topics/family/feedback");
  }
});
