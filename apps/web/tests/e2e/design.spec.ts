import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const screens = [
  {
    name: "dashboard",
    path: "/",
    heading: "Kleine stappen. Echte gesprekken.",
  },
  { name: "progress", path: "/progress", heading: "Elke stap vertelt iets." },
  { name: "settings", path: "/settings", heading: "Jouw leeromgeving." },
  {
    name: "speech",
    path: "/speech-check",
    heading: "Jouw stem. Jouw Nederlands.",
  },
];

test("page scripts use a fresh CSP nonce and private caching", async ({ request }) => {
  const first = await request.get("/");
  const second = await request.get("/");
  const policy = first.headers()["content-security-policy"];
  expect(policy).toContain("frame-ancestors 'none'");
  expect(policy).not.toContain("script-src 'self' 'unsafe-inline'");
  const nonce = policy.match(/'nonce-([^']+)'/)?.[1];
  expect(nonce).toBeTruthy();
  expect(second.headers()["content-security-policy"]).not.toEqual(policy);
  expect(await first.text()).toContain(`nonce="${nonce}"`);
  expect(first.headers()["cache-control"]).toContain("no-store");
});

for (const screen of screens) {
  test(`${screen.name} is usable at desktop and phone width`, async ({
    page,
  }, testInfo) => {
    await page.goto(screen.path);
    await expect(
      page.getByRole("heading", { name: screen.heading }),
    ).toBeVisible();
    if (screen.name === "dashboard")
      await expect(page.getByTestId("curriculum-path").locator("li")).toHaveCount(12);
    if (screen.name === "progress")
      await expect(page.locator(".progress-card")).toHaveCount(4);
    if (screen.name === "settings")
      await expect(page.getByText("Technische ondersteuning", { exact: true })).toBeVisible();
    await page.evaluate(() => document.fonts.ready.then(() => undefined));
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: width <= 390 ? 844 : 1000 });
      await testInfo.attach(`${screen.name}-${width}`, {
        body: await page.screenshot({ fullPage: true }),
        contentType: "image/png",
      });
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      await testInfo.attach(`accessibility-${width}`, {
        body: JSON.stringify(results.violations, null, 2),
        contentType: "application/json",
      });
      expect(results.violations).toEqual([]);
    }
  });
}

test("primary navigation waits for a writing draft to be saved", async ({
  page,
}) => {
  await page.goto("/missions/appointment-change");
  await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
  await page.route("**/api/practice/sessions/*/drafts/write-message", (route) =>
    route.abort(),
  );
  await page
    .getByTestId("writing-input")
    .fill("Mijn bericht blijft bewaard als ik de pagina verlaat.");
  await page
    .getByRole("navigation", { name: "Hoofdmenu", exact: true })
    .getByRole("link", { name: "Mijn voortgang" })
    .click();
  await expect(page.getByTestId("writing-input")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Opnieuw bewaren" }),
  ).toBeVisible();
  await page.unroute("**/api/practice/sessions/*/drafts/write-message");
  await page
    .getByRole("navigation", { name: "Hoofdmenu", exact: true })
    .getByRole("link", { name: "Mijn voortgang" })
    .click();
  await expect(page).toHaveURL(/\/progress$/);
  await page.goto("/missions/appointment-change");
  await page.getByRole("button", { name: /Schrijven: het bericht/ }).click();
  await expect(page.getByTestId("writing-input")).toHaveValue(
    "Mijn bericht blijft bewaard als ik de pagina verlaat.",
  );
});

test("keyboard skip link reaches the page content", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Naar de inhoud" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main")).toBeFocused();
});

test("lesson screenshots and accessible controls", async ({
  page,
}, testInfo) => {
  await page.goto("/missions/appointment-change");
  await expect(page.getByTestId("reading-text")).toBeVisible();
  for (const step of [
    /Lezen: de herinnering/,
    /Luisteren:/,
    /Spreken:/,
    /Schrijven: het bericht/,
  ]) {
    await page.getByRole("button", { name: step }).first().click();
    await testInfo.attach(`lesson-${String(step).replace(/\W/g, "")}`, {
      body: await page.screenshot({ fullPage: true }),
      contentType: "image/png",
    });
  }
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
