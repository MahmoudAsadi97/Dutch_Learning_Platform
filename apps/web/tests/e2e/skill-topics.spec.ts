import { readFile } from "node:fs/promises";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const copy = (nl: string) => ({nl, en: `English: ${nl}`, fa: `فارسی: ${nl}`});
const skills = {reading: "Lezen", listening: "Luisteren", speaking: "Spreken", writing: "Schrijven"};
type Skill = keyof typeof skills;
const topics = Array.from({length: 100}, (_, index) => ({id: `pre-a1-t${String(index + 1).padStart(3, "0")}`, title: copy(`Reis ${index + 1}`), category: copy(index < 50 ? "Onderweg" : "Vrije tijd")}));
const question = (id: string) => ({id: `${id}-q1`, prompt: copy("Waar wacht Noor?"), options: [copy("Thuis"), copy("Aan de halte")], answer_index: 1, explanation: copy("Noor wacht aan de halte op de bus.")});
const secondQuestion = (id: string) => ({id: `${id}-q2`, prompt: copy("Wat doet Noor daarna?"), options: [copy("De bus nemen"), copy("Naar huis gaan")], answer_index: 0, explanation: copy("Noor neemt de bus naar het station.")});
const productiveTask = {prompt: copy("Vertel Sam waar je op de bus wacht en waar je daarna naartoe gaat."), criteria: [copy("Zeg waar je wacht."), copy("Zeg waar je naartoe gaat.")], sample: copy("Ik wacht aan de halte. Ik ga naar het station."), sample_is_excerpt: false, min_words: 1, max_words: 60};

/** Browser transition fixtures only; the API suite validates all authored banks and persistence. */
async function mockTopics(page: Page) {
  const stage = await (await page.request.get("/api/curriculum/pre-a1")).json();
  const completed = new Set<string>();
  const attempted = new Set<string>();
  const requests: {id: string; body: Record<string, unknown>}[] = [];
  await page.route(/\/api\/curriculum\/pre-a1\/topics(?:\/|\?|$)/, async route => {
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
      const items = topics.filter(item => (!q || JSON.stringify(item.title).toLowerCase().includes(q)) && (!category || item.category.nl === category) && (status === "completed" ? completed.has(`${skill}.${item.id}`) : status === "not_started" ? !attempted.has(`${skill}.${item.id}`) : true));
      await route.fulfill({json: {stage_id: "pre-a1", skill, learner_key: stage.learner_key, total: items.length, total_topics: 100, completed_count: topics.filter(item => completed.has(`${skill}.${item.id}`)).length, offset, limit, categories: [copy("Onderweg"), copy("Vrije tijd")], items: items.slice(offset, offset + limit).map(item => ({...item, completed: completed.has(`${skill}.${item.id}`), attempted: attempted.has(`${skill}.${item.id}`)}))}});
      return;
    }
    const topic = topics.find(item => item.id === parts[0]);
    if (!topic) {await route.fulfill({status: 404, json: {detail: "Unknown topic"}}); return;}
    if (parts[1] === "practice") {
      const body = route.request().postDataJSON();
      requests.push({id: topic.id, body});
      const currentSkill = body.skill as Skill;
      const key = `${currentSkill}.${topic.id}`;
      attempted.add(key);
      const qs = [question(topic.id), secondQuestion(topic.id)];
      const receptive = ["reading", "listening"].includes(currentSkill);
      const correct = receptive ? qs.filter(q => body.answers[q.id] === q.answer_index).length : 0;
      const passed = !receptive || correct === qs.length;
      if (passed) completed.add(key);
      await route.fulfill({json: {completed: completed.has(key), passed, feedback: copy(passed ? "Je antwoord past bij de reis." : "Luister of lees nog eens waar Noor wacht."), ...(receptive ? {correct, total: qs.length, explanations: qs.map(q => ({id: q.id, correct: body.answers[q.id] === q.answer_index, answer_index: q.answer_index, explanation: q.explanation}))} : {})}});
      return;
    }
    if (parts[1] === "listening") {await route.fulfill({status: 503, json: {detail: "Audio fixture not installed for this test"}}); return;}
    await route.fulfill({json: {...topic, stage_id: "pre-a1", skill, review_status: "unreviewed", context: {reading: copy("Noor wacht aan de halte. Daarna neemt ze de bus naar het station."), listening: copy("Hallo Sam, ik wacht aan de halte. Ik neem straks de bus naar het station.")}, objectives: [copy("De juiste halte vinden.")], language_focus: copy("Ik wacht aan de halte. Ik neem de bus."), vocabulary: [{id: "bus", term: "de bus", meaning: copy("een voertuig"), example: copy("Ik neem de bus.")}], progress: {completed: completed.has(`${skill}.${topic.id}`), attempted: attempted.has(`${skill}.${topic.id}`)}, policy: {recording_max_seconds: 60}, activity: skill === "reading" || skill === "listening" ? {text: copy(skill === "reading" ? "Noor wacht aan de halte. Daarna neemt ze de bus naar het station." : "Hallo Sam, ik wacht aan de halte. Ik neem straks de bus naar het station."), audio_parts: 1, questions: [question(topic.id), secondQuestion(topic.id)].map(({id, prompt, options}) => ({id, prompt, options}))} : productiveTask}});
  });
  return {requests};
}

