"use client";

import { useCallback, useEffect, useState } from "react";

import { ContentLabel } from "@/components/ContentLabel";
import { ReadingStep } from "@/components/ReadingStep";
import { SpeakingStep } from "@/components/SpeakingStep";
import { ApiError, apiJson, newRequestId } from "@/lib/client/api";
import type {
  CheckpointPayload,
  MissionResponse,
  PracticeSessionView,
  ReadingPayload,
  SessionDetail,
  SkillRecordView,
  SpeakingPayload,
  Step,
} from "@/lib/types";

const SKILL_LABEL: Record<string, { nl: string; fa: string }> = {
  reading: { nl: "Lezen", fa: "خواندن" },
  listening: { nl: "Luisteren", fa: "شنیدن" },
  speaking: { nl: "Spreken", fa: "گفتن" },
  writing: { nl: "Schrijven", fa: "نوشتن" },
};

type Variant = "base" | "transfer";

interface Props {
  missionId: string;
}

type LoadState =
  | { kind: "loading" }
  | { kind: "error"; message: string; requestId: string }
  | { kind: "ready"; mission: MissionResponse };

async function loadMission(missionId: string): Promise<{ mission: MissionResponse; records: SkillRecordView[]; sessions: Record<Variant, SessionDetail | null> }> {
  const mission = await apiJson<MissionResponse>(`missions/${missionId}`);
  const progress = await apiJson<{ skill_records: SkillRecordView[] }>("progress");
  // An active session per variant is resumed, so a reload never loses the conversation.
  const active = await apiJson<{ sessions: PracticeSessionView[] }>(`practice/sessions?mission_id=${missionId}&status=active`);
  const sessions: Record<Variant, SessionDetail | null> = { base: null, transfer: null };
  for (const variant of ["base", "transfer"] as const) {
    const found = active.sessions.find((s) => s.variant === variant);
    if (found) sessions[variant] = await apiJson<SessionDetail>(`practice/sessions/${found.id}`);
  }
  return { mission, records: progress.skill_records.filter((r) => r.mission_id === missionId), sessions };
}

function describeError(error: unknown): { message: string; requestId: string } {
  return {
    message: error instanceof ApiError ? error.detail : "De API is niet bereikbaar.",
    requestId: error instanceof ApiError ? error.requestId : "",
  };
}

