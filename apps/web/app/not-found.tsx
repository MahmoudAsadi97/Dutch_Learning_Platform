import Link from "next/link";
export default function NotFound() {
  return <section className="card empty-state"><div><p className="eyebrow">404 · EVEN TERUG</p><h1>Hier is nog geen les.</h1><p>Deze pagina bestaat niet. Je oefeningen vind je in je leeromgeving.</p><Link className="button" href="/">Naar mijn leerplek</Link></div></section>;
}
