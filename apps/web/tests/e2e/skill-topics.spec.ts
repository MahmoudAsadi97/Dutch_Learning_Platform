import { readFile } from "node:fs/promises";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import type { Page, Route, TestInfo } from "@playwright/test";
import { expect, test } from "./fixtures/test";

const copy = (nl: string) => ({ nl, en: `English: ${nl}`, fa: `فارسی: ${nl}` });
const skills = { reading: "Lezen", listening: "Luisteren", speaking: "Spreken", writing: "Schrijven" };
type Skill = keyof typeof skills;
const topics = Array.from({ length: 100 }, (_, index) => ({
  id: `pre-a1-t${String(index + 1).padStart(3, "0")}`,
  title: copy(`Reis ${index + 1}`),
  category: copy(index < 50 ? "Onderweg" : "Vrije tijd"),
}));
const question = (id: string) => ({
  id: `${id}-q1`,
  prompt: copy("Waar wacht Noor?"),
  options: [copy("Thuis"), copy("Aan de halte")],
  answer_index: 1,
  explanation: copy("Noor wacht aan de halte op de bus."),
});
const secondQuestion = (id: string) => ({
  id: `${id}-q2`,
  prompt: copy("Wat doet Noor daarna?"),
  options: [copy("De bus nemen"), copy("Naar huis gaan")],
  answer_index: 0,
  explanation: copy("Noor neemt de bus naar het station."),
});
const productiveTask = {
  prompt: copy("Vertel Sam waar je op de bus wacht en waar je daarna naartoe gaat."),
  criteria: [copy("Zeg waar je wacht."), copy("Zeg waar je naartoe gaat.")],
  sample: copy("Ik wacht aan de halte. Ik ga naar het station."),
  sample_is_excerpt: false,
  min_words: 1,
  max_words: 60,
};

type Review = { stage_id: string; topic_id: string };

/** Browser transition fixtures only; the API suite validates all authored banks and persistence. */
async function mockTopics(page: Page, reviews: Record<string, Review> = {}, stageId = "pre-a1") {
  const stage = await (await page.request.get(`/api/curriculum/${stageId}`)).json();
  // the same hundred topics, with the ids of the stage asked for
  const list = topics.map((item) => ({ ...item, id: item.id.replace(/^pre-a1/, stageId) }));
  const completed = new Set<string>();
  const attempted = new Set<string>();
  const requests: { id: string; body: Record<string, unknown> }[] = [];
  await page.route(new RegExp(`/api/curriculum/${stageId}/topics(?:/|[?]|$)`), async (route) => {
    const url = new URL(route.request().url());
    const parts = url.pathname.split("/topics")[1].split("/").filter(Boolean);
    const skill = (url.searchParams.get("skill") ?? "reading") as Skill;
    if (!parts.length) {
      const q = (url.searchParams.get("q") ?? "").toLowerCase();
      const category = url.searchParams.get("category") ?? "";
      const status = url.searchParams.get("status") ?? "all";
      const offset = Number(url.searchParams.get("offset") ?? 0);
      const limit = Number(url.searchParams.get("limit") ?? 12);
      expect(limit).toBeLessThanOrEqual(24);
      const items = list.filter(
        (item) =>
          (!q || JSON.stringify(item.title).toLowerCase().includes(q)) &&
          (!category || item.category.nl === category) &&
          (status === "completed"
            ? completed.has(`${skill}.${item.id}`)
            : status === "not_started"
              ? !attempted.has(`${skill}.${item.id}`)
              : true),
      );
      await route.fulfill({
        json: {
          stage_id: stageId,
          skill,
          learner_key: stage.learner_key,
          total: items.length,
          total_topics: 100,
          completed_count: list.filter((item) => completed.has(`${skill}.${item.id}`)).length,
          offset,
          limit,
          categories: [copy("Onderweg"), copy("Vrije tijd")],
          items: items.slice(offset, offset + limit).map((item) => ({
            ...item,
            completed: completed.has(`${skill}.${item.id}`),
            attempted: attempted.has(`${skill}.${item.id}`),
            review_of: reviews[item.id] ?? null,
          })),
        },
      });
      return;
    }
    const topic = list.find((item) => item.id === parts[0]);
    if (!topic) {
      await route.fulfill({ status: 404, json: { detail: "Unknown topic" } });
      return;
    }
    if (parts[1] === "practice") {
      const body = route.request().postDataJSON();
      requests.push({ id: topic.id, body });
      const currentSkill = body.skill as Skill;
      const key = `${currentSkill}.${topic.id}`;
      attempted.add(key);
      const qs = [question(topic.id), secondQuestion(topic.id)];
      const receptive = ["reading", "listening"].includes(currentSkill);
      const correct = receptive ? qs.filter((q) => body.answers[q.id] === q.answer_index).length : 0;
      const passed = !receptive || correct === qs.length;
      if (passed) completed.add(key);
      await route.fulfill({
        json: {
          completed: completed.has(key),
          passed,
          feedback: copy(
            passed ? "Je antwoord past bij de reis." : "Luister of lees nog eens waar Noor wacht.",
          ),
          ...(receptive
            ? {
                correct,
                total: qs.length,
                explanations: qs.map((q) => ({
                  id: q.id,
                  correct: body.answers[q.id] === q.answer_index,
                  answer_index: q.answer_index,
                  explanation: q.explanation,
                })),
              }
            : {}),
        },
      });
      return;
    }
    if (parts[1] === "listening") {
      await route.fulfill({ status: 503, json: { detail: "Audio fixture not installed for this test" } });
      return;
    }
    await route.fulfill({
      json: {
        ...topic,
        stage_id: stageId,
        skill,
        review_status: "unreviewed",
        context: {
          reading: copy("Noor wacht aan de halte. Daarna neemt ze de bus naar het station."),
          listening: copy("Hallo Sam, ik wacht aan de halte. Ik neem straks de bus naar het station."),
        },
        objectives: [copy("De juiste halte vinden.")],
        language_focus: copy("Ik wacht aan de halte. Ik neem de bus."),
        vocabulary: [
          { id: "bus", term: "de bus", meaning: copy("een voertuig"), example: copy("Ik neem de bus.") },
        ],
        progress: {
          completed: completed.has(`${skill}.${topic.id}`),
          attempted: attempted.has(`${skill}.${topic.id}`),
        },
        policy: { recording_max_seconds: 60 },
        review_of: reviews[topic.id] ?? null,
        activity:
          skill === "reading" || skill === "listening"
            ? {
                text: copy(
                  skill === "reading"
                    ? "Noor wacht aan de halte. Daarna neemt ze de bus naar het station."
                    : "Hallo Sam, ik wacht aan de halte. Ik neem straks de bus naar het station.",
                ),
                audio_parts: 1,
                questions: [question(topic.id), secondQuestion(topic.id)].map(({ id, prompt, options }) => ({
                  id,
                  prompt,
                  options,
                })),
              }
            : productiveTask,
      },
    });
  });
  return { requests, completed, attempted };
}

