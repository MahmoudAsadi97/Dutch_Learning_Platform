import AxeBuilder from "@axe-core/playwright";
import type { Page, Route, TestInfo } from "@playwright/test";
import { expect, test } from "./fixtures/test";

/**
 * Practice sessions (roadmap 3.6): a mocked session run by keyboard, checked with axe and for overflow at
 * 1440, 390 and 320 in every state; then a real-API session through the proxy, which also measures the answer
 * round trip (p95 at or under 300 ms); and the way in from Today while an episode is written.
 */

const options = [
  { id: "aaaa", nl: "de deur" },
  { id: "bbbb", nl: "het raam" },
  { id: "cccc", nl: "de sleutel" },
  { id: "dddd", nl: "de trap" },
];
const support = options.map((option, index) => ({
  ...option,
  en: ["the door", "the window", "the key", "the stairs"][index],
  fa: ["در", "پنجره", "کلید", "پله"][index],
}));

function sessionView() {
  return {
    id: "mock-session",
    source: "stage_skill",
    stage_id: "a1",
    focus: "words",
    library_topic: null,
    status: "active",
    content_status: "unreviewed",
    resumed: false,
    items: [
      {
        id: "intro",
        position: 0,
        kind: "intro",
        skill: "",
        state: "open",
        attempts_left: 2,
        prompt: {
          kind: "intro",
          words: [
            {
              term: "het raam",
              meaning: { nl: "opening in een muur", en: "the window", fa: "پنجره" },
              example: { nl: "Ik open het raam.", en: "I open the window.", fa: "پنجره را باز می‌کنم." },
            },
          ],
        },
        feedback: null,
      },
      {
        id: "item-1",
        position: 1,
        kind: "choice",
        skill: "vocabulary",
        state: "open",
        attempts_left: 2,
        prompt: { kind: "choice", direction: "term", stem: { en: "the window", fa: "پنجره" }, options },
        feedback: null,
      },
      {
        id: "item-2",
        position: 2,
        kind: "cloze_choice",
        skill: "vocabulary",
        state: "open",
        attempts_left: 2,
        prompt: {
          kind: "cloze_choice",
          sentence: "Ik open ___ want het is warm.",
          cue: { en: "I open the window because it is warm.", fa: "پنجره را باز می‌کنم چون گرم است." },
          options,
        },
        feedback: null,
      },
    ],
    next_item_id: "intro",
    progress: { closed: 0, total: 2, queued: 0 },
    summary: null,
  };
}

const card = {
  library_id: "a1-v1",
  term: "het raam",
  meaning: { nl: "opening in een muur", en: "the window", fa: "پنجره" },
  example: { nl: "Ik open het raam want het is warm.", en: "I open the window because it is warm.", fa: "" },
};

async function mockSession(page: Page) {
  const posts: { url: string; body: unknown }[] = [];
  let closed = 0;
  await page.route(/\/api\/exercises\/sessions(\/|$)/, async (route: Route) => {
    const request = route.request();
    const url = request.url();
    const body = request.postDataJSON();
    posts.push({ url, body });
    if (url.endsWith("/api/exercises/sessions")) return route.fulfill({ status: 201, json: sessionView() });
    if (url.endsWith("/finish"))
      return route.fulfill({
        json: {
          id: "mock-session",
          status: "finished",
          points: 5,
          summary: {
            items_total: 2,
            answered: 2,
            first_try_correct: 1,
            fixed_on_retry: 0,
            skipped: 0,
            overridden: 0,
            points_earned: 7,
            session_bonus: 5,
            by_kind: {},
            missed: [{ ref: "word:a1-v1", term: "het raam", expected: "het raam" }],
            suggestions: [{ key: "raam", term: "het raam", meaning_en: "the window", meaning_fa: "پنجره" }],
          },
        },
      });
    const itemId = url.split("/items/")[1]?.split("/")[0];
    if (url.endsWith("/report")) return route.fulfill({ json: { item_id: itemId, reason: body.reason } });
    if (itemId === "intro")
      return route.fulfill({
        json: {
          item_id: "intro",
          attempt: 1,
          outcome: "done",
          closed: true,
          requeue: false,
          attempts_left: 0,
          feedback: { outcome: "done" },
          points: 0,
          progress: { closed: 0, total: 2, queued: 0 },
          next_item_id: "item-1",
        },
      });
    closed += 1;
    const right = body.answer?.option === "bbbb";
    return route.fulfill({
      json: {
        item_id: itemId,
        attempt: 1,
        outcome: right ? "correct" : "incorrect",
        closed: true,
        requeue: false,
        attempts_left: 0,
        feedback: {
          outcome: right ? "correct" : "incorrect",
          correct: "bbbb",
          given: body.answer?.option ?? null,
          support,
          word: card,
          sentence: itemId === "item-2" ? card.example.nl : null,
        },
        points: 1,
        progress: { closed, total: 2, queued: 0 },
        next_item_id: itemId === "item-1" ? "item-2" : null,
      },
    });
  });
  return posts;
}

