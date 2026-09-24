import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const copy = (nl: string) => ({nl, en: `English: ${nl}`, fa: `فارسی: ${nl}`});
const sessionId = "6bfde106-907c-4fe9-9575-d2e983376cd1";
type RequestBody = {client_turn_id: string; expected_turn: number; action: "respond" | "hint" | "repeat"; text?: string; audio_asset_id?: string};

/** Browser fixtures test interaction and recovery; the API suite tests real scenario enforcement. */
async function conversationFixture(page: Page) {
  const stage = await (await page.request.get("/api/curriculum/a1")).json();
  const choice = {id: "a1-shop", stage_id: "a1", topic_id: "a1-t001", title: copy("Een brood bestellen"), role: copy("De winkelbediende")};
  let state = {
    ...choice, id: sessionId, blueprint_id: choice.id, learner_key: stage.learner_key,
    setup: copy("Je wilt een brood kopen. Vraag de prijs en zeg hoeveel je wilt."), opening: copy("Goeiedag. Wat wilt u kopen?"),
    mode: "typed", status: "active", turn_count: 0, max_turns: 6, recording_max_seconds: 60,
    review_status: "unreviewed", current_goal: copy("Zeg wat je wilt kopen."), summary: null as ReturnType<typeof copy> | null,
    goals: [{goal: copy("Vraag om een brood."), met: false, assisted: false}],
    history: [] as {id: string; number: number; action: string; learner_text: string; reply: ReturnType<typeof copy>; accepted: boolean; assisted: boolean; mode: string}[],
  };
  const calls: {path: string; body: Record<string, unknown>}[] = [];
  let started = false;
  let failNext = false;
  let loseNext = false;
  let hold: Promise<void> | null = null;
  await page.route(/\/api\/topic-conversations(?:\?|\/|$)/, async route => {
    const url = new URL(route.request().url());
    const relative = url.pathname.split("/topic-conversations")[1];
    if (route.request().method() === "GET") {
      if (!relative) await route.fulfill({json: {learner_key: stage.learner_key, items: [{...choice, active_session_id: started && state.status === "active" ? state.id : null}]}});
      else await route.fulfill({json: state});
      return;
    }
    const body = route.request().postDataJSON(); calls.push({path: relative, body});
    if (relative === "/start") {started = true; state = {...state, mode: body.mode, status: "active", turn_count: 0, history: [], summary: null, current_goal: copy("Zeg wat je wilt kopen.")}; await route.fulfill({json: state}); return;}
    if (relative.endsWith("/end")) {state.status = "ended"; state.summary = copy("Je vroeg duidelijk om een brood. Oefen de prijs nog eens."); state.current_goal = null as unknown as ReturnType<typeof copy>; await route.fulfill({json: state}); return;}
    const turn = body as RequestBody;
    if (hold) await hold;
    if (failNext) {failNext = false; await route.fulfill({status: 503, json: {detail: "temporarily unavailable"}}); return;}
    if (state.history.some(item => item.id === turn.client_turn_id)) {await route.fulfill({json: state}); return;}
    expect(turn.expected_turn).toBe(state.turn_count);
    state = {...state, turn_count: state.turn_count + 1, history: [...state.history, {id: turn.client_turn_id, number: state.turn_count + 1, action: turn.action, learner_text: turn.text ?? (turn.audio_asset_id ? "Ik wil graag een brood." : ""), reply: copy(turn.action === "hint" ? "Begin met: Ik wil graag…" : turn.action === "repeat" ? "Goeiedag. Wat wilt u kopen?" : "Dat kan. Een brood kost drie euro. Hoeveel wilt u?"), accepted: turn.action === "respond", assisted: turn.action !== "respond", mode: state.mode}], goals: [{...state.goals[0], met: turn.action === "respond" || state.goals[0].met}]};
    if (loseNext) {loseNext = false; await route.abort("failed"); return;}
    await route.fulfill({json: state});
  });
  return {calls, fail: () => {failNext = true;}, lose: () => {loseNext = true;}, hold: (promise: Promise<void> | null) => {hold = promise;}};
}
async function openConversation(page: Page, mode = "typed") {
  await page.goto("/learn/a1?skill=speaking&topic=a1-t001");
  await page.getByRole("button", {name: "Oefen dit gesprek", exact: true}).click();
  if (mode === "spoken") await page.getByLabel("Spreken met de microfoon", {exact: true}).check();
  await page.getByRole("button", {name: "Begin het gesprek", exact: true}).click();
  await expect(page.locator(".conversation-messages")).toContainText("Goeiedag. Wat wilt u kopen?");
}

