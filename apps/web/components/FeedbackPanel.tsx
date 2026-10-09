"use client";

import { useState } from "react";

import { LearningText } from "@/components/LanguageSupport";
import { ApiError, apiJson, newRequestId } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { uiCopy, type Copy } from "@/lib/ui-copy";
import { missionsCopy } from "@/lib/copy/missions";
import type { FeedbackReportView, SessionDetail } from "@/lib/types";
import { HonestyChip } from "@/components/ui/HonestyChip";
import { UiText } from "@/components/ui/UiText";

interface Props {
  stepKey: string;
  detail: SessionDetail | null;
  onDetail: (detail: SessionDetail) => void;
  onProgressChanged?: () => void;
}

const KIND_LABEL: Record<string, { nl: string; fa: string; className: string }> = {
  strength: { nl: "sterk", fa: "نقطهٔ قوت", className: "ok" },
  error: { nl: "fout", fa: "خطا", className: "bad" },
  suggestion: { nl: "tip", fa: "پیشنهاد", className: "warn" },
};

/**
 * Feedback on one step. The report comes from the model, but every point carries the ids of the
 * evidence it was checked against; points the model could not tie to real evidence were dropped by
 * the server and are never shown as learning advice.
 */
export function FeedbackPanel({ stepKey, detail, onDetail, onProgressChanged }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Copy | null>(null);
  const [requestId, setRequestId] = useState(() => newRequestId());
  const reports = (detail?.feedback ?? []).filter((r) => r.step_key === stepKey);
  const latest: FeedbackReportView | undefined = reports[reports.length - 1];

  async function ask() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      const response = await apiJson<{ report: FeedbackReportView }>(
        `practice/sessions/${detail.session.id}/feedback`,
        {
          method: "POST",
          body: { step_key: stepKey },
          requestId,
        },
      );
      const others = detail.feedback.filter((r) => r.id !== response.report.id);
      onDetail({ ...detail, feedback: [...others, response.report] });
      onProgressChanged?.();
      setRequestId(newRequestId());
    } catch (cause) {
      setError(
        errorCopy(cause, missionsCopy.feedbackUnavailable, {
          409: uiCopy.errors.evidenceShort,
          503: missionsCopy.feedbackUnavailable,
        }),
      );
      if (cause instanceof ApiError && cause.status >= 500) setRequestId(newRequestId());
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      className="card"
      aria-labelledby={`${stepKey}-feedback-heading`}
      data-testid={`${stepKey}-feedback`}
    >
      <h3 id={`${stepKey}-feedback-heading`}>
        <LearningText text={{ nl: "Feedback", en: "Feedback", fa: "بازخورد" }} />
      </h3>
      <div className="honesty-row">
        <p className="muted">
          <UiText text={missionsCopy.feedbackIntro} tier="guide" />
        </p>
        <HonestyChip kind="feedback" />
      </div>
      <p>
        <button
          type="button"
          className="button secondary"
          onClick={() => void ask()}
          disabled={busy || !detail}
          data-testid={`${stepKey}-feedback-ask`}
        >
          <UiText
            text={
              busy
                ? missionsCopy.feedbackBusy
                : latest
                  ? missionsCopy.feedbackAgain
                  : missionsCopy.feedbackAsk
            }
            inline
          />
        </button>
      </p>
      {error && (
        <p className="error" role="alert">
          <UiText text={error} tier="guide" />
        </p>
      )}
      {latest && (
        <div data-testid={`${stepKey}-feedback-report`}>
          <p>
            <LearningText text={{ nl: latest.summary_nl, en: latest.summary_en, fa: latest.summary_fa }} />
          </p>
          <ul className="feedback-points" data-testid={`${stepKey}-feedback-points`}>
            {latest.points.map((point, index) => {
              const label = KIND_LABEL[point.kind] ?? KIND_LABEL.suggestion;
              return (
                <li key={`${latest.id}-${index}`} data-kind={point.kind}>
                  <span className={`label ${label.className}`}>
                    <LearningText text={label} />
                  </span>
                  <LearningText text={{ nl: point.text_nl, en: point.text_en, fa: point.text_fa }} />
                  {point.quote && (
                    <span className="muted" style={{ display: "block", fontSize: "0.9rem" }} lang="nl">
                      „{point.quote}”{point.correction && ` → ${point.correction}`}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </section>
  );
}