type Sets = { completed: Set<string>; attempted: Set<string> };
type SessionBody = { source: string; topic_id: string; skill: Skill; retry?: boolean; kinds: string[] };

/**
 * The exercise API for topic sessions, as browser transitions only: a reading or listening topic is its passage
 * and the two questions (a retry: the questions the last session missed), a warm-up one word item; every answer
 * closes its item, and finishing says what counted the way the server does. The API suites own the rules.
 */
async function mockTopicSessions(page: Page, sets: Sets) {
  const bodies: SessionBody[] = [];
  const missedLast: Record<string, string[]> = {};
  const sessions: Record<string, { body: SessionBody; firsts: Record<string, boolean>; items: string[] }> =
    {};
  const right: Record<string, string> = { q1: "q1b", q2: "q2a", w1: "w1a" };
  const support: Record<string, { id: string; nl: string; en: string; fa: string }[]> = {
    q1: [
      { id: "q1a", ...copy("Thuis") },
      { id: "q1b", ...copy("Aan de halte") },
    ],
    q2: [
      { id: "q2a", ...copy("De bus nemen") },
      { id: "q2b", ...copy("Naar huis gaan") },
    ],
    w1: [
      { id: "w1a", nl: "de bus", en: "the bus", fa: "اتوبوس" },
      { id: "w1b", nl: "de trein", en: "the train", fa: "قطار" },
    ],
  };
  const stems: Record<string, ReturnType<typeof copy>> = {
    q1: copy("Waar wacht Noor?"),
    q2: copy("Wat doet Noor daarna?"),
  };
  const text = (skill: Skill) =>
    copy(
      skill === "reading"
        ? "Noor wacht aan de halte. Daarna neemt ze de bus naar het station."
        : "Hallo Sam, ik wacht aan de halte. Ik neem straks de bus naar het station.",
    );
  const view = (id: string, revealed = false) => {
    const { body, items } = sessions[id];
    const passage =
      body.skill === "reading"
        ? {
            kind: "read_passage",
            text: revealed ? text("reading") : { nl: text("reading").nl },
            vocabulary: [{ term: "de bus", meaning: { en: "the bus", fa: "اتوبوس" } }],
          }
        : {
            kind: "listen_passage",
            parts: 1,
            transcript: revealed ? text("listening") : null,
            vocabulary: [],
          };
    return {
      id,
      source: "topic",
      stage_id: "pre-a1",
      focus: "words",
      library_topic: null,
      topic_id: body.topic_id,
      skill: body.skill,
      retry: Boolean(body.retry),
      status: revealed ? "finished" : "active",
      content_status: "unreviewed",
      resumed: false,
      items: items.map((item, position) => ({
        id: item,
        position,
        kind: item === "p" ? passage.kind : "choice",
        skill: item === "w1" ? "" : body.skill,
        state: revealed ? "closed" : "open",
        attempts_left: revealed ? 0 : item === "p" ? 1 : 2,
        prompt:
          item === "p"
            ? passage
            : item === "w1"
              ? {
                  kind: "choice",
                  direction: "meaning",
                  stem: { nl: "de bus" },
                  options: support.w1.map(({ id, en, fa }) => ({ id, en, fa })),
                }
              : {
                  kind: "choice",
                  direction: "question",
                  stem: stems[item],
                  options: support[item].map(({ id, nl }) => ({ id, nl })),
                },
        feedback: null,
      })),
      next_item_id: revealed ? null : items[0],
      progress: { closed: 0, total: items.filter((item) => item !== "p").length, queued: 0 },
      summary: null,
    };
  };
  await page.route(/\/api\/exercises\/sessions(\/|$)/, async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    const parts = url.pathname.split("/exercises/sessions")[1].split("/").filter(Boolean);
    if (!parts.length) {
      const body = request.postDataJSON() as SessionBody;
      bodies.push(body);
      const key = `${body.skill}.${body.topic_id}`;
      const receptive = body.skill === "reading" || body.skill === "listening";
      const items = !receptive ? ["w1"] : body.retry ? ["p", ...(missedLast[key] ?? [])] : ["p", "q1", "q2"];
      const id = `mock-topic-${bodies.length}`;
      sessions[id] = { body, firsts: {}, items };
      return route.fulfill({ status: 201, json: view(id) });
    }
    const id = parts[0];
    const session = sessions[id];
    if (request.method() === "GET") return route.fulfill({ json: view(id, true) });
    if (parts[1] === "finish") {
      const { body, firsts, items } = session;
      const key = `${body.skill}.${body.topic_id}`;
      const questions = items.filter((item) => item !== "p");
      const missed = questions.filter((item) => !firsts[item]);
      missedLast[key] = missed;
      const receptive = body.skill === "reading" || body.skill === "listening";
      const counted = receptive && !body.retry;
      const passed = counted ? missed.length === 0 : null;
      if (counted) sets.attempted.add(key);
      if (passed) sets.completed.add(key);
      return route.fulfill({
        json: {
          id,
          status: "finished",
          points: 0,
          summary: {
            items_total: questions.length,
            answered: questions.length,
            first_try_correct: questions.length - missed.length,
            fixed_on_retry: 0,
            skipped: 0,
            overridden: 0,
            points_earned: questions.length,
            session_bonus: 0,
            by_kind: {},
            missed: [],
            suggestions: [],
            completion: {
              scope: "topic",
              skill: body.skill,
              topic_id: body.topic_id,
              counted,
              reason: !receptive ? "open_task" : body.retry ? "retry" : null,
              passed,
              correct: counted ? questions.length - missed.length : null,
              total: counted ? questions.length : null,
              required: counted ? questions.length : null,
              completed: sets.completed.has(key),
              to_retry: missed.length,
            },
          },
        },
      });
    }
    const item = parts[2];
    const next = session.items[session.items.indexOf(item) + 1] ?? null;
    const progress = { closed: 1, total: 2, queued: 0 };
    if (item === "p")
      return route.fulfill({
        json: {
          item_id: "p",
          attempt: 1,
          outcome: "done",
          closed: true,
          requeue: false,
          attempts_left: 0,
          feedback: { outcome: "done" },
          points: 0,
          progress,
          next_item_id: next,
        },
      });
    const given = (request.postDataJSON() as { answer: { option: string } }).answer.option;
    const ok = given === right[item];
    session.firsts[item] = ok;
    return route.fulfill({
      json: {
        item_id: item,
        attempt: 1,
        outcome: ok ? "correct" : "incorrect",
        closed: true,
        requeue: false,
        attempts_left: 0,
        feedback: {
          outcome: ok ? "correct" : "incorrect",
          correct: right[item],
          given,
          support: support[item],
          explanation: item === "q1" ? copy("Noor wacht aan de halte op de bus.") : null,
        },
        points: 1,
        progress,
        next_item_id: next,
      },
    });
  });
  return { bodies };
}