test("topic conversation starts deliberately and preserves a failed response with the same retry id", async ({page}) => {
  const fixture = await conversationFixture(page);
  await page.goto("/learn/a1?skill=speaking&topic=a1-t001");
  await expect(page.getByRole("button", {name: "Oefen dit gesprek", exact: true})).toBeVisible();
  expect(fixture.calls).toHaveLength(0);
  await page.getByRole("button", {name: "Oefen dit gesprek", exact: true}).click();
  await page.getByRole("button", {name: "Begin het gesprek", exact: true}).click();
  const response = page.getByLabel("Jouw antwoord in het Nederlands", {exact: true});
  await response.fill("Ik wil graag een brood."); fixture.fail();
  await page.getByRole("button", {name: "Verstuur je antwoord", exact: true}).click();
  await expect(page.locator(".conversation-practice .error")).toContainText("Je invoer blijft staan");
  await expect(response).toHaveValue("Ik wil graag een brood.");
  await page.getByRole("button", {name: "Verstuur je antwoord", exact: true}).click();
  await expect(page.locator(".conversation-status")).toContainText("1 / 6");
  await expect(response).toHaveValue("");
  const turns = fixture.calls.filter(call => call.path.endsWith("/turns"));
  expect(turns).toHaveLength(2); expect(turns[0].body).toEqual(turns[1].body);
  await page.getByRole("button", {name: /Geef me een hint/}).click();
  await expect(page.locator(".conversation-messages")).toContainText("Begin met: Ik wil graag…");
  await expect(page.locator(".conversation-status")).toContainText("2 / 6");
  await page.getByRole("button", {name: "Stop en bekijk mijn oefening", exact: true}).click();
  await expect(page.locator(".conversation-summary")).toContainText("Oefen de prijs nog eens");
  await expect(page.locator(".conversation-summary")).toContainText("Dit gesprek telt niet als eindtoets");
  await expect(page.getByRole("link", {name: "Schrijf over deze situatie"})).toHaveAttribute("href", "/learn/a1?skill=writing&topic=a1-t001");
  await page.getByRole("button", {name: "Oefen het gesprek opnieuw", exact: true}).click();
  await expect(page.getByRole("button", {name: "Begin het gesprek", exact: true})).toBeVisible();
  expect(fixture.calls.filter(call => call.path === "/start")).toHaveLength(1);
  await page.getByRole("button", {name: "Begin het gesprek", exact: true}).click();
  await expect(page.locator(".conversation-status")).toContainText("0 / 6");
  const starts = fixture.calls.filter(call => call.path === "/start");
  expect(starts).toHaveLength(2); expect(starts[0].body.request_id).not.toEqual(starts[1].body.request_id);
});

test("a lost response is recovered from owned history after reload without resending or losing an unsent draft", async ({page}) => {
  const fixture = await conversationFixture(page); await openConversation(page);
  const response = page.getByLabel("Jouw antwoord in het Nederlands", {exact: true});
  await response.fill("Ik wil graag een brood."); fixture.lose();
  await page.getByRole("button", {name: "Verstuur je antwoord", exact: true}).click();
  await expect(page.locator(".conversation-practice .error")).toBeVisible();
  await page.reload(); await page.getByRole("button", {name: "Oefen dit gesprek", exact: true}).click();
  await expect(page.locator(".conversation-status")).toContainText("1 / 6");
  await expect(response).toHaveValue("");
  expect(fixture.calls.filter(call => call.path.endsWith("/turns"))).toHaveLength(1);
  await response.fill("Hoeveel kost dat?");
  await page.reload(); await page.getByRole("button", {name: "Oefen dit gesprek", exact: true}).click();
  await expect(response).toHaveValue("Hoeveel kost dat?");
});

