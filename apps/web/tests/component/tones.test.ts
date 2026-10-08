import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/** The tones stay silent unless the learner turned them on, and never play under reduced motion. */

let oscillators = 0;
let contextState: AudioContextState = "running";
let resumeDelayMs = 0;

class FakeParam {
  value = 0;
  setValueAtTime() {
    return this;
  }
  linearRampToValueAtTime() {
    return this;
  }
  exponentialRampToValueAtTime() {
    return this;
  }
}

class FakeContext {
  state: AudioContextState = contextState;
  currentTime = 0;
  destination = {};
  resume() {
    return new Promise<void>((resolve) => {
      now += resumeDelayMs;
      this.state = "running";
      resolve();
    });
  }
  createOscillator() {
    oscillators += 1;
    return {
      type: "sine",
      frequency: new FakeParam(),
      connect: (node: unknown) => node,
      start() {},
      stop() {},
    };
  }
  createGain() {
    return { gain: new FakeParam(), connect: (node: unknown) => node };
  }
}

let now = 1_000;
let reduce = false;

async function loadTones() {
  vi.resetModules();
  return import("@/lib/client/tones");
}

beforeEach(() => {
  oscillators = 0;
  contextState = "running";
  resumeDelayMs = 0;
  reduce = false;
  now = 1_000;
  localStorage.clear();
  vi.spyOn(Date, "now").mockImplementation(() => now);
  Object.assign(window, {
    AudioContext: FakeContext,
    matchMedia: (query: string) => ({
      matches: reduce && query.includes("reduce"),
      media: query,
      addEventListener() {},
      removeEventListener() {},
    }),
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("tones", () => {
  it("are off until the learner turns them on", async () => {
    const tones = await loadTones();
    expect(tones.readTonesEnabled()).toBe(false);
    tones.playTone("correct");
    expect(oscillators).toBe(0);
  });

  it("stay silent when switched off", async () => {
    const tones = await loadTones();
    tones.setTonesEnabled(false);
    tones.playTone("goal");
    expect(oscillators).toBe(0);
  });

  it("stay silent under reduced motion even when switched on", async () => {
    const tones = await loadTones();
    tones.setTonesEnabled(true);
    reduce = true;
    tones.playTone("correct");
    expect(oscillators).toBe(0);
  });

  it("play their notes when switched on", async () => {
    const tones = await loadTones();
    tones.setTonesEnabled(true);
    tones.playTone("correct");
    expect(oscillators).toBe(2);
  });

  it("keep the choice when storage refuses the write", async () => {
    const tones = await loadTones();
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("full", "QuotaExceededError");
    });
    tones.setTonesEnabled(true);
    expect(tones.readTonesEnabled()).toBe(true);
  });

  it("play after a quick resume but drop a tone whose context starts late", async () => {
    contextState = "suspended";
    const tones = await loadTones();
    tones.setTonesEnabled(true);
    tones.playTone("correct");
    await Promise.resolve();
    await Promise.resolve();
    expect(oscillators).toBe(2);

    oscillators = 0;
    const late = await loadTones();
    resumeDelayMs = 600;
    late.playTone("correct");
    await Promise.resolve();
    await Promise.resolve();
    expect(oscillators).toBe(0);
  });
});
