/**
 * Every browser-storage key the app writes, built in one place, and the sign-out sweep that clears the
 * learner-scoped ones. The language preference is not learner data and survives sign-out.
 */

const PREFIX = "taalstudio.";

export const storageKeys = {
  /** Support-language mode; a preference, kept across sign-out. */
  languageSupport: `${PREFIX}language-support`,
  /** Set while a support-language change has not reached the server; it belongs to the signed-in learner. */
  languageSupportUnsent: `${PREFIX}unsent.language-support`,
  /** Answer and goal tones on or off; a preference, kept across sign-out. */
  tones: `${PREFIX}tones`,
  /** Last level visited; a device preference containing no answers or scores. */
  studyStage: `${PREFIX}study-stage`,
  /** Writing draft of the core lesson (sessionStorage). */
  draft: (learnerKey: string, stageId: string) => `${PREFIX}draft.${learnerKey}.${stageId}`,
  /** Final-check attempt in progress (sessionStorage). */
  test: (learnerKey: string, stageId: string) => `${PREFIX}test.${learnerKey}.${stageId}`,
  /** Story Time read marks (localStorage). */
  stories: (learnerKey: string, stageId: string) => `${PREFIX}stories.${learnerKey}.${stageId}`,
  /** Topic writing draft (sessionStorage). */
  topicDraft: (learnerKey: string, stageId: string, skill: string, topicId: string) =>
    `${PREFIX}topic-draft.${learnerKey}.${stageId}.${skill}.${topicId}`,
  /** Guided conversation in progress (sessionStorage). */
  conversation: (learnerKey: string, stageId: string, topicId: string) =>
    `${PREFIX}conversation.${learnerKey}.${stageId}.${topicId}`,
} as const;

/** Prefixes of keys that hold learner data; everything else under `taalstudio.` is a device preference. */
export const LEARNER_KEY_PREFIXES = [
  `${PREFIX}draft.`,
  `${PREFIX}test.`,
  `${PREFIX}stories.`,
  `${PREFIX}topic-draft.`,
  `${PREFIX}conversation.`,
  `${PREFIX}unsent.`,
  // the coach level moved to the learner profile; old copies on a device are still swept at sign-out
  `${PREFIX}practice-stage.`,
] as const;

export function isLearnerKey(key: string): boolean {
  return LEARNER_KEY_PREFIXES.some((prefix) => key.startsWith(prefix));
}

/** Remove every learner-scoped key from the given storages; disabled storage must not throw. */
export function clearLearnerStorage(storages: Pick<Storage, "key" | "length" | "removeItem">[]): number {
  let removed = 0;
  for (const storage of storages) {
    try {
      const keys: string[] = [];
      for (let index = 0; index < storage.length; index += 1) {
        const key = storage.key(index);
        if (key && isLearnerKey(key)) keys.push(key);
      }
      for (const key of keys) {
        storage.removeItem(key);
        removed += 1;
      }
    } catch {
      /* Storage can be disabled or full; signing out must still proceed. */
    }
  }
  return removed;
}

export function browserStorages(): Storage[] {
  if (typeof window === "undefined") return [];
  const found: Storage[] = [];
  for (const name of ["localStorage", "sessionStorage"] as const) {
    try {
      found.push(window[name]);
    } catch {
      /* access can throw when storage is disabled */
    }
  }
  return found;
}