test("a pending spoken upload locks navigation and submits only the owned audio asset", async ({page}) => {
  const fixture = await conversationFixture(page);
  let release = () => {}; const held = new Promise<void>(resolve => {release = resolve;});
  await page.route("**/api/speech/transcribe", async route => {await held; await route.fulfill({json: {audio: {asset_id: "cc91846f-27fc-4bc8-86cc-e879055c75ea"}, transcript: {text: "Ik wil graag een brood."}}});});
  try {
    await openConversation(page, "spoken");
    await page.getByRole("button", {name: "Start de opname", exact: true}).click();
    await expect(page.getByRole("button", {name: "Gesprek sluiten", exact: true})).toBeDisabled();
    await expect(page.getByRole("button", {name: "Startles", exact: true})).toBeDisabled();
    await page.getByRole("button", {name: "Stop de opname", exact: true}).click();
    await expect(page.getByRole("button", {name: "Je opname verwerken…", exact: true})).toBeVisible();
    await expect(page.getByRole("button", {name: "Verstuur je antwoord", exact: true})).toBeDisabled();
    release();
    await expect(page.getByRole("button", {name: "Verstuur je antwoord", exact: true})).toBeEnabled();
    fixture.fail();
    await page.getByRole("button", {name: "Verstuur je antwoord", exact: true}).click();
    await expect(page.locator(".conversation-practice .error")).toBeVisible();
    await page.reload(); await page.getByRole("button", {name: "Oefen dit gesprek", exact: true}).click();
    await expect(page.getByRole("button", {name: "Verstuur je antwoord", exact: true})).toBeEnabled();
    await page.getByRole("button", {name: "Verstuur je antwoord", exact: true}).click();
    await expect(page.locator(".conversation-status")).toContainText("1 / 6");
    const turns = fixture.calls.filter(call => call.path.endsWith("/turns"));
    expect(turns).toHaveLength(2); expect(turns[0].body).toEqual(turns[1].body);
    expect(turns[0].body).toEqual({client_turn_id: expect.any(String), expected_turn: 0, action: "respond", audio_asset_id: "cc91846f-27fc-4bc8-86cc-e879055c75ea"});
    await expect(page.locator(".conversation-learner")).toContainText("ingesproken");
    await expect(page.getByRole("button", {name: "Verstuur je antwoord", exact: true})).toBeDisabled();
  } finally {release();}
});

test("the practice coach loads free suggestions and deep-links to the requested skill and topic", async ({page}) => {
  const calls: string[] = [];
  await page.route(/\/api\/coach\/plan(?:\?|$)/, async route => {
    calls.push(route.request().method());
    const stageId = new URL(route.request().url()).searchParams.get("stage_id") ?? "a1";
    await route.fulfill({json: {stage_id: stageId, history_version: "test", mode: "suggested", notice: copy("Kies zelf welke stap je eerst wilt zetten."), history_count: 0, can_personalise: false, items: ["reading", "writing", "listening"].map((skill, index) => ({id: `${stageId}-t001:${skill}`, stage_id: stageId, topic_id: `${stageId}-t001`, skill, title: copy(`Oefenstap ${index + 1}`), category: copy("Dagelijks leven"), reason: copy("Probeer dezelfde situatie met een andere vaardigheid."), basis: "start", evidence_count: 0}))}});
  });
  await page.goto("/");
  const coach = page.locator(".practice-coach");
  await expect(coach.getByRole("heading", {name: "Jouw volgende oefening"})).toBeVisible();
  await expect(coach.locator(".practice-recommendations li")).toHaveCount(3);
  await coach.getByLabel("Mijn oefenniveau", {exact: true}).selectOption("a2");
  await expect(coach.locator(".recommendation-label").first()).toContainText("A2");
  await coach.getByRole("link", {name: "Open deze oefening"}).nth(1).click();
  await expect(page).toHaveURL(/\/learn\/a2\?skill=writing&topic=a2-t001$/);
  await expect(page.getByLabel("Jouw tekst bij dit onderwerp", {exact: true})).toBeVisible();
  expect(calls.every(method => method === "GET")).toBe(true);
  await page.goto("/"); await expect(page.getByLabel("Mijn oefenniveau", {exact: true})).toHaveValue("a2");
});

