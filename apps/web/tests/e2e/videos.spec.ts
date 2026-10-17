import { expect, test } from "./fixtures/test";

/** Legacy URLs stay useful without exposing a paid video creation workflow. */
for (const path of ["/videos", "/videos/22222222-3333-4444-8555-666666666666"]) {
  test(`${path} opens stories without requesting video services`, async ({ page }) => {
    const videoRequests: string[] = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname.startsWith("/api/videos")) videoRequests.push(request.url());
    });
    await page.goto(path);
    await expect(page).toHaveURL(/\/verhalen$/);
    await expect(page.locator("#main")).toBeVisible();
    await expect(page.getByTestId("video-submit")).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Video's", exact: true })).toHaveCount(0);
    expect(videoRequests).toEqual([]);
  });
}

test("a stale client cannot create a video through the API", async ({ page }) => {
  const response = await page.evaluate(async () => {
    const result = await fetch("/api/videos", {
      method: "POST",
      headers: { "X-Requested-With": "fetch", "Content-Type": "application/json" },
      body: JSON.stringify({
        request_id: "retired-video-browser",
        stage_id: "a1",
        topic: "de markt",
        kind: "verhaal",
      }),
    });
    return { status: result.status, body: await result.json() };
  });
  expect(response.status).toBe(410);
  expect(response.body.detail).toContain("retired");
});
