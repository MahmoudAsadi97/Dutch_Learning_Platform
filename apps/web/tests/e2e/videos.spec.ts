import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

/** Browser checks for the video lessons. Route fixtures drive the states a learner meets and serve a
 * three-second WebM (headless Chromium decodes VP9, not H.264); the API suite proves the engine. One unmocked
 * check proves the real request path. */

const videoId = "22222222-3333-4444-8555-666666666666";
const scenes = [
  { nl: "Goeiemorgen! Vandaag gaan we naar de markt. De markt is op zaterdag.", en: "Good morning! Today we go to the market. The market is on Saturday.", fa: "صبح بخیر! امروز به بازار می‌رویم.", keyword: "de markt" },
  { nl: "Op de markt koop ik groenten en fruit. De appels zijn lekker en niet duur.", en: "At the market I buy vegetables and fruit.", fa: "در بازار سبزی و میوه می‌خرم.", keyword: "groenten en fruit" },
  { nl: "Tot morgen! Probeer het zelf.", en: "See you tomorrow! Try it yourself.", fa: "تا فردا!", keyword: "tot morgen" },
];
const cues = [
  { start: 0, end: 1, text: "Goeiemorgen! Vandaag gaan we naar de markt.", scene: 0 }, { start: 1, end: 1.6, text: "De markt is op zaterdag.", scene: 0 },
  { start: 1.6, end: 2.4, text: "Op de markt koop ik groenten en fruit.", scene: 1 }, { start: 2.4, end: 3, text: "Tot morgen! Probeer het zelf.", scene: 2 },
];
const glossary = [
  { term: "de markt", meaning_en: "the market", meaning_fa: "بازار", example: "Vandaag gaan we naar de markt." },
  { term: "duur", meaning_en: "expensive", meaning_fa: "گران", example: "De appels zijn lekker en niet duur." },
];
const questions = [
  { index: 0, prompt: "Wanneer is de markt?", options: ["Op maandag.", "Op zaterdag.", "Op zondag."] },
  { index: 1, prompt: "Wat koop ik op de markt?", options: ["Brood.", "Groenten en fruit.", "Vis."] },
];

function video(overrides: Record<string, unknown> = {}) {
  return { id: videoId, stage_id: "a1", kind: "uitleg", kind_label: "Uitleg", topic: "op de markt", topic_id: "", status: "ready", error_code: "",
    title: "Op de markt", word_count: 72, duration_seconds: 3, presenter: "avatar", renderer: "azure-avatar", attempts: 1, watched_at: null, rating: 0,
    created_at: "2026-10-02T07:00:00Z", ready_at: "2026-10-02T07:04:00Z", content_status: "generated", warnings: [], failure_reasons: [], scene_count: 3,
    scenes, glossary, cues, questions, answered: false, provider: "azure-strong", model: "gpt-4.1-mini", voice: "nl-BE-DenaNeural",
    media_url: `videos/${videoId}/media`, subtitles_url: `videos/${videoId}/subtitles.vtt`, ...overrides };
}
function library(items: Record<string, unknown>[]) {
  return { items, levels: [{ id: "pre-a1", label: "pre-A1" }, { id: "a1", label: "A1" }, { id: "a2", label: "A2" }],
    kinds: [{ id: "uitleg", label: "Uitleg" }, { id: "verhaal", label: "Verhaal" }], default_stage: "a1",
    renderer: { name: "azure-avatar", label: "avatar", voice: "nl-BE-DenaNeural" }, min_seconds: 20, max_seconds: 150, max_pending: 2 };
}
const vtt = "WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\nGoeiemorgen! Vandaag gaan we naar de markt.\n\n2\n00:00:01.000 --> 00:00:01.600\nDe markt is op zaterdag.\n\n3\n00:00:01.600 --> 00:00:02.400\nOp de markt koop ik groenten en fruit.\n\n4\n00:00:02.400 --> 00:00:03.000\nTot morgen! Probeer het zelf.\n";

