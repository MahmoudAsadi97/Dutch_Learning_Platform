"use client";

import { useState } from "react";

import { ApiError, apiJson, newRequestId } from "@/lib/client/api";
import type { FeedbackReportView, SessionDetail } from "@/lib/types";

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
 * the server and are only counted here.
 */
export function FeedbackPanel({ stepKey, detail, onDetail, onProgressChanged }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [requestId, setRequestId] = useState(() => newRequestId());
  const reports = (detail?.feedback ?? []).filter((r) => r.step_key === stepKey);
  const latest: FeedbackReportView | undefined = reports[reports.length - 1];
  const evidenceCount = (detail?.evidence ?? []).filter((e) => e.step_key === stepKey).length;

  async function ask() {
    if (!detail) return;
    setBusy(true);
    setError("");
    try {
      const response = await apiJson<{ report: FeedbackReportView }>(`practice/sessions/${detail.session.id}/feedback`, {
        method: "POST",
        body: { step_key: stepKey },
        requestId,
      });
      const others = detail.feedback.filter((r) => r.id !== response.report.id);
      onDetail({ ...detail, feedback: [...others, response.report] });
      onProgressChanged?.();
      setRequestId(newRequestId());
    } catch (cause) {
      if (cause instanceof ApiError) {
        setError(cause.status === 409 ? `Nog niet genoeg bewijs voor feedback. (${cause.detail})` : `${cause.detail} (request ${cause.requestId})`);
        if (cause.status >= 500) setRequestId(newRequestId());
      } else {
        setError("Geen verbinding met de server.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card" aria-labelledby={`${stepKey}-feedback-heading`} data-testid={`${stepKey}-feedback`}>
      <h3 id={`${stepKey}-feedback-heading`}>
        Feedback · <span className="fa" lang="fa" style={{ display: "inline" }}>بازخورد</span>
      </h3>
      <p className="muted" style={{ fontSize: "0.85rem" }}>
        Feedback van het taalmodel over uw bewijsstukken van deze stap ({evidenceCount}); elk punt verwijst naar het bewijs
        waarop het steunt. Niet nagekeken door een mens.
      </p>
      <p>
        <button type="button" className="button secondary" onClick={() => void ask()} disabled={busy || !detail} data-testid={`${stepKey}-feedback-ask`}>
          {busy ? "Feedback wordt opgesteld…" : latest ? "Vraag nieuwe feedback" : "Vraag feedback"}
        </button>
      </p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {latest && (
        <div data-testid={`${stepKey}-feedback-report`}>
          <p lang="nl">{latest.summary_nl}</p>
          {latest.summary_fa && (
            <p className="fa" lang="fa" dir="rtl">
              {latest.summary_fa}
            </p>
          )}
          <ul className="feedback-points" data-testid={`${stepKey}-feedback-points`}>
            {latest.points.map((point, index) => {
              const label = KIND_LABEL[point.kind] ?? KIND_LABEL.suggestion;
              return (
                <li key={`${latest.id}-${index}`} data-kind={point.kind}>
                  <span className={`label ${label.className}`}>
                    {label.nl} · <span className="fa" lang="fa" style={{ display: "inline" }}>{label.fa}</span>
                  </span>
                  <span lang="nl">{point.text_nl}</span>
                  {point.text_fa && (
                    <span className="fa" lang="fa" dir="rtl" style={{ display: "block" }}>
                      {point.text_fa}
                    </span>
                  )}
                  {point.quote && (
                    <span className="muted" style={{ display: "block", fontSize: "0.9rem" }} lang="nl">
                      „{point.quote}”{point.correction && ` → ${point.correction}`}
                    </span>
                  )}
                  <span className="muted mono" style={{ display: "block", fontSize: "0.75rem" }}>
                    bewijs: {point.evidence_ids.map((id) => id.slice(0, 8)).join(", ")}
                  </span>
                </li>
              );
            })}
          </ul>
          <p className="muted mono" style={{ fontSize: "0.75rem" }}>
            {latest.model_provider} · {latest.model_name} · {latest.prompt_version} · {latest.evidence_ids.length} bewijsstukken
            {latest.dropped_points > 0 && ` · ${latest.dropped_points} punt(en) weggelaten zonder geldig bewijs`}
          </p>
          {latest.dropped_points > 0 && (latest.dropped ?? []).length > 0 && (
            <details data-testid={`${stepKey}-feedback-dropped`}>
              <summary className="muted" style={{ fontSize: "0.85rem", cursor: "pointer" }}>
                Weggelaten punten (niet aan bewijs te koppelen; alleen ter controle)
              </summary>
              <ul className="feedback-points">
                {(latest.dropped ?? []).map((point, index) => (
                  <li key={`${latest.id}-dropped-${index}`} className="muted">
                    <span lang="nl">{point.text_nl}</span>
                    <span className="mono" style={{ display: "block", fontSize: "0.75rem" }}>
                      {point.kind} · verwijzing: {point.evidence.join(", ") || "geen"} · {point.reason}
                      {point.quote && ` · „${point.quote}”`}
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </section>
  );
}