async function selectSkill(page: Page, skill: Skill) {
  await page.getByRole("navigation", {name: "Onderdelen van dit niveau"}).getByRole("button", {name: skills[skill], exact: true}).click();
  await expect(page.locator(".skill-topic-library h3")).toHaveText(`100 onderwerpen voor ${skills[skill].toLowerCase()}`);
}
async function openTopic(page: Page, number = 1) {
  await page.getByRole("button", {name: `Oefen Reis ${number}`, exact: true}).click();
  await expect(page.locator(".topic-reader h3").first()).toContainText(`Reis ${number}`);
}

test("each skill opens its own 100-topic collection with bounded pages and filters", async ({page}) => {
  await mockTopics(page);
  await page.goto("/learn/pre-a1");
  for (const skill of Object.keys(skills) as Skill[]) {
    await selectSkill(page, skill);
    await expect(page.locator(".topic-tile")).toHaveCount(12);
    await expect(page.getByRole("button", {name: "Onderwerpen", exact: true})).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator(".communication-coach")).toHaveCount(0);
    const pager = page.getByRole("navigation", {name: "Pagina’s met oefenonderwerpen"});
    await expect(pager.getByRole("status")).toHaveText("1–12 van 100");
    await pager.getByRole("button", {name: "Volgende", exact: true}).click();
    await expect(pager.getByRole("status")).toHaveText("13–24 van 100");
    await page.getByLabel("Thema", {exact: true}).selectOption("Vrije tijd");
    await expect(pager.getByRole("status")).toHaveText("1–12 van 50");
    await expect(page.locator(".topic-tile h4").first()).toContainText("Reis 51");
    await page.getByLabel("Zoek een situatie").fill("Reis 100");
    await expect(page.locator(".topic-tile")).toHaveCount(1);
    await expect(pager.getByRole("status")).toHaveText("1–1 van 1");
    await page.getByLabel("Oefenstatus").selectOption("completed");
    await expect(page.getByRole("heading", {name: "Geen onderwerpen gevonden"})).toBeVisible();
  }
});

test("reading feedback is earned by submitting this topic and never completes listening", async ({page}) => {
  const {requests} = await mockTopics(page);
  await page.goto("/learn/pre-a1"); await selectSkill(page, "reading"); await openTopic(page);
  await expect(page.locator(".practice-correct,.practice-hint")).toHaveCount(0);
  await page.locator('input[name="q-pre-a1-t001-q1"]').nth(1).check();
  await page.locator('input[name="q-pre-a1-t001-q2"]').first().check();
  await page.getByRole("button", {name: "Rond lezen af", exact: true}).click();
  await expect(page.locator(".practice-feedback")).toContainText("2 van 2 juist");
  await expect(page.locator(".practice-correct")).toHaveCount(2);
  expect(requests).toEqual([{id: "pre-a1-t001", body: {skill: "reading", answers: {"pre-a1-t001-q1": 1, "pre-a1-t001-q2": 0}}}]);
  // A later mistake remains useful evidence without erasing completed practice.
  await page.locator('input[name="q-pre-a1-t001-q1"]').first().check();
  await page.getByRole("button", {name: "Rond lezen af", exact: true}).click();
  await expect(page.locator(".practice-feedback")).toContainText("Je hebt geoefend. Bekijk je volgende stap.");
  await page.getByRole("button", {name: "Kies een ander onderwerp", exact: true}).click();
  await expect(page.locator(".topic-progress-number")).toHaveText("1 / 100");
  await selectSkill(page, "listening");
  await expect(page.locator(".topic-progress-number")).toHaveText("0 / 100");
});

