"use client";

import { useState, type ReactNode } from "react";

import { Icon } from "@/components/Icon";
import { useDeveloperDetails } from "@/components/shell/EnvContext";
import { ButtonLink } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { UiText } from "@/components/ui/UiText";
import { uiCopy, type Copy } from "@/lib/ui-copy";

export type HonestyKind = "generated" | "video" | "unreviewed" | "feedback" | "voice" | "check";

const KINDS: Record<HonestyKind, { label: Copy; text: Copy }> = {
  generated: { label: uiCopy.chip.generatedLabel, text: uiCopy.chip.generated },
  video: { label: uiCopy.chip.videoLabel, text: uiCopy.chip.video },
  unreviewed: { label: uiCopy.chip.unreviewedLabel, text: uiCopy.chip.unreviewed },
  feedback: { label: uiCopy.chip.feedbackLabel, text: uiCopy.chip.feedback },
  voice: { label: uiCopy.chip.voiceLabel, text: uiCopy.chip.voice },
  check: { label: uiCopy.chip.checkLabel, text: uiCopy.chip.check },
};

/**
 * One small, honest label per generated or unreviewed surface, instead of a paragraph under every screen.
 * It opens a short explanation in the learner's languages and links to /over. `detail` (model names,
 * automatic-check counts) shows only outside production.
 */
export function HonestyChip({ kind, detail }: { kind: HonestyKind; detail?: ReactNode }) {
  const [open, setOpen] = useState(false);
  const developer = useDeveloperDetails();
  const { label, text } = KINDS[kind];
  return (
    <>
      <button
        type="button"
        className="honesty-chip"
        data-honesty={kind}
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        <Icon name="info" size={15} />
        <span lang="nl">{label.nl}</span>
      </button>
      <Dialog open={open} onClose={() => setOpen(false)} title={<UiText text={label} tier="always" />}>
        <p className="honesty-text">
          <UiText text={text} tier="always" />
        </p>
        {developer && detail && (
          <p className="honesty-detail">
            <strong lang="nl">{uiCopy.chip.details.nl}:</strong> {detail}
          </p>
        )}
        <ButtonLink href="/over" variant="secondary" size="small" icon="arrow" iconEnd>
          <UiText text={uiCopy.chip.more} inline />
        </ButtonLink>
      </Dialog>
    </>
  );
}
