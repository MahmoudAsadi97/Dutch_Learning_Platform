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

const TIMEOUT_MS = 45_000;

export function StatusPanel() {
  const [data, setData] = useState<Preflight | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    let timedOut = false;
    const slowTimer = window.setTimeout(() => setSlow(true), 8_000);
    const abortTimer = window.setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, TIMEOUT_MS);
    apiJson<Preflight>("health/preflight", { signal: controller.signal })
      .then((payload) => {
        setData(payload);
        setError("");
      })
      .catch((cause: unknown) => {
        if (cause instanceof ApiError) setError(`${cause.detail} (${cause.status})`);
        else if (cause instanceof DOMException && cause.name === "AbortError") {
          // An abort from the cleanup (navigation, strict-mode remount) is not an error; only the timeout is.
          if (timedOut) setError(`Geen antwoord van de API binnen ${TIMEOUT_MS / 1000} seconden.`);
        } else setError("De API is niet bereikbaar.");
      })
      .finally(() => {
        window.clearTimeout(slowTimer);
        window.clearTimeout(abortTimer);
        setSlow(false);
      });
    return () => {
      controller.abort();
      window.clearTimeout(slowTimer);
      window.clearTimeout(abortTimer);
    };
  }, [attempt]);

  if (error) {
    return (
      <div role="alert">
        <p className="error">{error}</p>
        <button
          type="button"
          className="button secondary"
          onClick={() => {
            setError("");
            setAttempt((n) => n + 1);
          }}
        >
          Opnieuw proberen
        </button>
      </div>
    );
  }
  if (!data) {
    return (
      <p role="status" aria-live="polite">
        Status laden…{slow && " De eerste aanvraag kan even duren (routes worden gecompileerd, providers worden gecontroleerd)."}
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