/** No page overflow and no WCAG A/AA violation in the topic reader, at 1440, 390 and 320 pixels. */
async function checkTopicWidths(page: Page, testInfo: TestInfo, name: string) {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: width <= 390 ? 844 : 1000 });
    const layout = await page.evaluate(() => ({
      viewport: innerWidth,
      document: document.documentElement.scrollWidth,
      containers: Array.from(
        document.querySelectorAll<HTMLElement>(
          ".app-workspace, .site-main, .learning-workspace, .unit-content, .topic-reader, .topic-start, .topic-steps",
        ),
      ).map((element) => ({
        className: element.className,
        left: element.getBoundingClientRect().left,
        width: element.getBoundingClientRect().width,
        right: element.getBoundingClientRect().right,
        display: getComputedStyle(element).display,
        columns: getComputedStyle(element).gridTemplateColumns,
        minWidth: getComputedStyle(element).minWidth,
      })),
      // Keep failure evidence focused on visible containers instead of an unexplained false assertion.
      outside: Array.from(document.querySelectorAll<HTMLElement>(".topic-reader, .topic-reader *"))
        .filter((element) => {
          const box = element.getBoundingClientRect();
          return box.width > 0 && (box.right > innerWidth + 1 || box.left < -1);
        })
        .slice(0, 12)
        .map((element) => ({
          tag: element.tagName,
          className: element.className,
          text: element.textContent?.slice(0, 90),
          width: element.getBoundingClientRect().width,
          right: element.getBoundingClientRect().right,
          parent: element.parentElement?.className,
          display: getComputedStyle(element).display,
          minWidth: getComputedStyle(element).minWidth,
        })),
      completionBanners: Array.from(document.querySelectorAll<HTMLElement>(".summary-completion")).map(
        (element) => ({
          width: element.getBoundingClientRect().width,
          display: getComputedStyle(element).display,
          children: Array.from(element.children).map((child) => ({
            tag: child.tagName,
            width: child.getBoundingClientRect().width,
            right: child.getBoundingClientRect().right,
          })),
        }),
      ),
    }));
    await testInfo.attach(`${name}-${width}-layout`, {
      body: JSON.stringify(layout, null, 2),
      contentType: "application/json",
    });
    expect(layout.document, JSON.stringify(layout.outside)).toBeLessThanOrEqual(layout.viewport);
    const results = await new AxeBuilder({ page })
      .include(".topic-reader")
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

/** Answers the two questions of a topic session: right (true) or wrong (false), each in turn. */
async function answerQuestions(page: Page, firsts: [boolean, boolean]) {
  const options: [RegExp, RegExp][] = [
    [/Aan de halte/, /Thuis/],
    [/De bus nemen/, /Naar huis gaan/],
  ];
  for (const [index, right] of firsts.entries()) {
    await page.getByRole("radio", { name: options[index][right ? 0 : 1] }).check();
    await page.getByRole("button", { name: "Controleer", exact: true }).click();
    await page.getByRole("button", { name: "Verder", exact: true }).click();
  }
}

