import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";
import type { StudyCatalog, StudyLesson } from "../../../lib/client/study";

export async function studyLesson(page: Page, stage = "a2", skill = "reading", topic = "family") {
  const response = await page.request.get(`/api/study/${stage}/topics/${topic}?skill=${skill}`);
  expect(response.ok()).toBe(true);
  return (await response.json()) as StudyLesson;
}
export async function studyCatalog(page: Page, stage: string, skill: string) {
  const response = await page.request.get(`/api/study/${stage}/topics?skill=${skill}`);
  expect(response.ok()).toBe(true);
  return (await response.json()) as StudyCatalog;
}
export const exampleFeedback = {
  status: "evaluated",
  score: 7,
  dimensions: { task: 7, grammar: 6, vocabulary: 7, organisation: 8, pronunciation: null },
  summary: {
    nl: "Je boodschap is duidelijk. Kijk naar de werkwoordsvorm.",
    en: "Your message is clear. Check the verb form.",
  },
  corrections: [
    {
      original: "Ik woont",
      replacement: "Ik woon",
      category: "grammar",
      explanation: { nl: "Bij ik gebruik je de stam.", en: "Use the stem with ik." },
    },
  ],
  checks: [],
  pronunciation_note: { nl: "Uitspraak is niet beoordeeld.", en: "Pronunciation has not been assessed." },
  ephemeral: true,
};
