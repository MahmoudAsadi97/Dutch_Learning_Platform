"use client";
import Link from "next/link";
export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <section className="card empty-state"><div><p className="eyebrow">EVEN OPNIEUW</p><h1>Deze pagina kon niet worden geladen.</h1><p>Je opgeslagen werk blijft bewaard. Probeer het opnieuw of ga terug naar je leerplek.</p><div className="overview-actions"><button className="button" onClick={reset}>Opnieuw proberen</button><Link className="button secondary" href="/">Naar mijn leerplek</Link></div></div></section>;
}
