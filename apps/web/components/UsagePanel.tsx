"use client";

import { ApiError } from "@/lib/client/api";
import { useUsage } from "@/lib/client/queries/usage";

const METRIC_LABEL: Record<string, string> = {
  model_calls: "modeloproepen",
  tokens: "tokens",
  audio_seconds: "seconden audio",
  video_seconds: "seconden video",
};

function format(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

/** Budget counters of the signed-in learner: what today's and the total budget allow and what is used. */
export function UsagePanel() {
  const { data: usage, error: cause } = useUsage();
  const error = cause ? (cause instanceof ApiError ? cause.detail : "De API is niet bereikbaar.") : "";

  if (error) {
    return (
      <p className="error" role="alert">
        {error}
      </p>
    );
  }
  if (!usage) {
    return (
      <p role="status" className="muted">
        Verbruik laden…
      </p>
    );
  }
  return (
    <div data-testid="usage-panel">
      <table className="plain">
        <thead>
          <tr>
            <th scope="col">Teller</th>
            <th scope="col">Vandaag</th>
            <th scope="col">Totaal</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(usage.counters).map(([metric, scopes]) => (
            <tr key={metric}>
              <th scope="row">{METRIC_LABEL[metric] ?? metric}</th>
              <td>
                {format(scopes.daily.used)} van {format(scopes.daily.limit)}
                {scopes.daily.reserved > 0 && (
                  <span className="muted"> (+{format(scopes.daily.reserved)} gereserveerd)</span>
                )}
              </td>
              <td>
                {format(scopes.total.used)} van {format(scopes.total.limit)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted" style={{ fontSize: "0.85rem" }} data-testid="pricing-note">
        {usage.pricing_table_entries === 0
          ? "Prijstabel leeg: geen kostenschatting tot fase B de toegestane besteding vastlegt."
          : usage.estimated_cost
            ? `Geschatte kosten: ${usage.estimated_cost.amount} ${usage.estimated_cost.currency ?? ""}`
            : usage.note}
      </p>
    </div>
  );
}
