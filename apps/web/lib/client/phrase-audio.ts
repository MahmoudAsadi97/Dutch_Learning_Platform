/** Explicit, single-speaker playback with bounded tab-only audio reuse. */
export type PhraseAudioError = "unavailable" | "signin" | "limit" | "blocked" | "too-long";
export type PhraseAudioState = {
  owner: string | null;
  phase: "idle" | "loading" | "playing" | "error";
  error?: PhraseAudioError;
  developmentTone?: boolean;
};
export const IDLE_PHRASE_AUDIO: PhraseAudioState = Object.freeze({ owner: null, phase: "idle" });
export type PhraseClip = { blob: Blob; developmentTone?: boolean };
type Player = Pick<HTMLAudioElement, "play" | "pause" | "load" | "removeAttribute" | "onended" | "onerror">;
export type PhraseAudioDependencies = {
  synthesize: (text: string, signal: AbortSignal) => Promise<PhraseClip>;
  player: (url: string) => Player;
  createUrl: (blob: Blob) => string;
  revokeUrl: (url: string) => void;
};

/** Word-boundary chunks preserve every word and never exceed the API's 600-character limit. */
export function splitSpeechText(text: string, limit = 600): string[] {
  const remaining = text.trim().replace(/\s+/g, " ");
  if (!remaining) return [];
  if (limit < 1 || !Number.isInteger(limit)) throw new Error("Invalid speech chunk limit");
  if (remaining.length > 12_000) throw new Error("Speech text is too long");
  const chunks: string[] = [];
  let part = "";
  for (const word of remaining.split(" ")) {
    // Never split a letter pair, surrogate pair or an unusually long unbroken token.
    if (word.length > limit) throw new Error("Speech token is too long");
    if (part && part.length + 1 + word.length > limit) { chunks.push(part); part = ""; }
    part = part ? `${part} ${word}` : word;
  }
  if (part) chunks.push(part);
  return chunks;
}

export class PhraseAudioController {
  private dependencies: PhraseAudioDependencies;
  private maxEntries: number;
  private maxBytes: number;
  private cache = new Map<string, PhraseClip>();
  private cachedBytes = 0;
  private listeners = new Set<() => void>();
  private state: PhraseAudioState = IDLE_PHRASE_AUDIO;
  private generation = 0;
  private request: AbortController | null = null;
  private disposePlayer: (() => void) | null = null;

  constructor(dependencies: PhraseAudioDependencies, limits = { entries: 32, bytes: 8 * 1024 * 1024 }) {
    this.dependencies = dependencies;
    this.maxEntries = limits.entries;
    this.maxBytes = limits.bytes;
  }

  getSnapshot = (): PhraseAudioState => this.state;
  subscribe = (listener: () => void): (() => void) => { this.listeners.add(listener); return () => this.listeners.delete(listener); };
  private publish(state: PhraseAudioState) { this.state = state; this.listeners.forEach(listener => listener()); }

  stop(owner?: string) {
    if (owner !== undefined && this.state.owner !== owner) return;
    this.generation++;
    this.request?.abort();
    this.request = null;
    this.disposePlayer?.();
    this.disposePlayer = null;
    this.publish(IDLE_PHRASE_AUDIO);
  }

  clear() { this.stop(); this.cache.clear(); this.cachedBytes = 0; }

  private remember(text: string, clip: PhraseClip) {
    if (clip.blob.size > this.maxBytes || this.maxEntries < 1) return;
    while (this.cache.size >= this.maxEntries || this.cachedBytes + clip.blob.size > this.maxBytes) {
      const oldest = this.cache.keys().next().value as string | undefined;
      if (oldest === undefined) break;
      this.cachedBytes -= this.cache.get(oldest)!.blob.size;
      this.cache.delete(oldest);
    }
    this.cache.set(text, clip);
    this.cachedBytes += clip.blob.size;
  }

  private async clip(text: string, signal: AbortSignal): Promise<PhraseClip> {
    const cached = this.cache.get(text);
    if (cached) {
      this.cache.delete(text); this.cache.set(text, cached);
      return cached;
    }
    const result = await this.dependencies.synthesize(text, signal);
    if (!signal.aborted) this.remember(text, result);
    return result;
  }

  async play(owner: string, text: string): Promise<void> {
    this.stop();
    const generation = this.generation;
    let chunks: string[];
    try { chunks = splitSpeechText(text); }
    catch { this.publish({ owner, phase: "error", error: "too-long" }); return; }
    if (!chunks.length) return;
    const request = new AbortController();
    this.request = request;
    const current = () => generation === this.generation && !request.signal.aborted;
    let developmentTone = false;
    try {
      for (const chunk of chunks) {
        if (!current()) return;
        this.publish({ owner, phase: "loading" });
        const clip = await this.clip(chunk, request.signal);
        if (!current()) return;
        developmentTone = Boolean(clip.developmentTone);
        const finished = await this.playClip(owner, clip, current);
        if (!finished || !current()) return;
      }
      if (current()) this.publish({ owner, phase: "idle", developmentTone });
    } catch (cause) {
      if (!current()) return;
      const code = cause instanceof Error ? cause.message : "unavailable";
      const allowed: PhraseAudioError[] = ["signin", "limit", "blocked", "too-long"];
      this.publish({ owner, phase: "error", error: allowed.includes(code as PhraseAudioError) ? code as PhraseAudioError : "unavailable" });
    } finally {
      if (current()) { this.request = null; this.disposePlayer?.(); this.disposePlayer = null; }
    }
  }

  private playClip(owner: string, clip: PhraseClip, current: () => boolean): Promise<boolean> {
    const url = this.dependencies.createUrl(clip.blob);
    let player: Player;
    try { player = this.dependencies.player(url); }
    catch (cause) { this.dependencies.revokeUrl(url); return Promise.reject(cause); }
    return new Promise<boolean>((resolve, reject) => {
      let completed = false;
      const clean = () => {
        player.onended = null; player.onerror = null;
        player.pause(); player.removeAttribute("src"); player.load();
        this.dependencies.revokeUrl(url);
      };
      const finish = (value: boolean, error?: string) => {
        if (completed) return;
        completed = true; clean(); this.disposePlayer = null;
        if (error) reject(new Error(error)); else resolve(value);
      };
      this.disposePlayer = () => finish(false);
      player.onended = () => finish(true);
      player.onerror = () => finish(false, "unavailable");
      try {
        // The user clicked this control. Browser gesture policies may still require a second tap
        // after the first network response; that retry reuses the cached clip.
        const playing = player.play();
        void playing.then(() => {
          if (completed || !current()) return;
          this.publish({ owner, phase: "playing", developmentTone: clip.developmentTone });
        }, (cause: unknown) => {
          const blocked = cause instanceof Error && cause.name === "NotAllowedError";
          finish(false, blocked ? "blocked" : "unavailable");
        });
      } catch { finish(false, "unavailable"); }
    });
  }
}
