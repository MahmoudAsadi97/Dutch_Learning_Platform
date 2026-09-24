"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiJson } from "@/lib/client/api";
import type { CurriculumCatalog, StageSummary } from "@/lib/client/curriculum";
import { stageLabel } from "@/lib/client/curriculum";
import type { LearningCopy } from "@/components/LanguageSupport";

interface ReviewIssue {path: string; category: string; quote: string; explanation: string}
interface ReviewState {status: string; issues: ReviewIssue[]; summary: string; error_code: string; updated_at: string | null}
interface ReviewTopic {id: string; title: LearningCopy; review: ReviewState}
interface ReviewPage {stage_id: string; offset: number; limit: number; total: number; items: ReviewTopic[]}
const statusLabels: Record<string, string> = {
  not_requested: "Nog niet aangevraagd", queued: "In de wachtrij", running: "Controle bezig",
  development_only: "Ontwikkeltest; geen taalcontrole uitgevoerd",
  needs_review: "Menselijke beoordeling nodig", failed: "Controle niet gelukt", stale: "Inhoud gewijzigd; opnieuw controleren",
};
const categoryLabels: Record<string, string> = {
  grounding: "Onderbouwing", ambiguity: "Onduidelijkheid", language: "Taalgebruik",
  translation: "Vertaling", difficulty: "Moeilijkheid", repetition: "Herhaling",
};

/** The private endpoint is never requested until the ordinary catalogue confirms explicit admin access. */
export function ContentReviewQueue() {
  const [stages, setStages] = useState<StageSummary[] | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    void apiJson<CurriculumCatalog>("curriculum", {signal: controller.signal}).then(result => {
      if (result.admin_bypass) setStages(result.stages);
    }).catch(() => { /* Content administration must not block personal settings. */ });
    return () => controller.abort();
  }, []);
  return stages?.length ? <ReviewPanel stages={stages} /> : null;
}

