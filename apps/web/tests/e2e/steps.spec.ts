import { expect, test } from "@playwright/test";

/** Listening and writing steps, help-ladder evidence and the export, against the fixture providers. */
test.describe("listening and writing steps", () => {
  test.describe.configure({ mode: "serial" });

  test("the listening step plays the labelled clip and records the answer", async ({ page }) => {
    await page.goto("/missions/appointment-change");
    await page.getByRole("button", { name: /Luisteren: de voicemail/ }).click();
    const step = page.locator('[data-step="listen-voicemail"]');
    await step.getByTestId("play-clip").click();
    await expect(step.getByTestId("clip-label")).toContainText("Synthetische luisterstem");
    await expect(step.getByTestId("play-count")).toContainText("1× beluisterd");
    await step.getByTestId("toggle-transcript").click();
    await expect(step.getByTestId("transcript")).toContainText("Tandarts De Smet is woensdag ziek");

    await step.getByRole("radio", { name: /De tandarts is ziek/ }).check();
    await step.getByTestId("listen-voicemail-check").click();
    await expect(step.getByTestId("score")).toHaveText("1 van 1 juist");
    await expect(step.getByTestId("listen-voicemail-done")).toBeVisible();
    await expect(page.getByTestId("skill-records")).toContainText("Luisteren: Geoefend");
  });

  test("the writing step autosaves the draft and submits typed evidence", async ({ page }) => {
    await page.goto("/missions/appointment-change");
    await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
    const step = page.locator('[data-step="write-message"]');
    const input = step.getByTestId("writing-input");
    await input.fill("Beste tandarts, ik kan woensdag niet");
    await expect(step.getByTestId("word-count")).toContainText("6 woorden (25–80 nodig)");
    await expect(step.getByTestId("missing-words")).toContainText("afspraak");
    await expect(step.getByTestId("autosave-status")).toContainText("bewaard", { timeout: 10_000 });
    await expect(step.getByTestId("writing-submit")).toBeDisabled();

    const message =
      "Beste tandarts De Smet, ik kan woensdag niet komen naar de praktijk omdat ik moet werken. " +
      "Kan ik een nieuwe afspraak maken op donderdag of vrijdag? Bedankt en tot binnenkort. Groeten, Mahmoud";
    await input.fill(message);
    await expect(step.getByTestId("writing-submit")).toBeEnabled();
    await step.getByTestId("writing-submit").click();
    await expect(step.getByTestId("writing-done")).toBeVisible();
    await expect(step.getByTestId("writing-notice")).toContainText("Alle vereiste woorden staan erin");
    await expect(page.getByTestId("skill-records")).toContainText("Schrijven: Geoefend");

    // a reload shows the submitted draft again
    await page.reload();
    await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
    await expect(page.locator('[data-step="write-message"]').getByTestId("writing-input")).toHaveValue(message);
    await expect(page.locator('[data-step="write-message"]').getByTestId("writing-done")).toBeVisible();
  });

  test("opening a help rung is recorded as evidence and the export contains everything", async ({ page }) => {
    await page.goto("/missions/appointment-change");
    const ladder = page.locator('[data-step="read-reminder"] .help-ladder').last();
    await ladder.getByRole("button", { name: /Hulp niveau 1/ }).click();
    await expect(ladder).toHaveAttribute("data-help-revealed", "1");

    const response = await page.request.get("/api/export");
    expect(response.status()).toBe(200);
    expect(response.headers()["content-disposition"]).toContain("learner-export-");
    const body = (await response.json()) as {
      sessions: { mission_id: string; variant: string; evidence: { kind: string; step_key: string }[]; feedback: unknown[] }[];
      skill_records: { mission_id: string; skill: string; status: string }[];
    };
    const base = body.sessions.find((s) => s.variant === "base" && s.mission_id === "appointment-change");
    expect(base).toBeTruthy();
    const kinds = new Set(base!.evidence.map((e) => e.kind));
    expect(kinds.has("answer")).toBe(true);
    expect(kinds.has("typed_text")).toBe(true);
    expect(base!.evidence.some((e) => e.kind === "help_used" && e.step_key === "read-reminder")).toBe(true);
    expect(base!.feedback.length).toBeGreaterThanOrEqual(1);
    expect(body.skill_records.filter((r) => r.status === "practised" && r.mission_id === "appointment-change").map((r) => r.skill).sort()).toEqual(["listening", "reading", "speaking", "writing"]);
  });
});
