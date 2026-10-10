"use client";

import { useId, useState } from "react";

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

const REASONS: { value: ReportReason; text: Copy }[] = [
  { value: "answer_wrong", text: exerciseCopy.reasonAnswerWrong },
  { value: "unclear", text: exerciseCopy.reasonUnclear },
  { value: "sound", text: exerciseCopy.reasonSound },
  { value: "other", text: exerciseCopy.reasonOther },
];

interface Props {
  sessionId: string;
  itemId: string;
  onClose: () => void;
}

/** "Meld een probleem": a reason and an optional note, kept with the item; it changes nothing in the session. */
export function ReportDialog({ sessionId, itemId, onClose }: Props) {
  const name = useId();
  const [reason, setReason] = useState<ReportReason | null>(null);
  const [note, setNote] = useState("");
  const [requestId] = useState(() => newRequestId());
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<Copy | null>(null);

  async function send() {
    if (!reason || sending) return;
    setSending(true);
    setError(null);
    try {
      await exercises.report(sessionId, itemId, requestId, reason, note);
      setSent(true);
    } catch (cause) {
      setError(errorCopy(cause, exerciseCopy.reportFailed, undefined, "input"));
    } finally {
      setSending(false);
    }
  }

  return (
    <Dialog
      open
      onClose={onClose}
      title={<UiText text={exerciseCopy.reportTitle} />}
      description={sent ? undefined : <UiText text={exerciseCopy.reportLead} tier="guide" />}
      closeLabel={uiCopy.action.close.nl}
      actions={
        sent ? (
          <Button onClick={onClose}>
            <UiText text={uiCopy.action.close} inline />
          </Button>
        ) : (
          <Button onClick={() => void send()} disabled={!reason || sending}>
            <UiText text={exerciseCopy.reportSend} inline />
          </Button>
        )
      }
    >
      {sent ? (
        <Notice tone="success" role="status">
          <UiText text={exerciseCopy.reportSent} tier="guide" />
        </Notice>
      ) : (
        <div className="report-form">
          <fieldset className="answer-group">
            <legend className="answer-group-legend">
              <UiText text={exerciseCopy.reasonLegend} />
            </legend>
            <div className="answer-list report-reasons">
              {REASONS.map((entry) => (
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
