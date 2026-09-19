import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

/**
 * Browser tests against a running web app (port 3000) that proxies to a running API (port 8000).
 * `scripts/e2e.sh` (or `python scripts/run.py e2e`) starts both with fixture providers and runs this.
 * Chromium is launched with a fake microphone that plays `tests/e2e/fixtures/speech-input.wav`.
 */
const fakeAudio = path.resolve(__dirname, "tests/e2e/fixtures/speech-input.wav");

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    permissions: ["microphone"],
    launchOptions: {
      args: [
        "--use-fake-device-for-media-stream",
        "--use-fake-ui-for-media-stream",
        `--use-file-for-fake-audio-capture=${fakeAudio}`,
        "--autoplay-policy=no-user-gesture-required",
      ],
    },
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    { name: "tablet", use: { ...devices["Desktop Chrome"], viewport: { width: 768, height: 1024 } }, testMatch: /(lesson|steps)\.spec\.ts/ },
    { name: "phone-width", use: { ...devices["Desktop Chrome"], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }, testMatch: /(lesson|steps)\.spec\.ts/ },
  ],
});