export function LessonShell({ missionId }: Props) {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Record<Variant, SessionDetail | null>>({ base: null, transfer: null });
  const [startRequestIds] = useState<Record<Variant, string>>(() => ({ base: newRequestId(), transfer: newRequestId() }));
  const [records, setRecords] = useState<SkillRecordView[]>([]);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string>("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    loadMission(missionId)
      .then(({ mission, records: loaded, sessions: found }) => {
        if (cancelled) return;
        setState({ kind: "ready", mission });
        setActiveKey((current) => current ?? mission.document.steps[0]?.key ?? null);
        setRecords(loaded);
        setSessions(found);
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ kind: "error", ...describeError(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [missionId, attempt]);

  const refreshRecords = useCallback(() => {
    apiJson<{ skill_records: SkillRecordView[] }>("progress")
      .then((progress) => setRecords(progress.skill_records.filter((r) => r.mission_id === missionId)))
      .catch(() => {
        // the sidebar keeps the last known records
      });
  }, [missionId]);

  async function startSession(variant: Variant) {
    setBusy(true);
    setNotice("");
    try {
      // The same request id is reused on retry, so a double click cannot create two sessions;
      // the server also resumes an active session of the same variant.
      const detail = await apiJson<SessionDetail>("practice/sessions", {
        method: "POST",
        body: { mission_id: missionId, variant },
        requestId: startRequestIds[variant],
      });
      setSessions((current) => ({ ...current, [variant]: detail }));
      setNotice(detail.turns.length > 0 ? "Sessie hervat." : "Sessie gestart.");
    } catch (error) {
      setNotice(error instanceof ApiError ? `Kon geen sessie starten: ${error.detail}` : "Kon geen sessie starten.");
    } finally {
      setBusy(false);
    }
  }

  function setDetail(variant: Variant, detail: SessionDetail) {
    setSessions((current) => ({ ...current, [variant]: detail }));
  }

  if (state.kind === "loading") {
    return (
      <p role="status" aria-live="polite">
        Missie laden…
      </p>
    );
  }
  if (state.kind === "error") {
    return (
      <div className="card" role="alert">
        <p className="error">{state.message}</p>
        {state.requestId && <p className="mono">request {state.requestId}</p>}
        <button
          type="button"
          className="button"
          onClick={() => {
            setState({ kind: "loading" });
            setAttempt((n) => n + 1);
          }}
        >
          Opnieuw proberen
        </button>
      </div>
    );
  }

  const { mission } = state;
  const steps = mission.document.steps;
  const active: Step | undefined = steps.find((s) => s.key === activeKey) ?? steps[0];
  const baseSession = sessions.base?.session ?? null;

  return (
    <div className="lesson-layout">
      <aside aria-label="Stappen">
        <div className="card">
          <h1 style={{ fontSize: "1.25rem" }}>
            {mission.title.nl}
            <span className="fa" lang="fa" style={{ display: "block", fontSize: "1rem", fontWeight: 400 }}>
              {mission.title.fa}
            </span>
          </h1>
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            {mission.cefr_target} · versie {mission.version} · {mission.fixed_word_count}/{mission.word_limit} woorden
          </p>
          <p>
            <ContentLabel status={mission.review.unreviewed === 0 ? "reviewed" : "unreviewed"} labelNl={mission.labels.unreviewed_nl} labelFa={mission.labels.unreviewed_fa} />
            <span className="muted" style={{ fontSize: "0.85rem" }}>
              {mission.review.unreviewed} van {mission.review.total_texts} teksten nog niet nagekeken
            </span>
          </p>
          <ol className="step-list">
            {steps.map((step, index) => {
              const progress = sessions[step.variant]?.session.step_progress[step.key];
              return (
                <li key={step.key}>
                  <button type="button" aria-current={active?.key === step.key ? "step" : undefined} onClick={() => setActiveKey(step.key)}>
                    <span className="step-skill">
                      {index + 1} · {SKILL_LABEL[step.skill]?.nl ?? step.skill} · {step.variant}
                      {progress?.completed ? " · ✓" : ""}
                    </span>
                    {step.title.nl}
                  </button>
                </li>
              );
            })}
          </ol>
        </div>
        <div className="card">
          <h2 style={{ fontSize: "1rem" }}>Sessie</h2>
          {baseSession ? (
            <p className="mono" data-testid="session-id">
              {baseSession.id}
              <br />
              stap: {baseSession.current_step_key}
            </p>
          ) : (
            <button type="button" className="button" onClick={() => void startSession("base")} disabled={busy}>
              Start een oefensessie
            </button>
          )}
          {notice && (
            <p role="status" aria-live="polite">
              {notice}
            </p>
          )}
        </div>
        <div className="card">
          <h2 style={{ fontSize: "1rem" }}>Vaardigheden</h2>
          <ul style={{ paddingInlineStart: "1.1rem", margin: 0 }} data-testid="skill-records">
            {records.map((record) => (
              <li key={record.id}>
                {SKILL_LABEL[record.skill]?.nl ?? record.skill}: <span className="muted">{record.status}</span>
              </li>
            ))}
            {records.length === 0 && <li className="muted">nog geen records</li>}
          </ul>
        </div>
      </aside>

      <section>
        {active?.payload.type === "reading" ? (
          <ReadingStep step={active as Step & { payload: ReadingPayload }} labels={mission.labels} />
        ) : active && (active.payload.type === "speaking" || active.payload.type === "checkpoint") ? (
          <SpeakingStep
            key={active.key}
            step={active as Step & { payload: SpeakingPayload | CheckpointPayload }}
            labels={mission.labels}
            detail={sessions[active.variant]}
            starting={busy}
            onStart={() => void startSession(active.variant)}
            onDetail={(detail) => setDetail(active.variant, detail)}
            onProgressChanged={refreshRecords}
          />
        ) : active ? (
          <article className="card" data-step={active.key}>
            <h2>
              {active.title.nl}
              <span className="fa" lang="fa" style={{ display: "block", fontSize: "1rem", fontWeight: 400 }}>
                {active.title.fa}
              </span>
            </h2>
            <p>
              <ContentLabel status={active.instructions.review_status} labelNl={mission.labels.unreviewed_nl} labelFa={mission.labels.unreviewed_fa} />
            </p>
            <p lang="nl">{active.instructions.nl}</p>
            <p className="fa" lang="fa">
              {active.instructions.fa}
            </p>
            <p className="muted">
              Deze stap ({active.payload.type}) wordt in milestone M2 gebouwd. De inhoud staat al in het missiebestand en is
              geladen.
            </p>
          </article>
        ) : null}
      </section>
    </div>
  );
}
