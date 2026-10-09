/**
 * Which support mode wins when the device and the server disagree. The device keeps a synchronous copy
 * so the first paint never flashes; the server is the record once it has a value.
 */
export type SupportMode = "nl-en" | "nl-fa" | "nl-fa-en";

const MODES: readonly SupportMode[] = ["nl-en", "nl-fa", "nl-fa-en"];

export function isSupportMode(value: unknown): value is SupportMode {
  return typeof value === "string" && (MODES as readonly string[]).includes(value);
}

export interface DeviceMode {
  /** The mode the learner chose on this device, or null when they never chose one here. */
  stored: unknown;
  /** True when that choice was made but the server never confirmed it. */
  pending: boolean;
}

export interface Reconciled {
  /** The mode the interface should show now. */
  mode: SupportMode;
  /** True when the device's choice should be written to the server. */
  upload: boolean;
}

/**
 * - a choice the server never confirmed wins and is sent again;
 * - otherwise a server value wins, even over a different device value;
 * - a server without a value adopts a choice made on this device;
 * - with no choice anywhere nothing is sent: a default is not a choice.
 */
export function reconcileMode(device: DeviceMode, server: unknown): Reconciled {
  const stored = isSupportMode(device.stored) ? device.stored : null;
  if (stored && device.pending) return { mode: stored, upload: true };
  if (isSupportMode(server)) return { mode: server, upload: false };
  if (stored) return { mode: stored, upload: true };
  return { mode: "nl-en", upload: false };
}
