import { LearningOverview } from "@/components/LearningOverview";
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
      <LearningOverview />
      <div className="grid two">
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
