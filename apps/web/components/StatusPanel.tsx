"use client";

import { useEffect, useState } from "react";

import { ApiError, apiJson } from "@/lib/client/api";
import type { PreflightItem } from "@/lib/types";

interface Preflight {
  configuration: Record<string, string | number | boolean>;
  items: PreflightItem[];
  principal: { email: string; identity_provider: string };
  request_id: string;
}

const STATUS_CLASS: Record<string, string> = {
  ok: "ok",
  missing: "bad",
  unreachable: "bad",
  not_configured: "warn",
  pending_m3: "warn",
};

export function StatusPanel() {
  const [data, setData] = useState<Preflight | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiJson<Preflight>("health/preflight")
      .then(setData)
      .catch((cause) => setError(cause instanceof ApiError ? `${cause.detail} (${cause.status})` : "De API is niet bereikbaar."));
  }, []);

  if (error) {
    return (
      <p className="error" role="alert">
        {error}
      </p>
    );
  }
  if (!data) {
    return (
      <p role="status" aria-live="polite">
        Status laden…
      </p>
    );
  }
  return (
    <div>
      <p data-testid="principal">
        Aangemeld als <strong>{data.principal.email}</strong> via <code>{data.principal.identity_provider}</code>
      </p>
      <table className="plain" data-testid="preflight">
        <thead>
          <tr>
            <th scope="col">Onderdeel</th>
            <th scope="col">Modus</th>
            <th scope="col">Status</th>
            <th scope="col">Detail</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((item) => (
            <tr key={item.component}>
              <td>{item.component}</td>
              <td>{item.mode}</td>
              <td>
                <span className={`label ${STATUS_CLASS[item.status] ?? "warn"}`}>{item.status}</span>
              </td>
              <td className="muted">{item.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
