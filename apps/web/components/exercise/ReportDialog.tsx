"use client";

import { useEffect, useId, useRef, useState } from "react";

import { AnswerOption } from "@/components/ui/AnswerOption";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Field, Textarea } from "@/components/ui/Field";
import { Notice } from "@/components/ui/Notice";
import { UiText } from "@/components/ui/UiText";
import { exerciseCopy } from "@/lib/copy/exercise";
import { newRequestId } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { exercises, type ReportReason } from "@/lib/client/exercises";
import { uiCopy, type Copy } from "@/lib/ui-copy";

import { hasSound } from "./registry";

const REASONS: { value: ReportReason; text: Copy }[] = [
  { value: "answer_wrong", text: exerciseCopy.reasonAnswerWrong },
  { value: "unclear", text: exerciseCopy.reasonUnclear },
  { value: "sound", text: exerciseCopy.reasonSound },
  { value: "other", text: exerciseCopy.reasonOther },
];

interface Props {
  open: boolean;
  sessionId: string;
  itemId: string;
  kind: string;
  onClose: () => void;
}

/**
 * "Meld een probleem": a reason and an optional note, kept with the item; it changes nothing in the session.
 * Kept mounted while its item is on screen (driven by `open`), so closing returns focus to the button that
 * opened it. A failed report sent again with the same reason and note keeps its request id; a changed one is
 * a new report.
 */
export function ReportDialog({ open, sessionId, itemId, kind, onClose }: Props) {
  const name = useId();
  const [reason, setReason] = useState<ReportReason | null>(null);
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<Copy | null>(null);
  const failed = useRef<{ body: string; requestId: string } | null>(null);
  const action = useRef<HTMLButtonElement>(null);

  // the same button turns from "Verstuur" into "Sluiten": keep focus on it and say that it worked
  useEffect(() => {
    if (sent) action.current?.focus();
  }, [sent]);

  async function send() {
    if (!reason || sending) return;
    const body = JSON.stringify({ reason, note: note.trim() });
    const requestId = failed.current?.body === body ? failed.current.requestId : newRequestId();
    setSending(true);
    setError(null);
    try {
      await exercises.report(sessionId, itemId, requestId, reason, note);
      failed.current = null;
      setSent(true);
    } catch (cause) {
      failed.current = { body, requestId };
      setError(errorCopy(cause, exerciseCopy.reportFailed, undefined, "input"));
    } finally {
      setSending(false);
    }
  }

  const reasons = REASONS.filter((entry) => entry.value !== "sound" || hasSound(kind));
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={<UiText text={exerciseCopy.reportTitle} />}
      description={sent ? undefined : <UiText text={exerciseCopy.reportLead} tier="guide" />}
      closeLabel={uiCopy.action.close.nl}
      actions={
        <Button
          ref={action}
          aria-disabled={!sent && (!reason || sending) ? true : undefined}
          onClick={() => (sent ? onClose() : void send())}
        >
          <UiText text={sent ? uiCopy.action.close : exerciseCopy.reportSend} inline />
        </Button>
      }
    >
      <p className="report-status" role="status">
        {sent && <UiText text={exerciseCopy.reportSent} tier="guide" />}
      </p>
      {!sent && (
        <div className="report-form">
          <fieldset className="answer-group">
            <legend className="answer-group-legend">
              <UiText text={exerciseCopy.reasonLegend} />
            </legend>
            <div className="answer-list report-reasons">
              {reasons.map((entry) => (
                <AnswerOption
                  key={entry.value}
                  name={name}
                  value={entry.value}
                  checked={reason === entry.value}
                  onSelect={(value) => setReason(value as ReportReason)}
                >
                  <UiText text={entry.text} />
                </AnswerOption>
              ))}
            </div>
          </fieldset>
          <Field label={<UiText text={exerciseCopy.reportNote} tier="guide" />}>
            {(control) => (
              <Textarea
                {...control}
                value={note}
                maxLength={500}
                rows={3}
                onChange={(e) => setNote(e.target.value)}
              />
            )}
          </Field>
          {error && (
            <Notice tone="danger" role="alert">
              <UiText text={error} tier="guide" />
            </Notice>
          )}
        </div>
      )}
    </Dialog>
  );
}
