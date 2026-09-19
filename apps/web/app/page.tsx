import Link from "next/link";

import { StatusPanel } from "@/components/StatusPanel";
import { UsagePanel } from "@/components/UsagePanel";

export default function HomePage() {
  return (
    <>
      <h1>Nederlands oefenen</h1>
      <p className="muted">
        Release 0.1: één missie, <em>Een afspraak verzetten</em>, met lezen, luisteren, spreken en schrijven. Hulp in het
        Perzisch.
      </p>
      <div className="grid two">
        <section className="card">
          <h2>Aan de slag</h2>
          <p>
            <Link className="button" href="/missions/appointment-change">
              Open de missie
            </Link>
          </p>
          <p>
            <Link className="button secondary" href="/speech-check">
              Test de microfoon
            </Link>
          </p>
        </section>
        <section className="card">
          <h2>Systeemstatus</h2>
          <StatusPanel />
        </section>
        <section className="card">
          <h2>Verbruik en budget</h2>
          <UsagePanel />
        </section>
      </div>
    </>
  );
}
