"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { apiJson } from "@/lib/client/api";
import { stageLabel, type CurriculumCatalog } from "@/lib/client/curriculum";

export function CurriculumPath() {
  const [data, setData] = useState<CurriculumCatalog | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<CurriculumCatalog>("curriculum", { signal: controller.signal }).then(value => { setData(value); setError(false); }).catch(cause => { if (cause?.name !== "AbortError") setError(true); });
    return () => controller.abort();
  }, [retry]);
  const next = data?.stages.find(stage => stage.unlocked && !stage.passed) ?? data?.stages.at(-1);
  const finished = data?.stages.filter(stage => stage.passed).length ?? 0;
  return <div className="learning-path" data-testid="learning-overview">
    <header className="path-heading">
      <div><p className="eyebrow">JOUW LEERPAD</p><h1>Kleine stappen. Echte gesprekken.</h1><p><LearningText text={{ nl: "Van je eerste woorden naar zelfverzekerd Nederlands.", en: "From your first words to confident Dutch.", fa: "از نخستین واژه‌ها تا هلندی با اعتمادبه‌نفس." }} /></p></div>
      {data?.admin_bypass && <span className="quiet-badge">Testweergave · alle niveaus open</span>}
    </header>
    {error ? <div className="error" role="alert">Je leerpad kon niet worden geladen. <button className="linklike" onClick={() => setRetry(value => value + 1)}>Opnieuw proberen</button></div> : !data ? <div className="path-loading" role="status">Je leerpad laden…</div> : <>
      {next && <section className="continue-panel" aria-labelledby="continue-title">
        <div className="continue-copy"><p className="eyebrow">JOUW VOLGENDE STAP <span>{stageLabel(next.id)}</span></p><h2 id="continue-title">{next.title.nl}</h2><p><LearningText text={next.description} /></p><Link className="button" href={`/learn/${next.id}`}>{next.practice_completed.length ? "Verder leren" : "Begin met leren"}<Icon name="arrow" size={18}/></Link></div>
        <div className="continue-overview"><span className="continue-count">{String(finished).padStart(2, "0")}<span> / {data.stages.length}</span></span><p>niveaus afgerond</p><div className="path-progress" role="progressbar" aria-label="Afgeronde niveaus" aria-valuenow={finished} aria-valuemin={0} aria-valuemax={data.stages.length}><span style={{ width: `${finished / data.stages.length * 100}%` }}/></div><div className="continue-skill-icons" role="group" aria-label="Lezen, luisteren, spreken en schrijven"><Icon name="book"/><Icon name="headphones"/><Icon name="mic"/><Icon name="pen"/></div></div>
      </section>}
      <section aria-labelledby="path-title"><div className="section-heading"><div><h2 id="path-title">Een helder pad vooruit</h2><p className="muted">Oefen vier vaardigheden. Rond de eindtoets af. Ga verder.</p></div><span className="quiet-badge">pre-A1 → C2</span></div>
        <ol className="stage-grid" data-testid="curriculum-path">{data.stages.map((stage, index) => <li key={stage.id} className={`stage-card ${!stage.unlocked ? "stage-locked" : ""} ${stage.passed ? "stage-passed" : ""} ${stage.id === next?.id ? "stage-current" : ""}`}>
          <div className="stage-card-top"><span className="stage-level">{stageLabel(stage.id)}</span><span className="stage-status">{stage.passed ? <><Icon name="check" size={15}/>Afgerond</> : !stage.unlocked ? <><Icon name="shield" size={15}/>Nog gesloten</> : stage.id === next?.id ? "Jouw volgende stap" : "Beschikbaar"}</span></div>
          <h3><LearningText text={stage.title}/></h3><p><LearningText text={stage.description}/></p>
          <div className="stage-practice-status"><span>{stage.practice_completed.length} / 4 vaardigheden</span><span>Eindtoets</span></div>
          {stage.unlocked ? <Link className="stage-link" href={`/learn/${stage.id}`} aria-label={`Open ${stageLabel(stage.id)}: ${stage.title.nl}`}>{stage.passed ? "Opnieuw oefenen" : "Open dit niveau"}<Icon name="arrow" size={17}/></Link> : <p className="stage-lock-reason">Rond {stageLabel(data.stages[index - 1]?.id ?? "pre-a1")} eerst af.</p>}
        </li>)}</ol>
      </section>
      <div className="path-bottom-links"><Link href="/missions"><Icon name="book"/><span><strong>Praktijkgesprekken</strong><small>Pas je Nederlands toe in het dagelijkse leven.</small></span><Icon name="arrow"/></Link><Link href="/speech-check"><Icon name="mic"/><span><strong>Even je stem opwarmen</strong><small>Neem op, luister terug en vergelijk.</small></span><Icon name="arrow"/></Link></div>
      <p className="course-note">Dit is een oefenleerpad met interne voortgangstoetsen, geen officieel taalcertificaat. De nieuwe lessen wachten op taalreview.</p>
    </>}
  </div>;
}