test("writing drafts and corrections stay with their own topic and survive a failed submission", async ({page}) => {
  const {requests} = await mockTopics(page);
  const original = "Ik bent aan de halte.";
  await page.route("**/api/curriculum/pre-a1/writing-feedback", route => route.fulfill({json: {original_text: original, corrected_text: "Ik ben aan de halte.", review_status: "automated", corrections: [{original: "Ik bent", replacement: "Ik ben", category: "grammar", explanation: copy("Bij ik gebruik je ben.")}], summary: copy("Controleer de persoonsvorm.")}}));
  let fail = true;
  await page.route("**/api/curriculum/pre-a1/topics/pre-a1-t001/practice", async route => {
    if (fail) {fail = false; await route.fulfill({status: 503, json: {detail: "temporary"}});} else await route.fallback();
  });
  await page.goto("/learn/pre-a1"); await selectSkill(page, "writing"); await openTopic(page);
  const draft = page.getByLabel("Jouw tekst bij dit onderwerp", {exact: true});
  await expect(page.locator(".topic-scene")).toHaveAttribute("open", "");
  await expect(page.locator(".topic-scene")).toContainText("Noor wacht aan de halte.");
  await expect(page.locator(".topic-scene")).toContainText("Hallo Sam, ik wacht aan de halte.");
  await draft.fill(original);
  await page.getByRole("button", {name: "Controleer spelling en grammatica", exact: true}).click();
  await expect(page.locator(".correction-list del")).toHaveText("Ik bent");
  await expect(draft).toHaveValue(original);
  await page.locator(".corrected-draft summary").click();
  await page.getByRole("button", {name: "Gebruik als nieuwe versie", exact: true}).click();
  await expect(draft).toHaveValue("Ik ben aan de halte.");
  await page.getByRole("button", {name: "Rond schrijven af", exact: true}).click();
  await expect(page.locator(".topic-reader .error")).toContainText("Je invoer blijft staan.");
  await expect(draft).toHaveValue("Ik ben aan de halte.");
  await page.getByRole("button", {name: "← Alle onderwerpen", exact: true}).click();
  await openTopic(page, 2); await expect(draft).toHaveValue("");
  await draft.fill("Ik ga met Sam naar Brugge.");
  await page.getByRole("button", {name: "← Alle onderwerpen", exact: true}).click();
  await openTopic(page); await expect(draft).toHaveValue("Ik ben aan de halte.");
  await page.getByRole("button", {name: "Rond schrijven af", exact: true}).click();
  await expect(page.locator(".practice-feedback")).toBeVisible();
  expect(requests[0]).toEqual({id: "pre-a1-t001", body: {skill: "writing", text: "Ik ben aan de halte."}});
  await page.reload(); await selectSkill(page, "writing"); await openTopic(page, 2);
  await expect(draft).toHaveValue("Ik ga met Sam naar Brugge.");
});

test("a delayed topic search cannot replace a newer filter or reuse its pager", async ({page}) => {
  await mockTopics(page);
  let release = () => {}; let started = () => {}; let finished = () => {};
  const ready = new Promise<void>(resolve => {release = resolve;});
  const pending = new Promise<void>(resolve => {started = resolve;});
  const done = new Promise<void>(resolve => {finished = resolve;});
  await page.route(/\/api\/curriculum\/pre-a1\/topics\?/, async route => {
    if (new URL(route.request().url()).searchParams.get("q") !== "Reis 99") {await route.fallback(); return;}
    started(); await ready;
    try {await route.fallback();} finally {finished();}
  });
  try {
    await page.goto("/learn/pre-a1"); await selectSkill(page, "reading");
    const bank = page.locator(".skill-topic-library");
    await bank.getByLabel("Zoek een situatie").fill("Reis 99");
    expect(await bank.evaluate(element => ({cards: element.querySelectorAll(".topic-tile").length, pagers: element.querySelectorAll(".library-pagination").length}))).toEqual({cards: 0, pagers: 0});
    await pending;
    await bank.getByLabel("Zoek een situatie").fill("Reis 100");
    await expect(bank.locator(".topic-tile")).toHaveCount(1);
    await expect(bank.locator(".topic-tile h4")).toContainText("Reis 100");
    release(); await done;
    await expect(bank.getByLabel("Zoek een situatie")).toHaveValue("Reis 100");
    await expect(bank.locator(".topic-tile h4")).toContainText("Reis 100");
  } finally {release();}
});