async function checkWidths(page: Page, testInfo: TestInfo, name: string) {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: width <= 390 ? 844 : 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    await testInfo.attach(`${name}-${width}`, {
      body: JSON.stringify(results.violations, null, 2),
      contentType: "application/json",
    });
    expect(results.violations).toEqual([]);
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
}

test("a mocked session runs by keyboard, in focus mode, accessible at every width", async ({
  page,
}, testInfo) => {
  const posts = await mockSession(page);
  await page.goto("/oefenen");
  await expect(page.getByRole("heading", { level: 1, name: "Oefenen" })).toBeVisible();
  // focus mode: no sidebar and no bottom tabs
  await expect(page.locator(".app-frame.is-bare")).toBeVisible();
  await expect(page.locator(".app-sidebar")).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: /hoofdmenu/i })).toHaveCount(0);
  expect(posts[0].body).toMatchObject({
    kinds: [
      "choice",
      "cloze_choice",
      "odd_one_out",
      "match_pairs",
      "de_het",
      "sentence_builder",
      "sentence_order",
    ],
    focus: "words",
  });

  await expect(page.getByRole("heading", { name: "Nieuwe woorden" })).toBeFocused();
  await checkWidths(page, testInfo, "intro");
  await page.getByRole("button", { name: "Begin met oefenen" }).click();

  const question = page.getByRole("heading", { name: "Welk Nederlands woord past bij deze betekenis?" });
  await expect(question).toBeFocused();
  // the Dutch options carry no glosses before the answer
  await expect(page.locator(".answer-option [lang=en]")).toHaveCount(0);
  await checkWidths(page, testInfo, "question");
  await page.keyboard.press("1");
  await expect(page.getByRole("radio", { name: "de deur" })).toBeChecked();
  await page.keyboard.press("Enter");

  const next = page.getByRole("button", { name: "Verder" });
  await expect(next).toBeFocused();
  await expect(page.getByRole("region", { name: /Nog niet/ })).toBeVisible();
  await expect(page.getByRole("radio", { name: /de deur Jouw antwoord/ })).toBeDisabled();
  await expect(page.getByRole("radio", { name: /het raam Het juiste antwoord/ })).toBeVisible();
  await expect(page.locator(".answer-option [lang=en]").first()).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: "Nog niet" })).toHaveCount(1);
  await checkWidths(page, testInfo, "feedback");

  // reporting changes nothing in the session
  await page.getByRole("button", { name: "Meld een probleem" }).click();
  const report = page.getByRole("dialog", { name: "Klopt er iets niet?" });
  await report.getByRole("radio", { name: "De vraag is niet duidelijk" }).check();
  await checkWidths(page, testInfo, "report");
  await report.getByRole("button", { name: "Verstuur" }).click();
  await expect(report.getByText("Bedankt. We bekijken deze oefening.")).toBeVisible();
  await report.getByRole("button", { name: "Sluiten" }).last().click();
  await expect(report).toBeHidden();
  await expect(page.getByRole("button", { name: "Meld een probleem" })).toBeFocused();
  expect(posts.find((post) => post.url.endsWith("/report"))?.body).toMatchObject({ reason: "unclear" });

  await next.press("Enter");
  await expect(page.getByRole("heading", { name: "Welk woord past in de zin?" })).toBeFocused();
  await page.keyboard.press("2");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("region", { name: /Juist/ })).toBeVisible();
  await page.getByRole("button", { name: "Verder" }).press("Enter");

  await expect(page.getByRole("heading", { name: "Je oefening is klaar" })).toBeFocused();
  await expect(page.getByText("Waarvan 5 extra voor een hele sessie.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Bewaar het raam" })).toBeVisible();
  await checkWidths(page, testInfo, "summary");
});

