import type { Copy } from "@/lib/ui-copy";

/**
 * What a learner reads when an episode or a video could not be made, chosen by the failure code the API
 * stores on it. Pure and free of runtime imports so the node:test suite loads it; callers pass the
 * catalogue's `failures` group.
 */
export type FailureCopies = Record<
  | "episodeAllowanceTitle"
  | "episodeQualityTitle"
  | "episodeAwayTitle"
  | "episodeQuality"
  | "episodeAllowance"
  | "paidNotApproved"
  | "writerAway"
  | "writerAwayDeveloper"
  | "videoAllowance"
  | "videoTime"
  | "videoQuality"
  | "videoRender"
  | "videoTooLong"
  | "videoAway",
  Copy
>;

/** The heading and the explanation for a failed episode; the local setup hint only for developers. */
export function episodeFailure(
  code: string | null | undefined,
  copies: FailureCopies,
  developer: boolean,
): { title: Copy; body: Copy } {
  if (code === "allowance") return { title: copies.episodeAllowanceTitle, body: copies.episodeAllowance };
  if (code === "quality") return { title: copies.episodeQualityTitle, body: copies.episodeQuality };
  if (code === "paid_not_approved") return { title: copies.episodeAwayTitle, body: copies.paidNotApproved };
  return { title: copies.episodeAwayTitle, body: developer ? copies.writerAwayDeveloper : copies.writerAway };
}

/** Why a video was not made. */
export function videoFailure(code: string | null | undefined, copies: FailureCopies): Copy {
  switch (code) {
    case "allowance":
      return copies.videoAllowance;
    case "allowance_video":
      return copies.videoTime;
    case "quality":
      return copies.videoQuality;
    case "paid_not_approved":
      return copies.paidNotApproved;
    case "render":
    case "render_timeout":
      return copies.videoRender;
    case "too_long":
      return copies.videoTooLong;
    default:
      return copies.videoAway;
  }
}
