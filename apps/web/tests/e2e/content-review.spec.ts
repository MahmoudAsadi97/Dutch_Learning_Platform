import { expect, test } from "@playwright/test";

const topic = (index: number, status = "not_requested") => ({id: `a2-t${String(index).padStart(3, "0")}`, title: {nl: `Redactiethema ${index}`, en: `Review topic ${index}`, fa: `موضوع ${index}`}, review: {status, issues: [], summary: "Nog door een taalreviewer te beoordelen.", error_code: "", updated_at: null}});

test("ordinary learners do not fetch or see the private editing queue", async ({page}) => {
  const requests: string[] = [];
  page.on("request", request => {if (request.url().includes("/content-review/")) requests.push(request.url());});
  // Prepare the catalogue before navigation: the negative assertion must not close
  // the page while an intercepted upstream request is still in flight.
  const catalogueResponse = await page.request.get("/api/curriculum");
  expect(catalogueResponse.ok()).toBeTruthy();
  const catalogue = {...await catalogueResponse.json(), admin_bypass: false};
  let catalogueHandled!: () => void;
  const handled = new Promise<void>(resolve => {catalogueHandled = resolve;});
  await page.route(/\/api\/curriculum$/, async route => {
    await route.fulfill({json: catalogue});
    catalogueHandled();
  });
  const catalogueLoaded = page.waitForResponse(/\/api\/curriculum$/);
  await page.goto("/settings");
  const loaded = await catalogueLoaded;
  expect((await loaded.json()).admin_bypass).toBe(false);
  await loaded.finished();
  await handled;
  await expect(page.getByRole("heading", {name: "Mijn leerprofiel"})).toBeVisible();
  await expect(page.getByRole("heading", {name: "Redactiewachtrij"})).toHaveCount(0);
  expect(requests).toEqual([]);
});

test("editor selects at most five topics and reviews suggestions without approval", async ({page}) => {
  await page.route(/\/api\/curriculum$/, async route => {
    const response = await route.fetch();
    const data = await response.json();
    await route.fulfill({json: {...data, admin_bypass: true, stages: data.stages.filter((stage: {id: string}) => stage.id === "a2")}});
  });
  const queued = new Set<string>();
  const posted: {topic_ids: string[]; retry_failed: boolean}[] = [];
  await page.route(/\/api\/content-review\/a2(?:\?|$)/, async route => {
    if (route.request().method() === "POST") {
      const body = route.request().postDataJSON();
      posted.push(body);
      body.topic_ids.forEach((id: string) => queued.add(id));
      await route.fulfill({json: {stage_id: "a2", items: []}});
      return;
    }
    const items = Array.from({length: 12}, (_, index) => topic(index + 1));
    for (const item of items) if (queued.has(item.id)) item.review.status = "needs_review";
    await route.fulfill({json: {stage_id: "a2", total: 100, offset: 0, limit: 12, items}});
  });
  await page.goto("/settings");
  const panel = page.locator(".content-review-panel");
  await expect(panel.getByRole("heading", {name: "Redactiewachtrij"})).toBeVisible();
  for (let index = 1; index <= 5; index++) await panel.getByRole("checkbox", {name: `Redactiethema ${index}`, exact: true}).check();
  await expect(panel.getByRole("checkbox", {name: "Redactiethema 6", exact: true})).toBeDisabled();
  await panel.getByRole("button", {name: "Controle aanvragen (5)", exact: true}).click();
  await expect(panel.getByText("Menselijke beoordeling nodig", {exact: true})).toHaveCount(5);
  expect(posted).toEqual([{topic_ids: ["a2-t001", "a2-t002", "a2-t003", "a2-t004", "a2-t005"], retry_failed: false}]);
  await panel.locator("summary").first().click();
  await expect(panel.getByText("Deze controle vond geen aandachtspunten. De inhoud is nog niet door een mens goedgekeurd.").first()).toBeVisible();
  await expect(panel.getByRole("button", {name: /goedkeuren/i})).toHaveCount(0);
});
