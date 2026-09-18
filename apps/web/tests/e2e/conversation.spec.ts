import { expect, test } from "@playwright/test";

/**
 * The speaking loop against the fixture providers: the fixture transcript is a fixed sentence and the
 * fixture chat model follows keyword rules, so the conversation is deterministic end to end.
 * `python scripts/run.py e2e` empties the learner data first, so the base session starts fresh here.
 */
test.describe("speaking step", () => {
  test.describe.configure({ mode: "serial" });

  test("a spoken turn and typed turns run the conversation to the goal", async ({ page, browserName }) => {
    test.skip(browserName !== "chromium", "fake audio capture is a Chromium feature");
    await page.goto("/missions/appointment-change");
    await page.getByRole("button", { name: /Spreken: het telefoongesprek/ }).click();
    const step = page.locator('[data-step="speak-call"]');
    await expect(step).toHaveAttribute("data-step-type", "speaking");

    await step.getByTestId("start-conversation").click();
    const conversation = step.getByTestId("conversation");
    await expect(conversation.getByTestId("turn-character").first()).toContainText("Goeiedag, Tandartspraktijk Molenstraat");
    await expect(step.getByTestId("step-status")).toHaveText("12 van 12 beurten over.");

    // spoken turn: the fake microphone plays the fixture wav, the fixture STT returns a fixed sentence
    const talk = step.getByTestId("talk-button");
    const box = await talk.boundingBox();
    if (!box) throw new Error("talk button not visible");
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await expect(talk).toHaveAttribute("aria-pressed", "true");
    await page.waitForTimeout(1200);
    await page.mouse.up();
    const spoken = conversation.getByTestId("turn-learner").first();
    await expect(spoken).toHaveAttribute("data-modality", "speech", { timeout: 30_000 });
    await expect(spoken).toContainText("Ik wil mijn afspraak verzetten.");
    await expect(spoken).toContainText("gesproken · transcriptie");
    await expect(conversation.getByTestId("turn-character")).toHaveCount(2);
    await expect(step.getByTestId("character-audio-label")).toContainText("synthetic-development");
    await expect(step.getByTestId("step-status")).toHaveText("11 van 12 beurten over.");

    // typed turns are allowed in the practice step and labelled as typed evidence
    const input = step.getByTestId("typed-input");
    await input.fill("Ik moet werken.");
    await step.getByTestId("typed-send").click();
    const typed = conversation.getByTestId("turn-learner").nth(1);
    await expect(typed).toHaveAttribute("data-modality", "typed");
    await expect(typed).toContainText("getypt · als getypte tekst opgeslagen · reden gegeven");
    await expect(conversation.getByTestId("turn-character").nth(2)).toContainText("donderdag om 10 uur");
    await expect(conversation.getByTestId("turn-character").nth(2)).toHaveAttribute("data-source", "fixed_line");
    const panel = step.getByTestId("appointment-panel");
    await expect(panel).toContainText("✓ reden gegeven");

    await input.fill("Donderdag om tien uur is goed.");
    await step.getByTestId("typed-send").click();
    await expect(panel).toContainText("✓ nieuw moment: donderdag 24 september om 10 uur");
    await expect(conversation.getByTestId("turn-character").nth(3)).toContainText("Uw nieuwe afspraak is op donderdag 24 september om 10 uur");

    await input.fill("Ja, dat past. Tot dan!");
    await step.getByTestId("typed-send").click();
    await expect(panel).toContainText("✓ bevestigd");
    await expect(step.getByTestId("step-status")).toContainText("Doel bereikt");
    await expect(step.getByTestId("typed-send")).toBeDisabled();

    // the speaking skill record moved on
    await expect(page.getByTestId("skill-records")).toContainText("Spreken: practised");
    // the sidebar marks the step as completed
    await expect(page.getByRole("button", { name: /Spreken: het telefoongesprek/ })).toContainText("✓");
  });

  test("a reload resumes the session with its turns", async ({ page }) => {
    await page.goto("/missions/appointment-change");
    await expect(page.getByTestId("session-id")).toContainText(/[0-9a-f-]{36}/);
    await page.getByRole("button", { name: /Spreken: het telefoongesprek/ }).click();
    const step = page.locator('[data-step="speak-call"]');
    await expect(step.getByTestId("turn-learner")).toHaveCount(4);
    await expect(step.getByTestId("appointment-panel")).toContainText("✓ bevestigd");
    await expect(step.getByTestId("step-status")).toContainText("Doel bereikt");
  });

  test("the checkpoint takes speech only, offers no help and states its one attempt", async ({ page }) => {
    await page.goto("/missions/appointment-change");
    await page.getByRole("button", { name: /Controle: de kapper/ }).click();
    const step = page.locator('[data-step="checkpoint-transfer"]');
    await expect(step).toHaveAttribute("data-step-type", "checkpoint");
    await expect(step.getByTestId("checkpoint-rules")).toContainText("één poging");
    await step.getByTestId("start-conversation").click();
    await expect(step.getByTestId("conversation").getByTestId("turn-character").first()).toContainText("Kapsalon Lies");
    await expect(step.getByTestId("typed-disabled")).toBeVisible();
    await expect(step.getByTestId("typed-input")).toHaveCount(0);
    await expect(step.locator('[data-help="disabled"]')).toBeVisible();
    await expect(step.getByTestId("talk-button")).toBeEnabled();
  });
});