function boardSession() {
  const view = sessionView();
  const board = (id: string, position: number, kind: string, prompt: Record<string, unknown>) => ({
    id,
    position,
    kind,
    skill: "vocabulary",
    state: "open",
    attempts_left: 2,
    prompt: { kind, ...prompt },
    feedback: null,
  });
  return {
    ...view,
    id: "mock-boards",
    items: [
      board("pairs", 0, "match_pairs", {
        left: [
          { id: "l1", nl: "de deur" },
          { id: "l2", nl: "het raam" },
        ],
        right: [
          { id: "r1", en: "the window", fa: "پنجره" },
          { id: "r2", en: "the door", fa: "در" },
        ],
      }),
      board("bins", 1, "de_het", {
        bins: ["de", "het"],
        options: [
          { id: "n1", nl: "huis" },
          { id: "n2", nl: "tafel" },
        ],
      }),
      board("tiles", 2, "sentence_builder", {
        tiles: [
          { id: "t2", nl: "woon" },
          { id: "t1", nl: "ik" },
          { id: "t3", nl: "in Gent" },
        ],
        end: ".",
        cue: { en: "I live in Ghent.", fa: "من در گنت زندگی می‌کنم." },
      }),
      board("order", 3, "sentence_order", {
        sentences: [
          { id: "s2", nl: "Dan eet ik een boterham." },
          { id: "s1", nl: "Ik sta om zeven uur op." },
        ],
      }),
    ],
    next_item_id: "pairs",
    progress: { closed: 0, total: 4, queued: 0 },
  };
}

const BOARD_FEEDBACK: Record<string, Record<string, unknown>> = {
  pairs: {
    pairs: {
      l1: { given: "r2", correct: "r2", ok: true },
      l2: { given: "r1", correct: "r1", ok: true },
    },
  },
  bins: {
    bins: {
      n1: { given: "de", correct: "het", ok: false },
      n2: { given: "de", correct: "de", ok: true },
    },
    cards: { n1: { ...card, term: "het huis" }, n2: { ...card, term: "de tafel" } },
  },
  tiles: { order: ["t1", "t2", "t3"], given_order: ["t1", "t2", "t3"], first_difference: null },
  order: {
    order: ["s1", "s2"],
    given_order: ["s1", "s2"],
    translation: { en: ["I get up at seven.", "Then I eat a sandwich."] },
  },
};

