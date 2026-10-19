import type { Page } from "@playwright/test";
import type { StudyLesson, StudyPart } from "../../lib/client/study";
import { expect, test } from "./fixtures/test";

const makePart = (id: string, title: string): StudyPart => ({
  id,
  title: { nl: title },
  instructions: { nl: "Luister en geef de dag." },
  prompt: { nl: "Wanneer spreken ze af?" },
  sample: null,
  text: [{ nl: "We spreken woensdag af in de bibliotheek." }],
  questions: [{ id: "day", kind: "short", prompt: { nl: "Op welke dag?" }, options: [] }],
  min_words: 1,
  max_words: 10,
});
const lesson: StudyLesson = {
  stage_id: "a1",
  topic_id: "friends",
  skill: "listening",
  title: { nl: "Een afspraak in de bibliotheek" },
  review_status: "unreviewed",
  preparation: { words: [], grammar: [] },
  activities: [{ id: "friends-scene", title: { nl: "Een afspraak" } }],
  activity_id: "friends-scene",
  parts: [makePart("first", "De eerste afspraak"), makePart("second", "De tweede afspraak")],
  policy: { ephemeral: true, pronunciation_assessed: false },
};

/** A real playable PCM fixture: browser media loading and play promises must run normally. */
function recording(): Buffer {
  const rate = 8_000;
  const samples = rate * 3;
  const wav = Buffer.alloc(44 + samples * 2);
  wav.write("RIFF", 0);
  wav.writeUInt32LE(wav.length - 8, 4);
  wav.write("WAVEfmt ", 8);
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);
  wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(rate, 24);
  wav.writeUInt32LE(rate * 2, 28);
  wav.writeUInt16LE(2, 32);
  wav.writeUInt16LE(16, 34);
  wav.write("data", 36);
  wav.writeUInt32LE(samples * 2, 40);
  for (let index = 0; index < samples; index++)
    wav.writeInt16LE(Math.round(Math.sin((index * 440 * 2 * Math.PI) / rate) * 1_000), 44 + index * 2);
  return wav;
}

async function openListening(page: Page) {
  await page.route(/\/api\/study\/a1\/topics\/friends\?/, (route) => route.fulfill({ json: lesson }));
  await page.goto("/learn/a1?skill=listening&topic=friends&step=practise");
  await expect(page.locator(".study-listen-player")).toBeVisible();
}

test("a delayed listening clip plays on the first click and replays without another synthesis", async ({
  page,
}) => {
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  let requests = 0;
  await page.route(/\/api\/study\/a1\/topics\/friends\/audio\?/, async (route) => {
    requests++;
    await pending;
    await route.fulfill({ contentType: "audio/wav", body: recording() });
  });
  await openListening(page);
  const play = page.locator(".study-listen-player > button");
  const audio = page.locator(".study-listen-player audio");
  await play.click();
  await expect.poll(() => requests).toBe(1);
  await expect(play).toBeDisabled();
  release();
  await expect
    .poll(() => audio.evaluate((element: HTMLAudioElement) => !element.paused && element.currentTime > 0))
    .toBe(true);
  await expect(page.locator(".study-error")).toHaveCount(0);
  await audio.evaluate((element: HTMLAudioElement) => {
    element.pause();
    element.currentTime = 0;
  });
  await play.click();
  await expect
    .poll(() => audio.evaluate((element: HTMLAudioElement) => !element.paused && element.currentTime > 0))
    .toBe(true);
  expect(requests).toBe(1);
  await expect(page.locator(".study-error")).toHaveCount(0);
});

test("leaving a listening part while its clip loads cannot start abandoned audio", async ({ page }) => {
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  let firstStarted = false;
  let firstReturned = false;
  await page.route(/\/api\/study\/a1\/topics\/friends\/audio\?/, async (route) => {
    if (new URL(route.request().url()).searchParams.get("part") === "first") {
      firstStarted = true;
      await pending;
      // An aborted request may no longer accept a response; either way it must never play.
      await route.fulfill({ contentType: "audio/wav", body: recording() }).catch(() => {});
      firstReturned = true;
    } else await route.fulfill({ contentType: "audio/wav", body: recording() });
  });
  await openListening(page);
  await page.locator(".study-listen-player > button").click();
  await expect.poll(() => firstStarted).toBe(true);
  await page
    .getByRole("navigation", { name: "Onderdelen van deze vaardigheid" })
    .getByRole("button", { name: /De tweede afspraak/ })
    .click();
  await expect(page).toHaveURL(/part=second/);
  await expect(page.getByRole("heading", { name: "De tweede afspraak", exact: true })).toBeVisible();
  release();
  await expect.poll(() => firstReturned).toBe(true);
  const audio = page.locator(".study-listen-player audio");
  await expect(audio).not.toHaveAttribute("src", /.+/);
  await expect(page.locator(".study-error")).toHaveCount(0);
  await page.locator(".study-listen-player > button").click();
  await expect
    .poll(() => audio.evaluate((element: HTMLAudioElement) => !element.paused && element.currentTime > 0))
    .toBe(true);
  await expect(page.locator(".study-error")).toHaveCount(0);
});
