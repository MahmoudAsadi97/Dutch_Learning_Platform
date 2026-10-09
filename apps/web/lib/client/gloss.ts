/**
 * Which interface glosses a learner sees. Dutch chrome always stays; a short translation sits under it
 * for beginners. Pure, so the node:test suite can pin every stage and mode.
 */

export type GlossMode = "auto" | "on" | "off";
/** `chrome`: every label; `guide`: explanations and instructions only; `none`: Dutch only. */
export type GlossLevel = "chrome" | "guide" | "none";
export type GlossTier = "chrome" | "guide" | "always";

// pre-A1 to A2 (and a stage not known yet) get every gloss, the next two get guides, the rest none;
// gloss.test checks this against the registry, which this module does not
// import so the node test runner can load it without the "@/" alias.
const GUIDE_STAGES = new Set(["pre-b1", "b1"]);
const DUTCH_ONLY_STAGES = new Set(["pre-b2", "b2", "pre-c1", "c1", "pre-c2", "c2"]);

export function glossLevelFor(stageId: string | null | undefined, mode: GlossMode): GlossLevel {
  if (mode === "off") return "none";
  if (mode === "on") return "chrome";
  if (stageId && GUIDE_STAGES.has(stageId)) return "guide";
  if (stageId && DUTCH_ONLY_STAGES.has(stageId)) return "none";
  // an early stage, or none known yet: the most help
  return "chrome";
}

/** Whether a text of `tier` shows its gloss at `level`. */
export function glossShown(tier: GlossTier, level: GlossLevel): boolean {
  if (tier === "always") return true;
  if (level === "none") return false;
  if (level === "chrome") return true;
  return tier === "guide";
}