test("explicit coaching retries keep the same id and a failed request leaves suggestions usable", async ({page}) => {
  const calls: Record<string, unknown>[] = []; let fail = true;
  const plan = {stage_id: "a1", history_version: "test", mode: "suggested", notice: copy("Je oefent verder met je recente antwoorden."), history_count: 3, can_personalise: true, items: ["reading", "writing", "listening"].map(skill => ({id: `a1-t001:${skill}`, stage_id: "a1", topic_id: "a1-t001", skill, title: copy("Een nieuwe stap"), category: copy("Dagelijks leven"), reason: copy("Je recente antwoord geeft een beginpunt."), basis: "recent_attempt", evidence_count: 1}))};
  await page.route(/\/api\/coach\/plan(?:\?|$)/, async route => {
    if (route.request().method() === "POST") {calls.push(route.request().postDataJSON()); if (fail) {fail = false; await route.fulfill({status: 503, json: {detail: "unavailable"}}); return;}}
    await route.fulfill({json: plan});
  });
  await page.goto("/"); const coach = page.locator(".practice-coach");
  await coach.getByRole("button", {name: "Stem de volgorde op mij af", exact: true}).click();
  await expect(coach.getByRole("alert")).toBeVisible();
  await expect(coach.getByRole("link", {name: "Open deze oefening"})).toHaveCount(3);
  await coach.getByRole("button", {name: "Stem de volgorde op mij af", exact: true}).click();
  await expect(coach.getByRole("alert")).toHaveCount(0);
  expect(calls).toHaveLength(2); expect(calls[0]).toEqual(calls[1]);
});

test("the conversation is readable and accessible at 320px with Persian support", async ({page}, testInfo) => {
  await page.setViewportSize({width: 320, height: 850});
  await page.addInitScript(() => localStorage.setItem("taalstudio.language-support", "nl-fa-en"));
  await conversationFixture(page); await openConversation(page);
  await expect(page.locator(".conversation-practice [lang=fa]").first()).toHaveAttribute("dir", "rtl");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  const audit = await new AxeBuilder({page}).include(".topic-conversation").withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(audit.violations).toEqual([]);
  await testInfo.attach("conversation-phone-persian", {body: await page.screenshot({fullPage: true}), contentType: "image/png"});
});

test("an authored pilot conversation persists a real typed turn and free end summary through the API", async ({page}) => {
  const catalogResponse = await page.request.get("/api/topic-conversations");
  expect(catalogResponse.ok()).toBe(true);
  const catalog = await catalogResponse.json();
  expect(catalog.items).toHaveLength(10);
  const choice = catalog.items.find((item: {stage_id: string}) => item.stage_id === "a1");
  expect(choice).toBeTruthy();
  await page.goto(`/learn/${choice.stage_id}?skill=speaking&topic=${choice.topic_id}`);
  await page.getByRole("button", {name: "Oefen dit gesprek", exact: true}).click();
  await page.getByRole("button", {name: "Begin het gesprek", exact: true}).click();
  await page.getByLabel("Jouw antwoord in het Nederlands", {exact: true}).fill("Goeiedag. Kunt u mij helpen, alstublieft?");
  await page.getByRole("button", {name: "Verstuur je antwoord", exact: true}).click();
  await expect(page.locator(".conversation-status")).toContainText("1 / 6");
  await expect(page.locator(".conversation-learner")).toContainText("Goeiedag. Kunt u mij helpen, alstublieft?");
  await page.getByRole("button", {name: "Stop en bekijk mijn oefening", exact: true}).click();
  await expect(page.locator(".conversation-summary")).toBeVisible();
  await page.reload(); await page.getByRole("button", {name: "Oefen dit gesprek", exact: true}).click();
  await expect(page.locator(".conversation-learner")).toContainText("Goeiedag. Kunt u mij helpen, alstublieft?");
  await expect(page.locator(".conversation-summary")).toBeVisible();
});