function ReviewPanel({stages}: {stages: StageSummary[]}) {
  const [stage, setStage] = useState(stages[0].id);
  const [offset, setOffset] = useState(0);
  const [loaded, setLoaded] = useState<{key: string; data: ReviewPage} | null>(null);
  const [loadError, setLoadError] = useState<{key: string; message: string} | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [revision, setRevision] = useState(0);
  const loadKey = `${stage}-${offset}-${revision}`;
  const page = loaded?.data;
  const loading = loaded?.key !== loadKey && loadError?.key !== loadKey;
  const displayedError = error || (loadError?.key === loadKey ? loadError.message : "");
  const mounted = useRef(true);
  useEffect(() => {mounted.current = true; return () => {mounted.current = false;};}, []);
  const refresh = useCallback(() => setRevision(value => value + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    void apiJson<ReviewPage>(`content-review/${stage}?offset=${offset}&limit=12`, {signal: controller.signal}).then(result => {
      if (!controller.signal.aborted) setLoaded({key: loadKey, data: result});
    }).catch(() => {
      if (!controller.signal.aborted) setLoadError({key: loadKey, message: "De redactiewachtrij kon niet worden geladen. Probeer opnieuw."});
    });
    return () => controller.abort();
  }, [stage, offset, loadKey]);
  useEffect(() => {
    if (!page?.items.some(item => ["queued", "running"].includes(item.review.status))) return;
    const timer = window.setTimeout(refresh, 5000);
    return () => window.clearTimeout(timer);
  }, [page, refresh]);
  function chooseStage(value: string) {
    setStage(value); setOffset(0); setSelected([]); setNotice("");
  }
  async function request(ids: string[], retryFailed = false) {
    if (busy || !ids.length) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await apiJson(`content-review/${stage}`, {method: "POST", body: {topic_ids: ids, retry_failed: retryFailed}});
      if (!mounted.current) return;
      setSelected([]);
      setNotice("Controle aangevraagd. Bestaande controles worden hergebruikt; de leerinhoud blijft ongewijzigd.");
      refresh();
    } catch {
      if (mounted.current) setError("Aanvragen lukte niet. Je selectie blijft staan; probeer opnieuw.");
    } finally {if (mounted.current) setBusy(false);}
  }
  const current = loaded?.key === loadKey ? loaded.data : null;
  return <section className="card content-review-panel" aria-labelledby="content-review-heading" style={{gridColumn: "1 / -1", minWidth: 0}}>
    <h2 id="content-review-heading">Redactiewachtrij</h2>
    <p>Controleer maximaal vijf onderwerpen per aanvraag op onduidelijke vragen, taalgebruik, vertalingen en samenhang. Dit gebruikt je modelbudget.</p>
    <p className="muted small-text">Suggesties zijn geen goedkeuring. Ook zonder opmerkingen blijft een bevoegde taalreviewer nodig. Alleen de lesinhoud wordt gecontroleerd, nooit antwoorden of opnamen van cursisten.</p>
    <div className="inline-controls">
      <label htmlFor="review-stage">Niveau voor redactie</label>{" "}
      <select id="review-stage" value={stage} onChange={event => chooseStage(event.target.value)} disabled={busy}>
        {stages.map(item => <option key={item.id} value={item.id}>{stageLabel(item.id)}</option>)}
      </select>{" "}
      <button className="button secondary" type="button" onClick={refresh} disabled={busy || loading}>Vernieuwen</button>
    </div>
    {notice && <p role="status">{notice}</p>}
    {displayedError && <p role="alert">{displayedError} <button type="button" className="linklike" onClick={refresh}>Opnieuw laden</button></p>}
    {loading && <p role="status">Onderwerpen laden…</p>}
    {current && <>
      <fieldset disabled={busy || loading} style={{border: 0, padding: 0, minWidth: 0}}>
        <legend>Kies maximaal vijf onderwerpen ({selected.length}/5)</legend>
        {current.items.map(item => <article key={item.id} className="review-topic" style={{borderTop: "1px solid var(--border, #dce4df)", paddingBlock: "1rem", overflowWrap: "anywhere"}}>
          <label style={{display: "flex", gap: ".75rem", alignItems: "flex-start"}}>
            <input type="checkbox" checked={selected.includes(item.id)}
              disabled={["queued", "running", "needs_review", "failed", "development_only"].includes(item.review.status) || (selected.length >= 5 && !selected.includes(item.id))}
              onChange={event => setSelected(values => event.target.checked ? [...values, item.id] : values.filter(key => key !== item.id))} />
            <strong>{item.title.nl}</strong>
          </label>
          <p className="muted small-text">{statusLabels[item.review.status] ?? "Status onbekend"}</p>
          {item.review.status === "failed" && <>
            <p>{item.review.error_code === "allowance" ? "De gebruikslimiet is bereikt. Pas het budget aan of probeer op een latere dag opnieuw." : item.review.error_code === "interrupted" ? "De eerdere controle werd onderbroken. Er volgt geen automatische betaalde herhaling; gereserveerd verbruik kan nog meetellen." : "Er kwam geen bruikbaar resultaat. De lesinhoud is niet gewijzigd."}</p>
            <button type="button" className="button secondary" onClick={() => void request([item.id], true)}>Controle opnieuw aanvragen: {item.title.nl}</button>
          </>}
          {item.review.status === "needs_review" && <details>
            <summary>{item.review.issues.length} aandachtspunten bekijken</summary>
            <p>{item.review.summary}</p>
            {!item.review.issues.length && <p>Deze controle vond geen aandachtspunten. De inhoud is nog niet door een mens goedgekeurd.</p>}
            <ul>{item.review.issues.map((issue, index) => <li key={`${issue.path}-${index}`}>
              <strong>{categoryLabels[issue.category] ?? "Controlepunt"}</strong> · <code>{issue.path}</code>
              <blockquote>{issue.quote}</blockquote><p>{issue.explanation}</p>
            </li>)}</ul>
          </details>}
        </article>)}
      </fieldset>
      <button className="button" type="button" disabled={busy || loading || !selected.length} onClick={() => void request(selected)}>
        {busy ? "Aanvragen…" : `Controle aanvragen (${selected.length})`}
      </button>
      <nav aria-label="Pagina’s voor redactie" className="inline-controls" style={{marginTop: "1rem"}}>
        <button className="button secondary" type="button" disabled={busy || loading || offset === 0}
          onClick={() => {setOffset(value => Math.max(0, value - 12)); setSelected([]);}}>Vorige</button>{" "}
        <span>{Math.min(offset + 1, current.total)}–{Math.min(offset + 12, current.total)} van {current.total}</span>{" "}
        <button className="button secondary" type="button" disabled={busy || loading || offset + 12 >= current.total}
          onClick={() => {setOffset(value => value + 12); setSelected([]);}}>Volgende</button>
      </nav>
    </>}
  </section>;
}