async function videoFixture(page: Page) {
  let state = video();
  const posts: string[] = [];
  await page.route(/\/api\/videos\/[^/]+\/media(?:\?|$)/, route => route.fulfill({ path: path.join(__dirname, "fixtures", "lesson.webm"), contentType: "video/webm", headers: { "accept-ranges": "bytes" } }));
  await page.route(/\/api\/videos\/[^/]+\/subtitles\.vtt(?:\?|$)/, route => route.fulfill({ body: vtt, contentType: "text/vtt; charset=utf-8" }));
  await page.route(/\/api\/videos\/[^/]+(?:\/(?:watched|answers|rating|words|retry))?(?:\?|$)/, async route => {
    const url = new URL(route.request().url());
    const action = url.pathname.split(`/videos/${videoId}`)[1] ?? "";
    if (route.request().method() === "GET") { await route.fulfill({ json: state }); return; }
    posts.push(action);
    const body = (route.request().postDataJSON() ?? {}) as Record<string, unknown>;
    if (action === "/watched") state = { ...state, watched_at: "2026-10-02T08:00:00Z" };
    if (action === "/answers") {
      const chosen = body.answers as Record<string, number>;
      state = { ...state, watched_at: "2026-10-02T08:00:00Z", answered: true, questions: [
        { ...questions[0], answer_index: 1, evidence: "De markt is op zaterdag.", chosen: chosen["0"], correct: chosen["0"] === 1 },
        { ...questions[1], answer_index: 1, evidence: "Op de markt koop ik groenten en fruit.", chosen: chosen["1"], correct: chosen["1"] === 1 },
      ] };
    }
    if (action === "/rating") state = { ...state, rating: Number(body.rating) };
    if (action === "/words") { await route.fulfill({ json: { item: { id: "w1", term: String(body.term) }, created: true } }); return; }
    await route.fulfill({ json: state });
  });
  return { posts, current: () => state };
}

test("the library lists videos in every state and takes a request", async ({ page }) => {
  const items = [video({ watched_at: null }), video({ id: "r1", status: "rendering", title: "", topic: "bij de dokter", kind: "verhaal", kind_label: "Verhaal", duration_seconds: 0 }),
    video({ id: "f1", status: "failed", error_code: "quality", title: "", topic: "op het station", failure_reasons: ["sentence_too_long: 18 words (limit 12)"], duration_seconds: 0 })];
  const requests: Record<string, unknown>[] = [];
  await page.route(/\/api\/videos(?:\?|$)/, async route => {
    if (route.request().method() === "POST") {
      requests.push(route.request().postDataJSON() as Record<string, unknown>);
      await route.fulfill({ status: 201, json: video({ id: "n1", status: "queued", title: "", topic: "een afspraak bij de kapper" }) });
      return;
    }
    await route.fulfill({ json: library(items) });
  });
  await page.goto("/videos");
  const page_ = page.getByTestId("video-library");
  await expect(page_.getByRole("heading", { level: 1 })).toContainText("Een korte video op jouw niveau");
  const tiles = page_.getByTestId("video-tile");
  await expect(tiles).toHaveCount(3);
  await expect(tiles.nth(0)).toContainText("Op de markt");
  await expect(tiles.nth(0).getByRole("link", { name: "Bekijk" })).toHaveAttribute("href", `/videos/${videoId}`);
  await expect(tiles.nth(1)).toContainText("de video wordt gemaakt");
  await expect(tiles.nth(2)).toContainText("Het script haalde de automatische controle niet");
  await tiles.nth(2).getByText("Wat er niet klopte").click();
  await expect(tiles.nth(2).getByText("sentence_too_long: 18 words (limit 12)")).toBeVisible();
  await expect(tiles.nth(2).getByRole("button", { name: "Opnieuw proberen" })).toBeVisible();
  await page_.getByTestId("video-level").selectOption("a2");
  await page_.getByTestId("video-kind").selectOption("verhaal");
  await page_.getByTestId("video-topic").fill("een afspraak bij de kapper");
  await page_.getByTestId("video-submit").click();
  await expect(page_.getByText("De schrijver is begonnen.")).toBeVisible();
  expect(requests).toEqual([expect.objectContaining({ stage_id: "a2", kind: "verhaal", topic: "een afspraak bij de kapper" })]);
  const scan = await new AxeBuilder({ page }).include("#main").analyze();
  expect(scan.violations.filter(v => ["critical", "serious"].includes(v.impact ?? ""))).toEqual([]);
});

