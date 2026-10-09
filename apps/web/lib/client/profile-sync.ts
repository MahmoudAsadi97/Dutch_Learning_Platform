/**
 * Which support mode wins when the device and the server disagree. The device keeps a synchronous
 * snapshot so the first paint never flashes; the server is the record once it has a value.
 */
export type SupportMode = "nl-en" | "nl-fa" | "nl-fa-en";

const MODES: readonly SupportMode[] = ["nl-en", "nl-fa", "nl-fa-en"];

export function isSupportMode(value: unknown): value is SupportMode {
  return typeof value === "string" && (MODES as readonly string[]).includes(value);
}

export interface Reconciled {
  /** The mode the interface should show now. */
  mode: SupportMode;
  /** True when the device's choice should be written to the server (the server had none). */
  upload: boolean;
}

/**
 * - server null: the device's choice stands and is uploaded once;
 * - server set: the server wins, even over a different device value;
 * - anything invalid falls back to nl-en.
 */
export function reconcileMode(local: unknown, server: unknown): Reconciled {
  if (isSupportMode(server)) return { mode: server, upload: false };
  if (isSupportMode(local)) return { mode: local, upload: true };
  return { mode: "nl-en", upload: false };
}