async function selectSkill(page: Page, skill: Skill) {
  await page
    .getByRole("navigation", { name: "Onderdelen van dit niveau" })
    .getByRole("button", { name: skills[skill], exact: true })
    .click();
  await expect(page.locator(".skill-topic-library h3")).toHaveText(
    `100 onderwerpen voor ${skills[skill].toLowerCase()}`,
  );
}
async function openTopic(page: Page, number = 1) {
  await page.getByRole("button", { name: `Oefen Reis ${number}`, exact: true }).click();
  await expect(page.locator(".topic-reader h3").first()).toContainText(`Reis ${number}`);
}

test("each skill opens its own 100-topic collection with bounded pages and filters", async ({ page }) => {
  await mockTopics(page);
  await page.goto("/learn/pre-a1");
  for (const skill of Object.keys(skills) as Skill[]) {
    await selectSkill(page, skill);
    await expect(page.locator(".topic-tile")).toHaveCount(12);
    await expect(page.getByRole("button", { name: "Onderwerpen", exact: true })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.locator(".communication-coach")).toHaveCount(0);
    const pager = page.getByRole("navigation", { name: "Pagina’s met oefenonderwerpen" });
    await expect(pager.getByRole("status")).toHaveText("1–12 van 100");
    await pager.getByRole("button", { name: "Volgende", exact: true }).click();
    await expect(pager.getByRole("status")).toHaveText("13–24 van 100");
    await page.getByLabel("Thema", { exact: true }).selectOption("Vrije tijd");
    await expect(pager.getByRole("status")).toHaveText("1–12 van 50");
    await expect(page.locator(".topic-tile h4").first()).toContainText("Reis 51");
    await page.getByLabel("Zoek een situatie").fill("Reis 100");
    await expect(page.locator(".topic-tile")).toHaveCount(1);
    await expect(pager.getByRole("status")).toHaveText("1–1 van 1");
    await page.getByLabel("Oefenstatus").selectOption("completed");
    await expect(page.getByRole("heading", { name: "Geen onderwerpen gevonden" })).toBeVisible();
  }
});