test("the boards are played by keyboard and answered whole, accessible at every width", async ({
  page,
}, testInfo) => {
  const answers: Record<string, unknown> = {};
  let closed = 0;
  await page.route(/\/api\/exercises\/sessions(\/|$)/, async (route: Route) => {
    const url = route.request().url();
    if (url.endsWith("/api/exercises/sessions")) return route.fulfill({ status: 201, json: boardSession() });
    const itemId = url.split("/items/")[1]?.split("/")[0] ?? "";
    if (url.endsWith("/finish"))
      return route.fulfill({
        json: {
          id: "mock-boards",
          status: "finished",
          points: 0,
          summary: {
            items_total: 4,
            answered: 4,
            first_try_correct: 3,
            fixed_on_retry: 0,
            skipped: 0,
            overridden: 0,
            points_earned: 4,
            session_bonus: 0,
            by_kind: {},
            missed: [],
            suggestions: [],
          },
        },
      });
    answers[itemId] = route.request().postDataJSON().answer;
    closed += 1;
    const order = ["pairs", "bins", "tiles", "order"];
    const outcome = itemId === "bins" ? "incorrect" : "correct";
    return route.fulfill({
      json: {
        item_id: itemId,
        attempt: 1,
        outcome,
        closed: true,
        requeue: false,
        attempts_left: 0,
        feedback: { outcome, ...BOARD_FEEDBACK[itemId] },
        points: 1,
        progress: { closed, total: 4, queued: 0 },
        next_item_id: order[order.indexOf(itemId) + 1] ?? null,
      },
    });
  });
  await page.goto("/oefenen");
  const check = page.getByRole("button", { name: "Controleer" });
  const next = page.getByRole("button", { name: "Verder" });

  // match pairs: choose a word, then its meaning; checking too early asks to finish first
  await expect(page.getByRole("heading", { name: "Welke betekenis hoort bij welk woord?" })).toBeFocused();
  await checkWidths(page, testInfo, "pairs");
  await page.getByRole("button", { name: /^de deur/ }).press("Enter");
  await page.getByRole("button", { name: /^the door/ }).press("Enter");
  await check.click();
  await expect(page.locator(".exercise-nudge")).toHaveText(/Maak eerst alles af./);
  await page.getByRole("button", { name: /^het raam/ }).press("Enter");
  await page.getByRole("button", { name: /^the window/ }).press("Enter");
  await check.click();
  await expect(next).toBeFocused();
  expect(answers.pairs).toEqual({ pairs: { l1: "r2", l2: "r1" } });
  await checkWidths(page, testInfo, "pairs-feedback");
  await next.press("Enter");

  // de or het: native radios
  await expect(page.getByRole("heading", { name: "De of het?" })).toBeFocused();
  await checkWidths(page, testInfo, "bins");
  await page.getByRole("group", { name: "huis" }).getByRole("radio", { name: "de" }).check();
  await page.getByRole("group", { name: "tafel" }).getByRole("radio", { name: "de" }).check();
  await check.click();
  await expect(page.getByText("het huis")).toBeVisible();
  expect(answers.bins).toEqual({ bins: { n1: "de", n2: "de" } });
  await checkWidths(page, testInfo, "bins-feedback");
  await next.press("Enter");

  // the sentence builder: the pieces by keyboard, focus staying among them
  await expect(page.getByRole("heading", { name: "Maak de zin." })).toBeFocused();
  await checkWidths(page, testInfo, "tiles");
  const pieces = page.getByRole("group", { name: "Stukjes" });
  await pieces.getByRole("button", { name: "ik" }).press("Enter");
  await expect(pieces.getByRole("button", { name: "in Gent" })).toBeFocused();
  await page.keyboard.press("Enter");
  await page
    .getByRole("group", { name: "Jouw zin" })
    .getByRole("button", { name: "Leg in Gent terug" })
    .press("Enter");
  await pieces.getByRole("button", { name: "woon" }).press("Enter");
  await pieces.getByRole("button", { name: "in Gent" }).press("Enter");
  await check.click();
  expect(answers.tiles).toEqual({ order: ["t1", "t2", "t3"] });
  await checkWidths(page, testInfo, "tiles-feedback");
  await next.press("Enter");

  // putting sentences in order: up and down buttons
  await expect(page.getByRole("heading", { name: "Zet de zinnen in de goede volgorde." })).toBeFocused();
  await checkWidths(page, testInfo, "order");
  await page.getByRole("button", { name: "Zet zin 1 lager" }).press("Enter");
  await expect(page.getByRole("button", { name: "Zet zin 2 hoger" })).toBeFocused();
  await check.click();
  expect(answers.order).toEqual({ order: ["s1", "s2"] });
  await expect(page.getByText("Then I eat a sandwich.")).toBeVisible();
  await checkWidths(page, testInfo, "order-feedback");
  await next.press("Enter");
  await expect(page.getByRole("heading", { name: "Je oefening is klaar" })).toBeFocused();
});

