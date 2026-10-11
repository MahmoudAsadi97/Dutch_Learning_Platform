import { readFileSync } from "node:fs";
import path from "node:path";
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
      "listen_choose",
      "cloze_typed",
      "typed_recall",
      "dictation",
      "match_pairs",
      "de_het",
      "sentence_builder",
      "sentence_order",
      "shadow",
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
          { id: "n3", nl: "verantwoordelijkheid" },
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
      n3: { given: "het", correct: "de", ok: false },
    },
    cards: {
      n1: { ...card, term: "het huis" },
      n2: { ...card, term: "de tafel" },
      n3: { ...card, term: "de verantwoordelijkheid" },
    },
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
  await check.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("status").filter({ hasText: "Maak eerst alles af." })).toHaveCount(1);
  await expect(page.locator(".exercise-nudge")).toHaveText(/Maak eerst alles af./);
  await page.getByRole("button", { name: /^het raam/ }).press("Enter");
  await page.getByRole("button", { name: /^the window/ }).press("Enter");
  await check.focus();
  await page.keyboard.press("Enter");
  await expect(next).toBeFocused();
  expect(answers.pairs).toEqual({ pairs: { l1: "r2", l2: "r1" } });
  await checkWidths(page, testInfo, "pairs-feedback");
  await next.press("Enter");

  // de or het: native radios, by keyboard (Space chooses, the arrow moves to the other article)
  await expect(page.getByRole("heading", { name: "De of het?" })).toBeFocused();
  await checkWidths(page, testInfo, "bins");
  const huis = page.getByRole("group", { name: "huis" }).getByRole("radio", { name: "de" });
  await huis.focus();
  await page.keyboard.press("Space");
  await expect(huis).toBeChecked();
  await page.getByRole("group", { name: "tafel" }).getByRole("radio", { name: "de" }).focus();
  await page.keyboard.press("Space");
  const long = page.getByRole("group", { name: "verantwoordelijkheid" });
  await long.getByRole("radio", { name: "de" }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(long.getByRole("radio", { name: "het" })).toBeChecked();
  await expect(long.getByRole("radio", { name: "het" })).toBeFocused();
  await check.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByText("het huis")).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: "Nog niet" })).toHaveCount(1);
  expect(answers.bins).toEqual({ bins: { n1: "de", n2: "de", n3: "het" } });
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
  await check.focus();
  await page.keyboard.press("Enter");
  expect(answers.tiles).toEqual({ order: ["t1", "t2", "t3"] });
  await checkWidths(page, testInfo, "tiles-feedback");
  await next.press("Enter");

  // putting sentences in order: up and down buttons
  await expect(page.getByRole("heading", { name: "Zet de zinnen in de goede volgorde." })).toBeFocused();
  await checkWidths(page, testInfo, "order");
  await page.getByRole("button", { name: "Zet zin 1 lager" }).press("Enter");
  await expect(page.getByRole("button", { name: "Zet zin 2 hoger" })).toBeFocused();
  await check.focus();
  await page.keyboard.press("Enter");
  expect(answers.order).toEqual({ order: ["s1", "s2"] });
  await expect(page.getByText("Then I eat a sandwich.")).toBeVisible();
  await checkWidths(page, testInfo, "order-feedback");
  await next.press("Enter");
  await expect(page.getByRole("heading", { name: "Je oefening is klaar" })).toBeFocused();
});

function speechSession() {
  const view = sessionView();
  const ask = (id: string, position: number, kind: string, prompt: Record<string, unknown>) => ({
    id,
    position,
    kind,
    skill: kind === "shadow" ? "speaking" : "listening",
    state: "open",
    attempts_left: 2,
    prompt: { kind, ...prompt },
    feedback: null,
  });
  return {
    ...view,
    id: "mock-speech",
    items: [
      ask("listen", 0, "listen_choose", { options }),
      ask("dictation", 1, "dictation", { word_count: 4 }),
      ask("cloze", 2, "cloze_typed", {
        sentence: "Ik zeg ___ tegen Sam.",
        cue: { en: "I say goodbye to Sam.", fa: "به سام خداحافظ می‌گویم." },
        hint: { first: "t", letters: [3, 5] },
      }),
      ask("recall", 3, "typed_recall", {
        cue: { en: "the key", fa: "کلید" },
        hint: { first: "s", letters: [7] },
      }),
      ask("shadow", 4, "shadow", { sentence: "Ik woon in Gent." }),
    ],
    next_item_id: "listen",
    progress: { closed: 0, total: 5, queued: 0 },
  };
}

