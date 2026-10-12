import { readFile } from "node:fs/promises";
import path from "node:path";
import type { Page } from "@playwright/test";

type Copy = { nl: string; en: string; fa: string };
type Word = { id: string; term: string; topic: Copy; meaning: Copy; example: Copy };
type BaseLibrary = {
  stage_id: string;
  review_status: string;
  vocabulary: Word[];
  stories: { topic: Copy }[];
};

/**
 * Freeze the authored base bank only in visual snapshots. The public library also includes source-linked
 * supplements; source-lessons.spec.ts checks their real API journeys without installing this fixture.
 * Keeping original terms and examples here makes a content-count change independent of a CSS regression.
 */
export async function baseA1LibraryFixture(page: Page): Promise<void> {
  const bank = JSON.parse(
    await readFile(path.resolve(__dirname, "../../../../../content/library/a1.json"), "utf8"),
  ) as BaseLibrary;
  // Use the browser's resolver, including in the pinned visual-test container, to retain the real identity.
  const learnerKey = await page.evaluate(async () => {
    const response = await fetch("/api/library/a1");
    if (!response.ok) throw new Error(`Library overview answered ${response.status}`);
    return (await response.json()).learner_key as string;
  });
  const labels = new Map<string, Copy>();
  for (const item of [...bank.vocabulary, ...bank.stories]) labels.set(item.topic.nl, item.topic);
  const overview = {
    stage_id: bank.stage_id,
    review_status: bank.review_status,
    learner_key: learnerKey,
    vocabulary_count: bank.vocabulary.length,
    story_count: bank.stories.length,
    topics: [...labels.keys()].sort().map((key) => ({
      key,
      label: labels.get(key),
      vocabulary_count: bank.vocabulary.filter((item) => item.topic.nl === key).length,
      story_count: bank.stories.filter((item) => item.topic.nl === key).length,
    })),
  };
  await page.route(/\/api\/library\/a1(?:\?|$)/, (route) => route.fulfill({ json: overview }));
  await page.route(/\/api\/library\/a1\/vocabulary(?:\?|$)/, (route) => {
    const params = new URL(route.request().url()).searchParams;
    const query = (params.get("q") ?? "").normalize("NFKC").toLowerCase();
    const topic = params.get("topic") ?? "";
    const offset = Number(params.get("offset") ?? 0);
    const limit = Number(params.get("limit") ?? 20);
    const items = bank.vocabulary.filter(
      (word) =>
        (!topic || word.topic.nl === topic) &&
        (!query || JSON.stringify(word).normalize("NFKC").toLowerCase().includes(query)),
    );
    return route.fulfill({
      json: { items: items.slice(offset, offset + limit), total: items.length, offset, limit },
    });
  });
}