test("Escape asks before stopping, closing gives focus back, and the session stays", async ({
  page,
}, testInfo) => {
  await mockSession(page);
  await page.goto("/oefenen");
  await page.getByRole("button", { name: "Begin met oefenen" }).click();
  await expect(page.getByRole("heading", { name: /Welk Nederlands woord/ })).toBeFocused();
  await page.keyboard.press("Escape");
  const dialog = page.getByRole("dialog", { name: "Stoppen met oefenen?" });
  await expect(dialog).toBeVisible();
  await checkWidths(page, testInfo, "exit");
  await dialog.getByRole("button", { name: "Blijf oefenen" }).click();
  await expect(dialog).toBeHidden();
  await page.getByRole("button", { name: "Stoppen" }).click();
  await expect(dialog).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(page.getByRole("button", { name: "Stoppen" })).toBeFocused();
  await page.getByRole("button", { name: "Stoppen" }).click();
  await dialog.getByRole("link", { name: "Naar Vandaag" }).click();
  await expect(page).toHaveURL(/\/$/);
});

test("a real session runs through the proxy with quick answers", async ({ page }, testInfo) => {
  const timings: number[] = [];
  page.on("requestfinished", (request) => {
    if (/\/api\/exercises\/sessions\/[^/]+\/items\/[^/]+\/answer$/.test(request.url())) {
      const timing = request.timing();
      if (timing.responseEnd > 0) timings.push(timing.responseEnd - Math.max(timing.requestStart, 0));
    }
  });
  await page.goto("/oefenen?bron=wachten");
  await expect(page.getByRole("heading", { level: 1, name: "Oefenen" })).toBeVisible();
  for (let step = 0; step < 30; step += 1) {
    const done = page.getByRole("heading", { name: "Je oefening is klaar" });
    if (await done.isVisible()) break;
    const start = page.getByRole("button", { name: "Begin met oefenen" });
    const next = page.getByRole("button", { name: "Verder" });
    if (await start.isVisible()) {
      await start.click();
      await expect(start).toBeHidden();
    } else if (await next.isVisible()) {
      await next.click();
      await expect(next).toBeHidden();
    } else {
      const skip = page.getByRole("button", { name: "Ik weet het niet" });
      if (!(await skip.isVisible())) {
        await page.waitForTimeout(100);
        continue;
      }
      // an option is answered (and timed); a board is skipped, which this smoke does not time
      const option = page.locator(".answer-option input").first();
      if (await option.isVisible()) {
        await option.check();
        await page.getByRole("button", { name: "Controleer" }).click();
      } else await skip.click();
      await expect(page.getByRole("button", { name: "Verder" })).toBeVisible();
    }
  }
  await expect(page.getByRole("heading", { name: "Je oefening is klaar" })).toBeVisible();
  expect(timings.length).toBeGreaterThan(2);
  const sorted = [...timings].sort((a, b) => a - b);
  const p95 = sorted[Math.min(sorted.length, Math.ceil(0.95 * sorted.length)) - 1];
  testInfo.annotations.push({ type: "answer round trip p95 (ms)", description: p95.toFixed(0) });
  expect(p95).toBeLessThanOrEqual(300);
});

test("Today offers practice while an episode is written", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const pending = page.getByText("De schrijver is bezig…");
  test.skip(!(await pending.isVisible()), "the first episode is not pending in this run");
  const link = page.getByRole("link", { name: "Oefen terwijl je wacht" });
  await expect(link).toHaveAttribute("href", "/oefenen?bron=wachten");
  await link.click();
  await expect(page.getByRole("heading", { level: 1, name: "Oefenen" })).toBeVisible();
});