test("speaking protects pending recordings and sends the asset to the selected topic only", async ({page}) => {
  const {requests} = await mockTopics(page);
  let release = () => {};
  const pending = new Promise<void>(resolve => {release = resolve;});
  await page.route("**/api/speech/transcribe", async route => {await pending; await route.fulfill({json: {audio: {asset_id: "cc91846f-27fc-4bc8-86cc-e879055c75ea"}, transcript: {text: "Ik wacht aan de halte. Ik ga naar het station."}}});});
  try {
    await page.goto("/learn/pre-a1"); await selectSkill(page, "speaking"); await openTopic(page, 3);
    await expect(page.locator(".communication-coach")).toHaveCount(0);
    await page.getByRole("button", {name: "Start de opname", exact: true}).click();
    await expect(page.getByRole("button", {name: "← Alle onderwerpen", exact: true})).toBeDisabled();
    await expect(page.getByRole("button", {name: "Startles", exact: true})).toBeDisabled();
    await page.getByRole("button", {name: "Stop de opname", exact: true}).click();
    await expect(page.getByRole("button", {name: "Je opname verwerken…", exact: true})).toBeVisible();
    await expect(page.getByRole("button", {name: "← Alle onderwerpen", exact: true})).toBeDisabled();
    await expect(page.getByRole("button", {name: "Rond spreken af", exact: true})).toBeDisabled();
    release();
    await expect(page.getByRole("button", {name: "Rond spreken af", exact: true})).toBeEnabled();
    await page.getByRole("button", {name: "Rond spreken af", exact: true}).click();
    await expect(page.locator(".practice-feedback")).toBeVisible();
    expect(requests).toEqual([{id: "pre-a1-t003", body: {skill: "speaking", audio_asset_id: "cc91846f-27fc-4bc8-86cc-e879055c75ea"}}]);
  } finally {release();}
});

test("a late listening response cannot play after leaving its topic", async ({page}) => {
  await mockTopics(page);
  const wav = await readFile(path.resolve(__dirname, "../../../api/tests/fixtures/tone_1s.wav"));
  let release = () => {}; let started = () => {}; let finished = () => {};
  const ready = new Promise<void>(resolve => {release = resolve;});
  const pending = new Promise<void>(resolve => {started = resolve;});
  const done = new Promise<void>(resolve => {finished = resolve;});
  await page.addInitScript(() => {Object.defineProperty(window, "topicAudioPlays", {value: [], writable: true}); HTMLMediaElement.prototype.play = async function () {(window as unknown as {topicAudioPlays: string[]}).topicAudioPlays.push(this.src);};});
  await page.route("**/api/curriculum/pre-a1/topics/pre-a1-t001/listening?part=0", async route => {
    started(); await ready;
    try {await route.fulfill({body: wav, contentType: "audio/wav"});} finally {finished();}
  });
  try {
    await page.goto("/learn/pre-a1"); await selectSkill(page, "listening"); await openTopic(page);
    await page.getByRole("button", {name: "Luister naar het fragment", exact: true}).click(); await pending;
    await page.getByRole("button", {name: "← Alle onderwerpen", exact: true}).click(); await openTopic(page, 2);
    release(); await done;
    await expect(page.locator(".topic-reader h3").first()).toContainText("Reis 2");
    expect(await page.evaluate(() => (window as unknown as {topicAudioPlays: string[]}).topicAudioPlays)).toEqual([]);
    await expect(page.getByRole("button", {name: "Luister naar het fragment", exact: true})).toBeEnabled();
  } finally {release();}
});

