"use client";

import { useState } from "react";
import { ContentReviewQueue } from "@/components/ContentReviewQueue";
import { Icon } from "@/components/Icon";
import { LearningPreferences } from "@/components/LearningPreferences";
import { useLanguageSupport } from "@/components/LanguageSupport";
import { apiFetch } from "@/lib/client/api";
import { browserStorages, clearLearnerStorage } from "@/lib/client/storage";
import { useLearningData } from "@/lib/client/learning";
import { playTone, setTonesEnabled, useTonesEnabled } from "@/lib/client/tones";

export function AccountSettings() {
  const { mode } = useLanguageSupport();
  const tones = useTonesEnabled();
  const { data, error, retry } = useLearningData();
  const [exporting, setExporting] = useState(false);
  const [notice, setNotice] = useState("");
  function clearDrafts() {
    // Every learner-scoped key goes; the language preference stays (lib/client/storage.ts).
    clearLearnerStorage(browserStorages());
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
      setNotice("Download mislukt. Probeer het opnieuw; je gegevens blijven bewaard.");
    } finally {
      setExporting(false);
    }
  }
  return (
    <div className="settings-top">
      <section className="card">
        <div className="section-heading">
          <h2>Mijn leerprofiel</h2>
          <span className="icon-tile small" data-accent="progress">
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
              <dd>{mode === "nl-en" ? "English" : mode === "nl-fa" ? "فارسی" : "فارسی · English"}</dd>
            </div>
          </dl>
        )}
        <LearningPreferences />
        <p className="muted small-text">
          Accountgegevens komen uit je aanmelding. Je studiegegevens blijven aan dit account gekoppeld.
        </p>
        <a className="button secondary" href="/.auth/logout?post_logout_redirect_uri=/" onClick={clearDrafts}>
          Afmelden
        </a>
      </section>
      <section className="card">
        <div className="section-heading">
          <h2>Geluid</h2>
          <span className="icon-tile small" data-accent="speaking">
            <Icon name="volume" size={20} />
          </span>
        </div>
        <label className="toggle-row">
          <input
            type="checkbox"
            checked={tones}
            onChange={(event) => {
              setTonesEnabled(event.target.checked);
              if (event.target.checked) playTone("correct");
            }}
          />
          <span>
            Korte geluidjes bij een antwoord en bij je dagdoel
            <span className="muted small-text">Staat uit als je systeem minder beweging vraagt.</span>
          </span>
        </label>
      </section>
      <section className="card">
        <div className="section-heading">
          <h2>Jouw gegevens</h2>
          <span className="icon-tile small" data-accent="neutral">
            <Icon name="shield" size={20} />
          </span>
        </div>
        <p>
          Download je oefenpogingen, feedback en vaardigheidsrecords als JSON-bestand. Het bestand bevat
          persoonlijke gegevens: bewaar het privé.
        </p>
        <button className="button secondary" onClick={() => void download()} disabled={exporting}>
          <Icon name="download" size={18} />
          {exporting ? "Download voorbereiden…" : "Download mijn gegevens"}
        </button>
        {notice && (
          <p role="status" className="export-notice">
            {notice}
          </p>
        )}
        <p className="muted small-text">
          Opnamen staan niet in dit JSON-bestand. Spreek verwijderen en bewaartermijnen af met de beheerder.
          Deze privéversie heeft nog geen knop om je account zelf te verwijderen.
        </p>
      </section>
      <ContentReviewQueue />
    </div>
  );
}
