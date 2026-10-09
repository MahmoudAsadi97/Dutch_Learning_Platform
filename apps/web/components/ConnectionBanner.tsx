"use client";

import { useEffect, useState } from "react";

import { apiFetch, CONNECTIVITY_EVENT } from "@/lib/client/api";
import { useDeveloperDetails } from "@/components/shell/EnvContext";

type State = "online" | "offline" | "api-down" | "checking";

/**
 * A bar at the top of every page when the browser is offline or the API stopped answering.
 * It clears itself as soon as any call succeeds again, or when the retry button reaches /api/health.
 */
export function ConnectionBanner() {
  const developer = useDeveloperDetails();
  const [state, setState] = useState<State>("online");

  useEffect(() => {
    const onOffline = () => setState("offline");
    const onOnline = () => setState((current) => (current === "offline" ? "checking" : current));
    const onConnectivity = (event: Event) => {
      const reachable = (event as CustomEvent<{ reachable: boolean }>).detail?.reachable;
      setState((current) => (reachable ? "online" : current === "offline" ? "offline" : "api-down"));
    };
    window.addEventListener("offline", onOffline);
    window.addEventListener("online", onOnline);
    window.addEventListener(CONNECTIVITY_EVENT, onConnectivity);
    return () => {
      window.removeEventListener("offline", onOffline);
      window.removeEventListener("online", onOnline);
      window.removeEventListener(CONNECTIVITY_EVENT, onConnectivity);
    };
  }, []);

  useEffect(() => {
    if (state !== "checking") return;
    apiFetch("health")
      .then((response) => setState(response.ok ? "online" : "api-down"))
      .catch(() => setState("api-down"));
  }, [state]);

  if (state === "online") return null;
  return (
    <div className="connection-banner" role="alert" data-testid="connection-banner" data-state={state}>
      <span>
        {state === "offline"
          ? "Geen internetverbinding. Je werk blijft staan; opnames en antwoorden worden pas verstuurd als de verbinding terug is."
          : state === "checking"
            ? "Verbinding controleren…"
            : developer
              ? "De server antwoordt niet. Draait `python scripts/run.py dev`? Je laatste actie kun je opnieuw proberen."
              : "De server antwoordt even niet. Je laatste actie kun je zo opnieuw proberen."}
      </span>
      {state !== "checking" && (
        <button type="button" className="button secondary" onClick={() => setState("checking")}>
          Opnieuw proberen
        </button>
      )}
    </div>
  );
}