test("topic cards and translated reading fit a 320-pixel phone and keyboard focus follows navigation", async ({page}, testInfo) => {
  await mockTopics(page);
  await page.setViewportSize({width: 320, height: 850});
  await page.goto("/learn/pre-a1"); await page.getByLabel("Taalhulp / language").selectOption("nl-fa-en");
  await selectSkill(page, "reading");
  const bank = page.locator(".skill-topic-library");
  await expect(bank.locator('[lang="fa"]').first()).toHaveAttribute("dir", "rtl");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const cardsAudit = await new AxeBuilder({page}).include(".skill-topic-library").withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(cardsAudit.violations).toEqual([]);
  await testInfo.attach("topic-cards-320-rtl", {body: await page.screenshot({fullPage: true}), contentType: "image/png"});
  await openTopic(page);
  await expect(page.locator(".topic-detail-heading h3")).toBeFocused();
  await expect(page.locator(".topic-reading-text [lang=en]")).toHaveCount(0);
  await page.getByRole("button", {name: "Vertaling tonen", exact: true}).click();
  await expect(page.locator(".topic-reading-text [lang=fa]")).toHaveAttribute("dir", "rtl");
  await expect(page.locator(".topic-reading-text [lang=en]")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const detailAudit = await new AxeBuilder({page}).include(".topic-reader").withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(detailAudit.violations).toEqual([]);
  await testInfo.attach("topic-reading-320-rtl", {body: await page.screenshot({fullPage: true}), contentType: "image/png"});
  await page.getByRole("button", {name: "← Alle onderwerpen", exact: true}).click();
  await expect(bank.locator("h3")).toBeFocused();
});

test("an authored A2 topic persists reading evidence through the real API and plays its distinct listening source", async ({page}) => {
  const source = JSON.parse(await readFile(path.resolve(__dirname, "../../../../content/practice/a2.json"), "utf8")) as {
    topics: {id: string; title: {nl: string}; reading: {questions: {id: string; answer_index: number}[]}}[];
  };
  const topic = source.topics.at(-1)!;
  const beforeReading = await (await page.request.get("/api/curriculum/a2/topics?skill=reading")).json();
  const beforeListening = await (await page.request.get("/api/curriculum/a2/topics?skill=listening")).json();
  const beforeDetail = await (await page.request.get(`/api/curriculum/a2/topics/${topic.id}?skill=reading`)).json();
  const expectedCount = beforeReading.completed_count + (beforeDetail.progress.completed ? 0 : 1);
  await page.goto("/learn/a2");
  const nav = page.getByRole("navigation", {name: "Onderdelen van dit niveau"});
  await nav.getByRole("button", {name: "Lezen", exact: true}).click();
  await expect(page.locator(".skill-topic-library h3")).toHaveText("100 onderwerpen voor lezen");
  await page.getByLabel("Zoek een situatie").fill(topic.title.nl);
  await page.getByRole("button", {name: `Oefen ${topic.title.nl}`, exact: true}).click();
  await expect(page.locator(".topic-reading-text")).toBeVisible();
  for (const question of topic.reading.questions) await page.locator(`input[name="q-${question.id}"]`).nth(question.answer_index).check();
  await page.getByRole("button", {name: "Rond lezen af", exact: true}).click();
  await expect(page.locator(".practice-feedback")).toContainText(`${topic.reading.questions.length} van ${topic.reading.questions.length} juist`);
  await page.reload();
  await nav.getByRole("button", {name: "Lezen", exact: true}).click();
  await expect(page.locator(".topic-progress-number")).toHaveText(`${expectedCount} / 100`);
  const persisted = await (await page.request.get(`/api/curriculum/a2/topics/${topic.id}?skill=reading`)).json();
  expect(persisted.progress).toEqual({completed: true, attempted: true});
  await nav.getByRole("button", {name: "Luisteren", exact: true}).click();
  await expect(page.locator(".topic-progress-number")).toHaveText(`${beforeListening.completed_count} / 100`);
  await page.getByLabel("Zoek een situatie").fill(topic.title.nl);
  await page.getByRole("button", {name: `Oefen ${topic.title.nl}`, exact: true}).click();
  const audio = page.waitForResponse(response => response.url().includes(`/topics/${topic.id}/listening?part=0`));
  await page.getByRole("button", {name: "Luister naar het fragment", exact: true}).click();
  const response = await audio;
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("audio/");
  await expect(page.locator('.topic-reader audio[aria-label="Luisterfragment"]')).toBeVisible();
  await expect(page.getByText("Testtoon; dit is geen luistervoorbeeld.", {exact: true})).toBeVisible();
  const afterListening = await (await page.request.get("/api/curriculum/a2/topics?skill=listening")).json();
  expect(afterListening.completed_count).toBe(beforeListening.completed_count);
});