test("listening, typing and speaking items by keyboard, judged by the server and accessible at every width", async ({
  page,
}, testInfo) => {
  const sent: Record<string, unknown> = {};
  let audioRequests = 0;
  let takes = 0;
  const wav = readFileSync(path.resolve("tests/e2e/fixtures/speech-input.wav"));

  // a stand-in for the server: an answer moves its item as service.respond does (two attempts; a miss comes
  // back at the end; the first real answer earns the point), and an override as service.override does
  const server = speechSession();
  let nextItem: string | null = server.next_item_id;
  const lastFeedback: Record<string, Record<string, unknown>> = {};
  const itemOf = (id: string) => server.items.find((entry) => entry.id === id)!;
  const progress = () => ({
    closed: server.items.filter((entry) => entry.state === "closed").length,
    total: server.items.length,
    queued: server.items.filter((entry) => entry.state === "open" && entry.attempts_left < 2).length,
  });
  const verdict = (
    itemId: string,
    outcome: string,
    feedback: Record<string, unknown>,
    next: string | null,
    { closes = true, requeue = false }: { closes?: boolean; requeue?: boolean } = {},
  ) => {
    const entry = itemOf(itemId);
    const attempt = 3 - entry.attempts_left;
    entry.attempts_left = closes ? 0 : entry.attempts_left - 1;
    if (closes) entry.state = "closed";
    nextItem = next;
    lastFeedback[itemId] = { outcome, ...feedback };
    return {
      item_id: itemId,
      attempt,
      outcome,
      closed: closes,
      requeue,
      attempts_left: entry.attempts_left,
      feedback: lastFeedback[itemId],
      points: attempt === 1 ? 1 : 0,
      progress: progress(),
      next_item_id: next,
    };
  };
  const recallDiff = [
    { op: "same", expected: "de", given: "de" },
    { op: "changed", expected: "sleutel", given: "sleuter" },
  ];

  await page.route(/\/api\/exercises\/sessions(\/|$)/, async (route: Route) => {
    const request = route.request();
    const url = request.url();
    if (url.endsWith("/api/exercises/sessions")) return route.fulfill({ status: 201, json: speechSession() });
    if (request.method() === "GET")
      return route.fulfill({ json: { ...server, next_item_id: nextItem, progress: progress() } });
    const itemId = url.split("/items/")[1]?.split("/")[0] ?? "";
    if (url.endsWith("/audio")) {
      audioRequests += 1;
      return route.fulfill({
        body: wav,
        headers: { "content-type": "audio/wav", "x-audio-voice": "fixture-tone" },
      });
    }
    if (url.endsWith("/recording")) {
      takes += 1;
      sent[`take${takes}`] = request.postData()?.includes('name="audio"');
      // the first take is not heard (the item stays open for a second take at once), the second is
      return route.fulfill({
        json:
          takes === 1
            ? verdict(
                "shadow",
                "not_heard",
                { transcript: "", matched_words: 0, target_words: 4 },
                "shadow",
                {
                  closes: false,
                },
              )
            : verdict(
                "shadow",
                "heard",
                { transcript: "ik woon in gent", matched_words: 4, target_words: 4 },
                "recall",
              ),
      });
    }
    if (url.endsWith("/override")) {
      sent.override = itemId;
      // the item closes as accepted with the feedback it had; the override earns nothing, progress stays
      return route.fulfill({
        json: {
          item_id: itemId,
          attempt: 1,
          outcome: "accepted",
          closed: true,
          requeue: false,
          attempts_left: 0,
          feedback: { ...lastFeedback[itemId], outcome: "accepted", overridable: false },
          points: 0,
          progress: progress(),
          next_item_id: nextItem,
        },
      });
    }
    if (url.endsWith("/finish"))
      return route.fulfill({
        json: {
          id: "mock-speech",
          status: "finished",
          points: 0,
          summary: {
            items_total: 5,
            answered: 5,
            first_try_correct: 2,
            fixed_on_retry: 1,
            skipped: 0,
            overridden: 1,
            points_earned: 5,
            session_bonus: 0,
            by_kind: {},
            missed: [],
            suggestions: [],
          },
        },
      });
    const body = request.postDataJSON();
    sent[`${itemId}${itemOf(itemId).attempts_left < 2 ? "-again" : ""}`] = body;
    if (itemId === "listen")
      return route.fulfill({
        json: verdict("listen", "correct", { correct: "bbbb", given: "bbbb", support }, "dictation"),
      });
    if (itemId === "dictation")
      return route.fulfill({
        json: verdict(
          "dictation",
          "almost",
          {
            typed: "ik woon in gend",
            expected: "Ik woon in Gent.",
            notes: ["spelling"],
            diff: [
              { op: "same", expected: "ik", given: "ik" },
              { op: "same", expected: "woon", given: "woon" },
              { op: "same", expected: "in", given: "in" },
              { op: "changed", expected: "gent", given: "gend" },
            ],
            overridable: true,
          },
          "cloze",
        ),
      });
    if (itemId === "cloze")
      return route.fulfill({
        json: verdict("cloze", "correct", { typed: "tot ziens", expected: "tot ziens" }, "recall"),
      });
    // typed recall: missed at first (it comes back at the end), right the second time
    if (itemOf("recall").attempts_left === 2)
      return route.fulfill({
        json: verdict(
          "recall",
          "incorrect",
          {
            typed: "de sleuter",
            expected: "de sleutel",
            diff: recallDiff,
            overridable: true,
            word: { ...card, term: "de sleutel" },
          },
          "shadow",
          { closes: false, requeue: true },
        ),
      });
    return route.fulfill({
      json: verdict(
        "recall",
        "correct",
        { typed: "de sleutel", expected: "de sleutel", word: { ...card, term: "de sleutel" } },
        null,
      ),
    });
  });
  await page.goto("/oefenen");
  const next = page.getByRole("button", { name: "Verder" });
  const field = page.getByRole("textbox", { name: /Jouw antwoord/ });

  // listen and choose: the sound comes from the item's audio route; the options are Dutch
  const listenHeading = page.getByRole("heading", { name: "Welk woord hoor je?" });
  await expect(listenHeading).toBeFocused();
  await expect(page.getByRole("button", { name: "Ik kan nu niet luisteren" })).toBeVisible();
  await checkWidths(page, testInfo, "listen");
  await page.getByRole("button", { name: "Luister", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect.poll(() => audioRequests).toBe(1);
  await expect(page.getByText(/Testtoon/)).toBeVisible();
  await listenHeading.focus();
  await page.keyboard.press("2");
  await page.keyboard.press("Enter");
  await expect(next).toBeFocused();
  expect(sent.listen).toMatchObject({ answer: { option: "bbbb" } });
  await page.keyboard.press("Enter");

  // dictation: typed, judged tolerantly; "almost" is neutral, never in the miss colours
  await expect(page.getByRole("heading", { name: "Luister en typ wat je hoort." })).toBeFocused();
  await expect(field).toHaveAttribute("lang", "nl");
  await expect(field).toHaveAttribute("autocapitalize", "off");
  await field.focus();
  await page.keyboard.type("ik woon in gend");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("region", { name: /Bijna/ })).toBeVisible();
  await expect(next).toBeFocused();
  await expect(page.locator('.token-diff[data-outcome="almost"]')).toBeVisible();
  await expect(page.getByRole("insertion")).toContainText("gent");
  await expect(page.getByText("Een kleine tikfout.")).toBeVisible();
  await checkWidths(page, testInfo, "dictation-feedback");

  // the learner may say the answer is right too: focus stays on "Verder", the point stays on screen
  await next.focus();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Mijn antwoord klopt ook" })).toBeFocused();
  await page.keyboard.press("Enter");
  const accepted = page.getByRole("region", { name: /Je antwoord telt/ });
  await expect(accepted).toBeVisible();
  await expect(next).toBeFocused();
  await expect(accepted).toContainText("+1 punt");
  await expect(page.getByText(/Wat de controle verwachtte/)).toBeVisible();
  await expect(page.locator('.token-diff[data-outcome="accepted"]')).toBeVisible();
  expect(sent.override).toBe("dictation");
  await page.keyboard.press("Enter");

  // typed cloze of two words: the hint is asked for by keyboard, read out, and focus goes back to the field
  await expect(page.getByRole("heading", { name: "Typ de woorden die in de zin passen." })).toBeFocused();
  await page.getByRole("button", { name: "Toon een hint" }).focus();
  await page.keyboard.press("Enter");
  await expect(field).toBeFocused();
  const hint = "Het begint met t. Het zijn 2 woorden, met 3 + 5 letters.";
  await expect(page.getByRole("status").filter({ hasText: hint })).toBeVisible();
  await expect(field).toHaveAccessibleDescription(new RegExp(hint.replace(/[.+]/g, "\\$&")));
  await page.keyboard.type("tot ziens");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("region", { name: /Juist/ })).toBeVisible();
  expect(sent.cloze).toMatchObject({ answer: { text: "tot ziens" }, hint_used: true });
  await page.keyboard.press("Enter");

  // typed recall: missed, so it comes back at the end; the hint of the item before is not reported with it
  await expect(page.getByRole("heading", { name: "Typ het Nederlandse woord." })).toBeFocused();
  await field.focus();
  await page.keyboard.type("de sleuter");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("region", { name: /Nog niet/ })).toBeVisible();
  await expect(page.getByText("Deze vraag komt aan het einde nog één keer terug.")).toBeVisible();
  await expect(page.locator('.token-diff[data-outcome="incorrect"]')).toBeVisible();
  expect(sent.recall).toMatchObject({ answer: { text: "de sleuter" }, hint_used: false });
  await checkWidths(page, testInfo, "recall-feedback");
  await page.keyboard.press("Enter");

  // shadowing by keyboard: one press records, another stops (the fake microphone speaks); never a score
  const shadowHeading = page.getByRole("heading", { name: "Luister en zeg het na." });
  await expect(shadowHeading).toBeFocused();
  await expect(page.getByRole("button", { name: "Controleer" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Ik kan nu niet spreken" })).toBeVisible();
  const record = page.getByRole("button", { name: "Neem op" });
  await expect(record).toHaveAccessibleDescription(/zeg de zin en druk dan op stop/);
  await checkWidths(page, testInfo, "shadow");
  const take = async () => {
    await page.getByRole("button", { name: "Neem op" }).focus();
    await page.keyboard.press("Enter");
    const stop = page.getByRole("button", { name: "Stop met opnemen" });
    await expect(stop).toHaveAttribute("aria-pressed", "true");
    await expect(stop).toBeFocused();
    await page.waitForTimeout(600);
    await page.keyboard.press("Enter");
  };
  await take();
  // not heard: the item stays open for a second take at once
  await expect(page.getByRole("region", { name: /Niet gehoord/ })).toBeVisible();
  await expect(page.getByText("Je mag het meteen nog een keer proberen.")).toBeVisible();
  await expect(page.locator("p", { hasText: "Wat we hoorden" })).toContainText("nog niets");
  await expect(next).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(shadowHeading).toBeFocused();
  await take();
  await expect(page.getByRole("region", { name: /Gehoord/ })).toBeVisible();
  expect(sent.take1).toBe(true);
  expect(sent.take2).toBe(true);
  await expect(page.locator("p", { hasText: "Wat we hoorden" })).toContainText("ik woon in gent");
  await expect(page.locator(".exercise-session")).not.toContainText(/4\s*\/\s*4|%/);
  await checkWidths(page, testInfo, "shadow-feedback");
  await page.keyboard.press("Enter");

  // the missed recall comes back (from the server's view of the session), and is right this time
  await expect(page.getByRole("heading", { name: "Typ het Nederlandse woord." })).toBeFocused();
  await field.focus();
  await page.keyboard.type("de sleutel");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("region", { name: /Juist/ })).toBeVisible();
  expect(sent["recall-again"]).toMatchObject({ answer: { text: "de sleutel" }, hint_used: false });
  await page.keyboard.press("Enter");
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
