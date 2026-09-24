import { expect, test } from "@playwright/test";

test("recall reveals only on request and repeats the words the learner found difficult", async ({ page }) => {
  await page.goto("/learn/pre-a1");
  const tool = page.getByTestId("vocabulary-recall");
  await expect(tool).toBeVisible();
  const before = await (await page.request.get("/api/curriculum/pre-a1")).json();
  await tool.getByRole("button", { name: "Start een korte woordronde" }).click();
  await expect(tool.getByRole("status")).toHaveText("Woord 1 van 5");
  await expect(tool.locator(".recall-reveal")).toHaveCount(0);
  await tool.locator("input").fill("mijn poging");
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
  await expect(tool.locator("input")).toHaveValue("mijn poging");
  await tool.getByRole("button", { name: "Vergelijk je antwoord" }).click();
  const firstWord = await tool.locator(".recall-reveal h4").innerText();
  await tool.getByRole("button", { name: "Nog eens oefenen" }).click();
  for (let i = 0; i < 4; i++) {
    await tool.getByRole("button", { name: "Vergelijk je antwoord" }).click();
    await tool.getByRole("button", { name: "Ik herinnerde het me" }).click();
  }
  await expect(tool).toContainText("1 van 5 woorden wil je opnieuw oefenen.");
  await tool.getByRole("button", { name: "Herhaal de lastige woorden" }).click();
  await expect(tool.getByRole("status")).toHaveText("Woord 1 van 1");
  await tool.getByRole("button", { name: "Vergelijk je antwoord" }).click();
  await expect(tool.locator(".recall-reveal h4")).toHaveText(firstWord);
  // Self-report is practice support, never a pass or a shortcut through a level.
  const after = await (await page.request.get("/api/curriculum/pre-a1")).json();
  expect(after.progress.practice_completed).toEqual(before.progress.practice_completed);
});

test("speaking support explains a communication goal and connects to the real role-play library", async ({ page }) => {
  await page.goto("/learn/pre-a1");
  await page.getByRole("navigation", { name: "Onderdelen van dit niveau" }).getByRole("button", { name: "Spreken", exact: true }).click();
  await page.getByRole("button", { name: "Startles", exact: true }).click();
  const coach = page.locator(".communication-coach");
  await coach.locator("summary").click();
  await expect(coach.locator(".communication-steps > li")).toHaveCount(3);
  await expect(coach).toContainText("Kunt u dat herhalen?");
  await expect(coach).toContainText("geen uitspraakscore");
  await coach.getByRole("link").click();
  await expect(page).toHaveURL(/\/missions$/);
  await expect(page.locator(".catalog-card")).toHaveCount(4);
});