test("watching a video: subtitles, transcript follows the playhead, questions, a saved word, a rating", async ({ page }) => {
  const fixture = await videoFixture(page);
  await page.goto(`/videos/${videoId}`);
  const lesson = page.getByTestId("video-lesson");
  await expect(lesson.getByRole("heading", { level: 1 })).toHaveText("Op de markt");
  const element = lesson.getByTestId("video-element");
  await expect(element.locator("track")).toHaveAttribute("src", `/api/videos/${videoId}/subtitles.vtt`);
  await expect(lesson.getByTestId("video-scene")).toHaveCount(3);
  await expect(lesson.getByText("Good morning! Today we go to the market. The market is on Saturday.")).toBeVisible();
  await expect(lesson.getByText("Virtuele presentator en synthetische stem")).toBeVisible();
  await expect(lesson.getByRole("heading", { name: "Twee vragen over de video" })).toHaveCount(0);

  // The transcript follows the playhead and a scene button seeks to its first cue.
  await lesson.getByRole("button", { name: "Ga naar scène 3" }).click();
  await expect.poll(() => element.evaluate(node => Math.round((node as HTMLVideoElement).currentTime * 10) / 10)).toBeGreaterThanOrEqual(2.4);
  await expect(lesson.getByTestId("video-scene").nth(2)).toHaveAttribute("aria-current", "true");
  await element.evaluate(node => { (node as HTMLVideoElement).pause(); (node as HTMLVideoElement).currentTime = 1.2; });
  await expect(lesson.getByTestId("video-scene").nth(0)).toHaveAttribute("aria-current", "true");
  await expect(lesson.getByTestId("video-scene").nth(2)).not.toHaveAttribute("aria-current", "true");

  await lesson.getByRole("button", { name: "Bewaar", exact: true }).first().click();
  await expect(lesson.getByText('"de markt" staat in je woordenlijst en komt terug op het juiste moment.')).toBeVisible();
  await lesson.getByTestId("finish-watching").click();
  await expect(lesson.getByRole("heading", { name: "Twee vragen over de video" })).toBeVisible();
  const check = lesson.getByRole("button", { name: "Controleer mijn antwoorden" });
  await expect(check).toBeDisabled();
  await lesson.getByRole("radiogroup", { name: "Wanneer is de markt?" }).getByLabel("Op zaterdag.").check();
  await lesson.getByRole("radiogroup", { name: "Wat koop ik op de markt?" }).getByLabel("Vis.").check();
  await check.click();
  await expect(lesson.getByRole("heading", { name: "1 van 2 juist" })).toBeVisible();
  await expect(lesson.getByText("In de video: “Op de markt koop ik groenten en fruit.”")).toBeVisible();
  const yes = lesson.getByRole("button", { name: "Ja", exact: true });
  await yes.click();
  await expect(yes).toHaveAttribute("aria-pressed", "true");
  expect(fixture.posts).toEqual(["/words", "/watched", "/answers", "/rating"]);
  expect(fixture.current().rating).toBe(1);
});

test("a video that is still being made or failed is explained, also on a phone", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route(/\/api\/videos\/[^/]+(?:\?|$)/, route => route.fulfill({ json: video({ status: "rendering", title: "", scenes: undefined }) }));
  await page.goto(`/videos/${videoId}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Deze video wordt nog gemaakt.");
  await page.unroute(/\/api\/videos\/[^/]+(?:\?|$)/);
  await page.route(/\/api\/videos\/[^/]+(?:\?|$)/, route => route.fulfill({ json: video({ status: "failed", error_code: "allowance_video", title: "" }) }));
  await page.goto(`/videos/${videoId}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Deze video is niet gelukt.");
  await expect(page.getByText("Je dagelijkse videotijd is op.")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.route(/\/api\/videos(?:\?|$)/, route => route.fulfill({ json: library([video()]) }));
  await page.goto("/videos");
  await expect(page.getByTestId("video-tile")).toHaveCount(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.getByRole("navigation", { name: "Mobiel hoofdmenu" }).getByRole("link", { name: "Video's" })).toBeVisible();
});

test("the real request path queues a video that the library then shows", async ({ page }) => {
  await page.goto("/videos");
  const page_ = page.getByTestId("video-library");
  await expect(page_.getByTestId("video-submit")).toBeEnabled();
  await page_.getByTestId("video-topic").fill("een regenachtige dag");
  await page_.getByTestId("video-submit").click();
  await expect(page_.getByText("De schrijver is begonnen.")).toBeVisible();
  const tile = page_.getByTestId("video-tile").filter({ hasText: "een regenachtige dag" });
  await expect(tile).toHaveCount(1);
  await expect(tile).toContainText(/wacht op de schrijver|het script wordt geschreven|de video wordt gemaakt/);
});