test("a reading topic starts on its card, runs as a session and completes only reading", async ({
  page,
}, testInfo) => {
  const { requests, completed, attempted } = await mockTopics(page);
  const { bodies } = await mockTopicSessions(page, { completed, attempted });
  await page.goto("/learn/pre-a1");
  await selectSkill(page, "reading");
  await openTopic(page);
  // the start card says what happens; nothing is asked of the server yet
  await expect(page.locator(".topic-start")).toContainText("Zo werkt het");
  expect(bodies).toEqual([]);
  await expect(page.locator("[data-honesty]")).toHaveCount(1);
  await checkTopicWidths(page, testInfo, "reading-card");
  await page.getByRole("button", { name: "Begin met lezen", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Lees eerst de tekst" })).toBeFocused();
  expect(bodies).toEqual([
    {
      request_id: expect.any(String),
      focus: "words",
      source: "topic",
      stage_id: "pre-a1",
      topic_id: "pre-a1-t001",
      skill: "reading",
      kinds: expect.arrayContaining(["choice"]),
    },
  ]);
  await expect(page.locator(".exercise-passage-text")).toContainText("Noor wacht aan de halte.");
  await expect(page.locator(".exercise-passage-text [lang=en]")).toHaveCount(0);
  await expect(page.locator("[data-honesty]")).toHaveCount(1);
  await checkTopicWidths(page, testInfo, "reading-passage");
  await page.getByRole("button", { name: "Naar de vragen", exact: true }).click();
  // the question in Dutch with its gloss; the options' glosses wait for the answer; the text stays above
  await expect(page.locator(".exercise-passage[data-mode=reference]")).toContainText(
    "Noor wacht aan de halte.",
  );
  await expect(page.locator(".answer-option .exercise-meaning")).toHaveCount(0);
  await page.getByRole("radio", { name: /Aan de halte/ }).check();
  await page.getByRole("button", { name: "Controleer", exact: true }).click();
  await expect(page.getByRole("region", { name: /Juist/ })).toBeVisible();
  await expect(page.getByText("Noor wacht aan de halte op de bus.", { exact: true })).toBeVisible();
  await checkTopicWidths(page, testInfo, "reading-verdict");
  await page.getByRole("button", { name: "Verder", exact: true }).click();
  // Escape within the session asks before stopping
  await page.getByRole("heading", { name: /Kies het juiste antwoord/ }).press("Escape");
  const dialog = page.getByRole("dialog", { name: "Stoppen met oefenen?" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Blijf oefenen", exact: true }).click();
  await expect(dialog).toBeHidden();
  await page.getByRole("radio", { name: /De bus nemen/ }).check();
  await page.getByRole("button", { name: "Controleer", exact: true }).click();
  await page.getByRole("button", { name: "Verder", exact: true }).click();
  // the summary says what counted; the passage again, now with its translation on request
  await expect(page.locator(".summary-completion[data-state=done]")).toContainText("Gelukt");
  await expect(page.locator(".topic-detail-kicker")).toContainText("Al geoefend");
  await page.getByRole("button", { name: "Vertaling tonen", exact: true }).click();
  await expect(page.locator(".summary-passage [lang=en]").first()).toBeVisible();
  await checkTopicWidths(page, testInfo, "reading-summary");
  // the classic form's endpoint is not used by the page any more
  expect(requests).toEqual([]);
  await page.getByRole("button", { name: "Kies een ander onderwerp", exact: true }).click();
  await expect(page.locator(".topic-progress-number")).toHaveText("1 / 100");
  await expect(page.getByRole("progressbar", { name: "Voortgang lezen" })).toHaveAttribute(
    "aria-valuenow",
    "1",
  );
  await selectSkill(page, "listening");
  await expect(page.locator(".topic-progress-number")).toHaveText("0 / 100");
  await expect(page.getByRole("progressbar", { name: "Voortgang luisteren" })).toHaveAttribute(
    "aria-valuenow",
    "0",
  );
});

test("a missed question can be practised again, which completes nothing; all questions again can", async ({
  page,
}) => {
  const { completed, attempted } = await mockTopics(page);
  const { bodies } = await mockTopicSessions(page, { completed, attempted });
  await page.goto("/learn/pre-a1");
  await selectSkill(page, "reading");
  await openTopic(page, 2);
  await page.getByRole("button", { name: "Begin met lezen", exact: true }).click();
  await page.getByRole("button", { name: "Naar de vragen", exact: true }).click();
  await answerQuestions(page, [false, true]);
  await expect(page.locator(".summary-completion[data-state=open]")).toContainText(
    "eerste antwoord op elke vraag goed is",
  );
  await page.getByRole("button", { name: "Oefen de gemiste vragen", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Lees eerst de tekst" })).toBeFocused();
  expect(bodies[1]).toMatchObject({ topic_id: "pre-a1-t002", skill: "reading", retry: true });
  await page.getByRole("button", { name: "Naar de vragen", exact: true }).click();
  await expect(page.getByText("Waar wacht Noor?", { exact: true })).toBeVisible();
  await page.getByRole("radio", { name: /Aan de halte/ }).check();
  await page.getByRole("button", { name: "Controleer", exact: true }).click();
  await page.getByRole("button", { name: "Verder", exact: true }).click();
  await expect(page.locator(".summary-completion")).toContainText("extra oefening");
  await expect(page.locator(".summary-completion")).toContainText("Doe alle vragen opnieuw om het onderwerp");
  const again = page.locator(".exercise-summary .exercise-actions button").first();
  await expect(again).toHaveText(/Doe alle vragen opnieuw/);
  await again.click();
  expect(bodies[2]).not.toHaveProperty("retry");
  await page.getByRole("button", { name: "Naar de vragen", exact: true }).click();
  await answerQuestions(page, [true, true]);
  await expect(page.locator(".summary-completion[data-state=done]")).toContainText("Gelukt");
  await page.getByRole("button", { name: "Kies een ander onderwerp", exact: true }).click();
  await expect(page.locator(".topic-progress-number")).toHaveText("1 / 100");
});

test("writing drafts and corrections stay with their own topic and survive a failed submission", async ({
  page,
}) => {
  const { requests } = await mockTopics(page);
  const original = "Ik bent aan de halte.";
  await page.route("**/api/curriculum/pre-a1/writing-feedback", (route) =>
    route.fulfill({
      json: {
        original_text: original,
        corrected_text: "Ik ben aan de halte.",
        review_status: "automated",
        corrections: [
          {
            original: "Ik bent",
            replacement: "Ik ben",
            category: "grammar",
            explanation: copy("Bij ik gebruik je ben."),
          },
        ],
        summary: copy("Controleer de persoonsvorm."),
      },
    }),
  );
  let fail = true;
  await page.route("**/api/curriculum/pre-a1/topics/pre-a1-t001/practice", async (route) => {
    if (fail) {
      fail = false;
      await route.fulfill({ status: 503, json: { detail: "temporary" } });
    } else await route.fallback();
  });
  await page.goto("/learn/pre-a1");
  await selectSkill(page, "writing");
  await openTopic(page);
  await page.getByRole("button", { name: "Ga meteen naar de opdracht", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Jouw opdracht" })).toBeFocused();
  const draft = page.getByLabel("Jouw tekst bij dit onderwerp", { exact: true });
  await expect(page.locator(".topic-scene")).toHaveAttribute("open", "");
  await expect(page.locator(".topic-scene")).toContainText("Noor wacht aan de halte.");
  await expect(page.locator(".topic-scene")).toContainText("Hallo Sam, ik wacht aan de halte.");
  await draft.fill(original);
  await page.getByRole("button", { name: "Controleer spelling en grammatica", exact: true }).click();
  await expect(page.locator(".correction-list del")).toHaveText("Ik bent");
  await expect(draft).toHaveValue(original);
  await page.locator(".corrected-draft summary").click();
  await page.getByRole("button", { name: "Gebruik als nieuwe versie", exact: true }).click();
  await expect(draft).toHaveValue("Ik ben aan de halte.");
  await page.getByRole("button", { name: "Rond schrijven af", exact: true }).click();
  await expect(page.locator(".topic-reader .error")).toContainText("Je invoer blijft staan.");
  await expect(draft).toHaveValue("Ik ben aan de halte.");
  await page.getByRole("button", { name: "← Alle onderwerpen", exact: true }).click();
  await openTopic(page, 2);
  await page.getByRole("button", { name: "Ga meteen naar de opdracht", exact: true }).click();
  await expect(draft).toHaveValue("");
  await draft.fill("Ik ga met Sam naar Brugge.");
  await page.getByRole("button", { name: "← Alle onderwerpen", exact: true }).click();
  await openTopic(page);
  await expect(draft).toHaveValue("Ik ben aan de halte.");
  await page.getByRole("button", { name: "Rond schrijven af", exact: true }).click();
  await expect(page.locator(".practice-feedback")).toBeVisible();
  expect(requests[0]).toEqual({
    id: "pre-a1-t001",
    body: { request_id: expect.any(String), skill: "writing", text: "Ik ben aan de halte." },
  });
  await page.reload();
  await selectSkill(page, "writing");
  await openTopic(page, 2);
  await expect(draft).toHaveValue("Ik ga met Sam naar Brugge.");
});

test("a writing warm-up runs on its words and hands over to the task", async ({ page }, testInfo) => {
  const { requests, completed, attempted } = await mockTopics(page);
  const { bodies } = await mockTopicSessions(page, { completed, attempted });
  await page.goto("/learn/pre-a1");
  await selectSkill(page, "writing");
  await openTopic(page, 4);
  await checkTopicWidths(page, testInfo, "writing-card");
  await page.getByRole("button", { name: "Oefen eerst de woorden", exact: true }).click();
  await expect(page.getByRole("button", { name: "Ga meteen naar de opdracht", exact: true })).toBeVisible();
  await page.getByRole("radio", { name: /the bus/ }).check();
  await page.getByRole("button", { name: "Controleer", exact: true }).click();
  await page.getByRole("button", { name: "Verder", exact: true }).click();
  expect(bodies).toEqual([
    expect.objectContaining({ source: "topic", topic_id: "pre-a1-t004", skill: "writing" }),
  ]);
  expect(bodies[0]).not.toHaveProperty("retry");
  await expect(page.locator(".summary-completion")).toContainText("opwarming");
  await checkTopicWidths(page, testInfo, "writing-summary");
  const toTask = page.locator(".exercise-summary .exercise-actions button").first();
  await expect(toTask).toHaveText(/Naar de opdracht/);
  await toTask.click();
  await expect(page.getByRole("heading", { name: "Jouw opdracht" })).toBeFocused();
  await expect(page.getByLabel("Jouw tekst bij dit onderwerp", { exact: true })).toBeVisible();
  // the warm-up completes nothing, and nothing was submitted as the task
  expect(requests).toEqual([]);
  await page.getByRole("button", { name: "← Alle onderwerpen", exact: true }).click();
  await expect(page.locator(".topic-progress-number")).toHaveText("0 / 100");
});

test("a delayed topic search cannot replace a newer filter or reuse its pager", async ({ page }) => {
  await mockTopics(page);
  let release = () => {};
  let started = () => {};
  let finished = () => {};
  const ready = new Promise<void>((resolve) => {
    release = resolve;
  });
  const pending = new Promise<void>((resolve) => {
    started = resolve;
  });
  const done = new Promise<void>((resolve) => {
    finished = resolve;
  });
  await page.route(/\/api\/curriculum\/pre-a1\/topics\?/, async (route) => {
    if (new URL(route.request().url()).searchParams.get("q") !== "Reis 99") {
      await route.fallback();
      return;
    }
    started();
    await ready;
    try {
      await route.fallback();
    } finally {
      finished();
    }
  });
  try {
    await page.goto("/learn/pre-a1");
    await selectSkill(page, "reading");
    const bank = page.locator(".skill-topic-library");
    await bank.getByLabel("Zoek een situatie").fill("Reis 99");
    expect(
      await bank.evaluate((element) => ({
        cards: element.querySelectorAll(".topic-tile").length,
        pagers: element.querySelectorAll(".library-pagination").length,
      })),
    ).toEqual({ cards: 0, pagers: 0 });
    await pending;
    await bank.getByLabel("Zoek een situatie").fill("Reis 100");
    await expect(bank.locator(".topic-tile")).toHaveCount(1);
    await expect(bank.locator(".topic-tile h4")).toContainText("Reis 100");
    release();
    await done;
    await expect(bank.getByLabel("Zoek een situatie")).toHaveValue("Reis 100");
    await expect(bank.locator(".topic-tile h4")).toContainText("Reis 100");
  } finally {
    release();
  }
});

test("speaking protects pending recordings and sends the asset to the selected topic only", async ({
  page,
}) => {
  const { requests } = await mockTopics(page);
  let release = () => {};
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/speech/transcribe", async (route) => {
    await pending;
    await route.fulfill({
      json: {
        audio: { asset_id: "cc91846f-27fc-4bc8-86cc-e879055c75ea" },
        transcript: { text: "Ik wacht aan de halte. Ik ga naar het station." },
      },
    });
  });
  try {
    await page.goto("/learn/pre-a1");
    await selectSkill(page, "speaking");
    await openTopic(page, 3);
    await page.getByRole("button", { name: "Ga meteen naar de opdracht", exact: true }).click();
    await expect(page.locator(".communication-coach")).toHaveCount(0);
    await page.getByRole("button", { name: "Start de opname", exact: true }).click();
    await expect(page.getByRole("button", { name: "← Alle onderwerpen", exact: true })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Startles", exact: true })).toBeDisabled();
    await page.getByRole("button", { name: "Stop de opname", exact: true }).click();
    await expect(page.getByRole("button", { name: "Je opname verwerken…", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "← Alle onderwerpen", exact: true })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Rond spreken af", exact: true })).toBeDisabled();
    release();
    await expect(page.getByRole("button", { name: "Rond spreken af", exact: true })).toBeEnabled();
    await page.getByRole("button", { name: "Rond spreken af", exact: true }).click();
    await expect(page.locator(".practice-feedback")).toBeVisible();
    expect(requests).toEqual([
      {
        id: "pre-a1-t003",
        body: {
          request_id: expect.any(String),
          skill: "speaking",
          audio_asset_id: "cc91846f-27fc-4bc8-86cc-e879055c75ea",
        },
      },
    ]);
  } finally {
    release();
  }
});

test("a late listening response cannot play after leaving its topic", async ({ page }) => {
  const { completed, attempted } = await mockTopics(page);
  await mockTopicSessions(page, { completed, attempted });
  const wav = await readFile(path.resolve(__dirname, "../../../api/tests/fixtures/tone_1s.wav"));
  let release = () => {};
  let started = () => {};
  let finished = () => {};
  const ready = new Promise<void>((resolve) => {
    release = resolve;
  });
  const pending = new Promise<void>((resolve) => {
    started = resolve;
  });
  const done = new Promise<void>((resolve) => {
    finished = resolve;
  });
  await page.addInitScript(() => {
    Object.defineProperty(window, "topicAudioPlays", { value: [], writable: true });
    HTMLMediaElement.prototype.play = async function () {
      (window as unknown as { topicAudioPlays: string[] }).topicAudioPlays.push(this.src);
    };
  });
  await page.route("**/api/curriculum/pre-a1/topics/pre-a1-t001/listening?part=0", async (route) => {
    started();
    await ready;
    try {
      await route.fulfill({ body: wav, contentType: "audio/wav" });
    } finally {
      finished();
    }
  });
  try {
    await page.goto("/learn/pre-a1");
    await selectSkill(page, "listening");
    await openTopic(page);
    await page.getByRole("button", { name: "Begin met luisteren", exact: true }).click();
    await page.getByRole("button", { name: "Luister naar het fragment", exact: true }).click();
    await pending;
    await page.getByRole("button", { name: "← Alle onderwerpen", exact: true }).click();
    await openTopic(page, 2);
    await page.getByRole("button", { name: "Begin met luisteren", exact: true }).click();
    release();
    await done;
    await expect(page.locator(".topic-reader h3").first()).toContainText("Reis 2");
    expect(
      await page.evaluate(() => (window as unknown as { topicAudioPlays: string[] }).topicAudioPlays),
    ).toEqual([]);
    await expect(page.getByRole("button", { name: "Luister naar het fragment", exact: true })).toBeEnabled();
  } finally {
    release();
  }
});

test("topic cards and translated reading fit a 320-pixel phone and keyboard focus follows navigation", async ({
  page,
}, testInfo) => {
  const { completed, attempted } = await mockTopics(page);
  await mockTopicSessions(page, { completed, attempted });
  await page.setViewportSize({ width: 320, height: 850 });
  await page.goto("/learn/pre-a1");
  await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
  await selectSkill(page, "reading");
  const bank = page.locator(".skill-topic-library");
  await expect(bank.locator('[lang="fa"]').first()).toHaveAttribute("dir", "rtl");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const cardsAudit = await new AxeBuilder({ page })
    .include(".skill-topic-library")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(cardsAudit.violations).toEqual([]);
  await testInfo.attach("topic-cards-320-rtl", {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png",
  });
  await openTopic(page);
  await expect(page.locator(".topic-detail-heading h3")).toBeFocused();
  const cardAudit = await new AxeBuilder({ page })
    .include(".topic-reader")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(cardAudit.violations).toEqual([]);
  await page.getByRole("button", { name: "Begin met lezen", exact: true }).click();
  // the translation waits until every question is answered
  await expect(page.locator(".exercise-passage-text [lang=en]")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Vertaling tonen", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Naar de vragen", exact: true }).click();
  await answerQuestions(page, [true, true]);
  await page.getByRole("button", { name: "Vertaling tonen", exact: true }).click();
  await expect(page.locator(".summary-passage [lang=fa]").first()).toHaveAttribute("dir", "rtl");
  await expect(page.locator(".summary-passage [lang=en]").first()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const detailAudit = await new AxeBuilder({ page })
    .include(".topic-reader")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(detailAudit.violations).toEqual([]);
  await testInfo.attach("topic-reading-320-rtl", {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png",
  });
  await page.getByRole("button", { name: "← Alle onderwerpen", exact: true }).click();
  await expect(bank.locator("h3")).toBeFocused();
});

test("an authored A2 topic persists reading evidence through the real API and plays its distinct listening source", async ({
  page,
}) => {
  const source = JSON.parse(
    await readFile(path.resolve(__dirname, "../../../../content/practice/a2.json"), "utf8"),
  ) as {
    topics: {
      id: string;
      title: { nl: string };
      reading: {
        questions: { id: string; prompt: { nl: string }; options: { nl: string }[]; answer_index: number }[];
      };
    }[];
  };
  const topic = source.topics.at(-1)!;
  const beforeReading = await (await page.request.get("/api/curriculum/a2/topics?skill=reading")).json();
  const beforeListening = await (await page.request.get("/api/curriculum/a2/topics?skill=listening")).json();
  const beforeDetail = await (
    await page.request.get(`/api/curriculum/a2/topics/${topic.id}?skill=reading`)
  ).json();
  const expectedCount = beforeReading.completed_count + (beforeDetail.progress.completed ? 0 : 1);
  await page.goto("/learn/a2");
  const nav = page.getByRole("navigation", { name: "Onderdelen van dit niveau" });
  await nav.getByRole("button", { name: "Lezen", exact: true }).click();
  await expect(page.locator(".skill-topic-library h3")).toHaveText("100 onderwerpen voor lezen");
  await page.getByLabel("Zoek een situatie").fill(topic.title.nl);
  await page.getByRole("button", { name: `Oefen ${topic.title.nl}`, exact: true }).click();
  await page.getByRole("button", { name: "Begin met lezen", exact: true }).click();
  // a session through the real API: the passage, then each question answered right the first time (a session
  // left open by an earlier run resumes where it was; one that did not count is done again once)
  const toQuestions = page.getByRole("button", { name: "Naar de vragen", exact: true });
  const stem = page.locator(".exercise-stage .exercise-prompt > [lang=nl]").first();
  const summary = page.locator(".exercise-summary");
  let again = true;
  for (let round = 0; round < 12; round += 1) {
    await expect(toQuestions.or(stem).or(summary).first()).toBeVisible();
    if (await summary.isVisible()) {
      if ((await page.locator(".summary-completion[data-state=done]").count()) || !again) break;
      again = false;
      await page.getByRole("button", { name: "Doe alle vragen opnieuw", exact: true }).click();
      continue;
    }
    if (await toQuestions.isVisible()) {
      await toQuestions.click();
      await expect(stem.or(summary).first()).toBeVisible();
      continue;
    }
    const prompt = ((await stem.textContent()) ?? "").trim();
    const question = topic.reading.questions.find((entry) => entry.prompt.nl.trim() === prompt);
    expect(question, prompt).toBeTruthy();
    await page.getByRole("radio", { name: question!.options[question!.answer_index].nl }).check();
    await page.getByRole("button", { name: "Controleer", exact: true }).click();
    await page.getByRole("button", { name: "Verder", exact: true }).click();
  }
  await expect(page.locator(".summary-completion[data-state=done]")).toBeVisible();
  await page.reload();
  await nav.getByRole("button", { name: "Lezen", exact: true }).click();
  await expect(page.locator(".topic-progress-number")).toHaveText(`${expectedCount} / 100`);
  const persisted = await (
    await page.request.get(`/api/curriculum/a2/topics/${topic.id}?skill=reading`)
  ).json();
  expect(persisted.progress).toEqual({ completed: true, attempted: true });
  await nav.getByRole("button", { name: "Luisteren", exact: true }).click();
  await expect(page.locator(".topic-progress-number")).toHaveText(`${beforeListening.completed_count} / 100`);
  await page.getByLabel("Zoek een situatie").fill(topic.title.nl);
  await page.getByRole("button", { name: `Oefen ${topic.title.nl}`, exact: true }).click();
  await page.getByRole("button", { name: "Begin met luisteren", exact: true }).click();
  const audio = page.waitForResponse((response) =>
    response.url().includes(`/topics/${topic.id}/listening?part=0`),
  );
  await page.getByRole("button", { name: "Luister naar het fragment", exact: true }).click();
  const response = await audio;
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("audio/");
  await expect(page.locator('.topic-reader audio[aria-label="Luisterfragment"]')).toBeVisible();
  await expect(page.getByText("Testtoon; dit is geen luistervoorbeeld.", { exact: true })).toBeVisible();
  const afterListening = await (await page.request.get("/api/curriculum/a2/topics?skill=listening")).json();
  expect(afterListening.completed_count).toBe(beforeListening.completed_count);
});

test("a reused topic says which stage it repeats", async ({ page }) => {
  // as the API does: a topic of a later stage repeats an earlier stage's text, never its own stage's
  await mockTopics(page, { "a1-t002": { stage_id: "pre-a1", topic_id: "pre-a1-t002" } }, "a1");
  const sessions: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/exercises/sessions")) sessions.push(request.url());
  });
  await page.goto("/learn/a1");
  await selectSkill(page, "reading");
  const tiles = page.locator(".topic-tile");
  await expect(tiles.nth(1).locator(".topic-review")).toHaveText(/Herhaling van pre-A1/);
  await expect(tiles.nth(0).locator(".topic-review")).toHaveCount(0);
  await openTopic(page, 2);
  await expect(page.locator(".topic-detail-kicker .topic-review")).toHaveText(/Herhaling van pre-A1/);
  await expect(page.locator(".topic-start")).toContainText("Dit kwam al voor bij pre-A1.");
  expect(sessions).toEqual([]);
});

test.describe("reading feedback with normal motion", () => {
  // The rest of the suite intentionally reduces motion. This regression exercises the real shake effect
  // at a phone width so a moving verdict cannot widen the document between otherwise stable screenshots.
  test.use({ contextOptions: { reducedMotion: "no-preference" } });

  test("a 390px reading verdict fits at every shake keyframe", async ({ page }, testInfo) => {
    const { completed, attempted } = await mockTopics(page);
    await mockTopicSessions(page, { completed, attempted });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/learn/pre-a1");
    expect(await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches)).toBe(false);
    await selectSkill(page, "reading");
    await openTopic(page);
    await page.getByRole("button", { name: "Begin met lezen", exact: true }).click();
    await page.getByRole("button", { name: "Naar de vragen", exact: true }).click();
    await page.getByRole("radio", { name: /Thuis/ }).check();
    await page.getByRole("button", { name: "Controleer", exact: true }).click();
    await expect(page.locator(".feedback-bar[data-outcome=incorrect]")).toBeVisible();

    const frames = await page.locator(".answer-option[data-state=incorrect]").evaluate(async (element) => {
      const animation = element
        .getAnimations()
        .find((candidate) => candidate instanceof CSSAnimation && candidate.animationName === "ts-shake");
      if (!animation?.effect) throw new Error("The normal-motion reading verdict must have its shake effect");
      const duration = animation.effect.getComputedTiming().duration;
      if (typeof duration !== "number" || duration <= 0) throw new Error("The shake must have a duration");
      animation.pause();
      const measured = [];
      // Seeking the real CSS animation makes these measurements deterministic, even on a busy CI runner.
      for (const progress of [0, 0.25, 0.5, 0.75, 1]) {
        animation.currentTime = duration * progress;
        await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
        const box = element.getBoundingClientRect();
        measured.push({
          progress,
          duration,
          viewport: innerWidth,
          document: document.documentElement.scrollWidth,
          left: box.left,
          right: box.right,
        });
      }
      animation.finish();
      return measured;
    });
    await testInfo.attach("reading-verdict-normal-motion-390", {
      body: JSON.stringify(frames, null, 2),
      contentType: "application/json",
    });
    for (const frame of frames) {
      expect(frame.document, `shake progress ${frame.progress}`).toBeLessThanOrEqual(frame.viewport);
      expect(frame.left, `shake progress ${frame.progress}`).toBeGreaterThanOrEqual(0);
      expect(frame.right, `shake progress ${frame.progress}`).toBeLessThanOrEqual(frame.viewport);
    }
    await page.getByRole("button", { name: "Verder", exact: true }).click();
    await expect(page.getByText("Wat doet Noor daarna?", { exact: true })).toBeVisible();
  });
});
