"use client";

import { useState } from "react";
import { Icon } from "@/components/Icon";
import { useLanguageSupport } from "@/components/LanguageSupport";
import { apiFetch } from "@/lib/client/api";
import { useLearningData } from "@/lib/client/learning";

export function AccountSettings() {
  const { mode } = useLanguageSupport();
  const { data, error, retry } = useLearningData();
  const [exporting, setExporting] = useState(false);
  const [notice, setNotice] = useState("");
  function clearDrafts() {
    for (const name of ["sessionStorage", "localStorage"] as const) {
      try {
        const storage = window[name];
        for (const key of Object.keys(storage)) {
          if (key.startsWith("taalstudio.draft.") || key.startsWith("taalstudio.test.")) storage.removeItem(key);
        }
      } catch { /* Disabled storage must not prevent signing out. */ }
    }
  }
  async function download() {
    setExporting(true);
    setNotice("");
    try {
      const response = await apiFetch("export");
      if (!response.ok) throw new Error("export failed");
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = "taalstudio-oefengegevens.json";
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice("Je gegevensbestand is klaargezet voor download.");
    } catch {
      setNotice(
        "Download mislukt. Probeer het opnieuw; je gegevens blijven bewaard.",
      );
    } finally {
      setExporting(false);
    }
  }
  return (
    <div className="settings-top">
      <section className="card">
        <div className="section-heading">
          <h2>Mijn leerprofiel</h2>
          <span className="icon-tile small sage">
            <Icon name="user" size={20} />
          </span>
        </div>
        {error ? (
          <p role="alert">
            Profiel niet beschikbaar.{" "}
            <button className="linklike" onClick={retry}>
              Opnieuw laden
            </button>
          </p>
        ) : !data ? (
          <p role="status">Profiel laden…</p>
        ) : (
          <dl className="profile-facts">
            <div>
              <dt>Naam</dt>
              <dd>{data.learner.display_name || "Niet ingevuld"}</dd>
            </div>
            <div>
              <dt>Account</dt>
              <dd>{data.learner.email}</dd>
            </div>
            <div>
              <dt>Doeltaal</dt>
              <dd>Nederlands · België</dd>
            </div>
            <div>
              <dt>Taal voor hulp</dt>
              <dd>
                {mode === "nl-en" ? "English" : mode === "nl-fa" ? "فارسی" : "فارسی · English"}
              </dd>
            </div>
          </dl>
        )}
        <p className="muted small-text">
          Accountgegevens komen uit je aanmelding. Je studiegegevens blijven aan
          dit account gekoppeld.
        </p>
        <a className="button secondary" href="/.auth/logout?post_logout_redirect_uri=/" onClick={clearDrafts}>Afmelden</a>
      </section>
      <section className="card">
        <div className="section-heading">
          <h2>Jouw gegevens</h2>
          <span className="icon-tile small sand">
            <Icon name="shield" size={20} />
          </span>
        </div>
        <p>
          Download je oefenpogingen, feedback en vaardigheidsrecords als
          JSON-bestand. Het bestand bevat persoonlijke gegevens: bewaar het
          privé.
        </p>
        <button
          className="button secondary"
          onClick={() => void download()}
          disabled={exporting}
        >
          <Icon name="download" size={18} />
          {exporting ? "Download voorbereiden…" : "Download mijn gegevens"}
        </button>
        {notice && (
          <p role="status" className="export-notice">
            {notice}
          </p>
        )}
        <p className="muted small-text">
          Opnamen staan niet in dit JSON-bestand. Spreek verwijderen en
          bewaartermijnen af met de beheerder. Deze privéversie heeft nog geen
          knop om je account zelf te verwijderen.
        </p>
      </section>
    </div>
  );
}
