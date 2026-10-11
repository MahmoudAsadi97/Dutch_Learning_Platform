import type { Page } from "@playwright/test";

/** Route fixtures for the serial, the daily plan and the word bank, shared by the story checks and the
 * screenshot baselines. The API suite proves the engine; these only drive the states a learner meets. */

export const episodeId = "11111111-2222-4333-8444-555555555555";
export const paragraphs = [
  {
    nl: "Het is maandag. Sami gaat naar zijn werk. Hij werkt in de fietsenwinkel.",
    en: "It is Monday. Sami goes to work.",
  },
  {
    nl: "Sami gaat naar de bakkerij op de hoek. Ayşe staat achter de toonbank.",
    en: "Sami goes to the bakery on the corner.",
  },
  {
    nl: "Baas, de oude hond, ligt bij de deur. Hij heeft iets in zijn mond.",
    en: "Baas, the old dog, is lying by the door.",
  },
];
export const glossary = [
  {
    term: "de toonbank",
    meaning_en: "the counter",
    meaning_fa: "پیشخوان",
    example: "Ayşe staat achter de toonbank.",
  },
  { term: "de mond", meaning_en: "the mouth", meaning_fa: "دهان", example: "Hij heeft iets in zijn mond." },
];
export const questions = [
  {
    index: 0,
    prompt: "Waar werkt Sami?",
    options: ["In de bakkerij.", "In de fietsenwinkel.", "Op het station."],
  },
  { index: 1, prompt: "Wie ligt bij de deur?", options: ["Ayşe.", "Tom.", "Baas."] },
];
export const choices = [
  { id: "a" as const, label: "Sami vraagt Tom om hulp." },
  { id: "b" as const, label: "Sami gaat naar mevrouw De Clercq." },
];
export const series = {
  id: "s1",
  title: "De Lindestraat",
  stage_id: "a1",
  episode_count: 3,
  town: "Zilverdonk",
  cast: [
    { name: "Sami", role: "fietsenmaker bij De Trapper" },
    { name: "Ayşe", role: "bakker" },
  ],
  memory: [{ number: 2, title: "De markt", recap: "Sami kocht appels.", choice: "" }],
};

export function episode(overrides: Record<string, unknown> = {}) {
  return {
    id: episodeId,
    number: 3,
    stage_id: "a1",
    status: "ready",
    error_code: "",
    title: "De sleutel van Sami",
    theme: "Een sleutel kwijt",
    theme_source: "auto",
    topic_id: "a1-t004",
    mood: "light",
    word_count: 127,
    read_at: null,
    rating: 0,
    chosen_choice: "",
    created_at: "2026-10-02T07:00:00Z",
    content_status: "generated",
    attempts: 1,
    warnings: [],
    failure_reasons: [],
    paragraphs,
    glossary,
    choices,
    questions,
    answered: false,
    previous_choice: "",
    read_aloud: {},
    provider: "local-ollama-strong",
    model: "llama3.1:8b",
    ...overrides,
  };
}
export function plan(overrides: Record<string, unknown> = {}) {
  return {
    date: "2026-10-02",
    streak: { current: 4, best: 9, today_active: false, today_points: 0, active_days: 12 },
    goal: { target: 20, points: 0, met: false },
    series,
    episode: episode(),
    failed: null,
    awaiting_choice: null,
    words: { due_count: 3, total: 18, learned_count: 5, new_count: 2, preview: [] },
    next_step: "read",
    recent_days: Array.from({ length: 14 }, (_, i) => ({
      day: `2026-09-${String(19 + i).padStart(2, "0")}`,
      points: i % 3 ? 22 : 0,
      goal_met: i % 3 !== 0,
    })),
    levels: [
      { id: "a1", label: "A1" },
      { id: "a2", label: "A2" },
    ],
    ...overrides,
  };
}

export async function storyFixture(page: Page) {
  let state: Record<string, unknown> = episode();
  const posts: string[] = [];
  await page.route(/\/api\/today(?:\/prepare)?(?:\?|$)/, (route) =>
    route.fulfill({ json: plan({ episode: state }) }),
  );
  await page.route(/\/api\/stories\/episodes\/[^/]+(?:\/.*)?$/, async (route) => {
    const url = new URL(route.request().url());
    const action = url.pathname.split(`/stories/episodes/${episodeId}`)[1] ?? "";
    if (route.request().method() === "GET") {
      await route.fulfill({ json: state });
      return;
    }
    posts.push(action);
    const body = route.request().postDataJSON() as Record<string, unknown>;
    if (action === "/read") state = { ...state, read_at: "2026-10-02T08:00:00Z" };
    if (action === "/answers") {
      const chosen = body.answers as Record<string, number>;
      state = {
        ...state,
        read_at: "2026-10-02T08:00:00Z",
        answered: true,
        questions: [
          {
            ...questions[0],
            answer_index: 1,
            evidence: "Hij werkt in de fietsenwinkel.",
            chosen: chosen["0"],
            correct: chosen["0"] === 1,
          },
          {
            ...questions[1],
            answer_index: 2,
            evidence: "Baas, de oude hond, ligt bij de deur.",
            chosen: chosen["1"],
            correct: chosen["1"] === 2,
          },
        ],
      };
    }
    if (action === "/choice") state = { ...state, chosen_choice: String(body.choice) };
    if (action === "/rating") state = { ...state, rating: Number(body.rating) };
    if (action === "/words") {
      await route.fulfill({ json: { item: { id: "w1", term: String(body.term) }, created: true } });
      return;
    }
    if (action === "/translate") {
      await route.fulfill({
        json: { paragraph_index: body.paragraph_index, fa: "ترجمهٔ این بند.", cached: false },
      });
      return;
    }
    await route.fulfill({ json: state });
  });
  return { posts, current: () => state };
}

/** Two due words for the word-review screen; mirrors the shape of GET /api/words. */
export const wordItems = [
  {
    id: "w1",
    term: "de toonbank",
    meaning_en: "the counter",
    meaning_fa: "پیشخوان",
    example: "Ayşe staat achter de toonbank.",
    source_kind: "story",
    source_id: episodeId,
    ease: 2.5,
    interval_days: 1,
    repetitions: 1,
    lapses: 0,
    due_at: "2026-10-02T06:00:00Z",
    due: true,
    learned: false,
    last_grade: 3,
    created_at: "2026-10-01T08:00:00Z",
  },
  {
    id: "w2",
    term: "de mond",
    meaning_en: "the mouth",
    meaning_fa: "دهان",
    example: "Hij heeft iets in zijn mond.",
    source_kind: "story",
    source_id: episodeId,
    ease: 2.36,
    interval_days: 1,
    repetitions: 0,
    lapses: 1,
    due_at: "2026-10-02T06:10:00Z",
    due: true,
    learned: false,
    last_grade: 1,
    created_at: "2026-10-01T08:00:00Z",
  },
];

export async function wordsFixture(page: Page) {
  await page.route(/\/api\/words(?:\?|$)/, (route) =>
    route.fulfill({
      json: { total: 18, due_count: wordItems.length, learned_count: 5, new_count: 2, items: wordItems },
    }),
  );
}
