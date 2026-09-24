import type { Metadata } from "next";
import { AccountSettings } from "@/components/AccountSettings";
import { StatusPanel } from "@/components/StatusPanel";
import { UsagePanel } from "@/components/UsagePanel";
export const metadata: Metadata = { title: "Instellingen" };
export default function SettingsPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">ALLES OP ZIJN PLEK</p>
          <h1>Jouw leeromgeving.</h1>
          <p>Je account, je gegevens en je gebruikslimieten.</p>
        </div>
      </header>
      <AccountSettings />
      <div className="grid two settings-diagnostics">
        <details className="card">
          <summary>Technische ondersteuning</summary>
          <p className="muted small-text">
            Technische controles voor verbinding en ondersteuning.
          </p>
          <StatusPanel />
        </details>
        <section className="card">
          <h2>Verbruik en budget</h2>
          <p className="muted small-text">
            Je gebruikslimieten zijn geen leerscore.
          </p>
          <UsagePanel />
        </section>
      </div>
    </>
  );
}
