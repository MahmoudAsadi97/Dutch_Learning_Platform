"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { LearningText } from "@/components/LanguageSupport";
import { ContentLabel } from "@/components/ContentLabel";
import { ListeningStep } from "@/components/ListeningStep";
import { ReadingStep } from "@/components/ReadingStep";
import { SpeakingStep } from "@/components/SpeakingStep";
import { WritingStep } from "@/components/WritingStep";
import { UiText } from "@/components/ui/UiText";
import { apiJson, newRequestId } from "@/lib/client/api";
import { errorCopy } from "@/lib/client/error-copy";
import { useNavigationGuard } from "@/lib/client/navigation";
import { recordStatus } from "@/lib/client/learning";
import { missionsCopy } from "@/lib/copy/missions";
import type {
  CheckpointPayload,
  ListeningPayload,
  MissionResponse,
  PracticeSessionView,
  ReadingPayload,
  SessionDetail,
  SkillRecordView,
  SpeakingPayload,
  Step,
  WritingPayload,
} from "@/lib/types";
import { skillList } from "@/lib/domain/registry";
import { fill, uiCopy, type Copy } from "@/lib/ui-copy";

const SKILL_LABEL: Record<string, { nl: string; fa: string }> = Object.fromEntries(
  skillList.map((skill) => [skill.key, { nl: skill.label.nl, fa: skill.label.fa }]),
);

type Variant = "base" | "transfer";

interface Props {
  missionId: string;
}

type LoadState =
  { kind: "loading" } | { kind: "error"; message: Copy } | { kind: "ready"; mission: MissionResponse };

async function loadMission(missionId: string): Promise<{
  mission: MissionResponse;
  records: SkillRecordView[];
  sessions: Record<Variant, SessionDetail | null>;
}> {
  const mission = await apiJson<MissionResponse>(`missions/${missionId}`);
  const progress = await apiJson<{ skill_records: SkillRecordView[] }>("progress");
  // An active session per variant is resumed, so a reload never loses the conversation.
  const active = await apiJson<{ sessions: PracticeSessionView[] }>(
    `practice/sessions?mission_id=${missionId}&status=active`,
  );
  const sessions: Record<Variant, SessionDetail | null> = { base: null, transfer: null };
  for (const variant of ["base", "transfer"] as const) {
    const found = active.sessions.find((s) => s.variant === variant);
    if (found) sessions[variant] = await apiJson<SessionDetail>(`practice/sessions/${found.id}`);
  }
  return { mission, records: progress.skill_records.filter((r) => r.mission_id === missionId), sessions };
}

/**
 * Updates arrive from independent calls (an answer, a help rung, an autosave) that each carry the detail they
 * started from; merging by id keeps the newest of everything instead of letting the last reply win.
 */
function mergeDetail(current: SessionDetail | null, incoming: SessionDetail): SessionDetail {
  if (!current || current.session.id !== incoming.session.id) return incoming;
  const byId = <T extends { id: string }>(a: T[], b: T[]) => {
    const map = new Map(a.map((item) => [item.id, item]));
    for (const item of b) map.set(item.id, item);
    return [...map.values()];
  };
  const at = (value: string) => Date.parse(value) || 0;
  const newerSession =
    at(incoming.session.updated_at) >= at(current.session.updated_at) ? incoming.session : current.session;
  const drafts = { ...current.drafts };
  for (const [key, draft] of Object.entries(incoming.drafts ?? {})) {
    if (!drafts[key] || at(draft.saved_at) >= at(drafts[key].saved_at)) drafts[key] = draft;
  }
  return {
    ...incoming,
    session: newerSession,
    turns: byId(current.turns, incoming.turns).sort((a, b) => a.turn_index - b.turn_index),
    evidence: byId(current.evidence, incoming.evidence).sort((a, b) => at(a.created_at) - at(b.created_at)),
    feedback: byId(current.feedback, incoming.feedback),
    drafts,
  };
}

export function LessonShell({ missionId }: Props) {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Record<Variant, SessionDetail | null>>({
    base: null,
    transfer: null,
  });
  // One request id per variant for starting a session: reused on retry, replaced only after a deliberate restart.
  const startRequestIdsRef = useRef<Record<Variant, string>>({
    base: newRequestId(),
    transfer: newRequestId(),
  });
  const [records, setRecords] = useState<SkillRecordView[]>([]);
  const [busy, setBusy] = useState(false);
  // A Copy for what went well; a failed start keeps the API's own message as a plain string (step 2.8 maps those).
  const [notice, setNotice] = useState<Copy | null>(null);
  const [attempt, setAttempt] = useState(0);
  const sessionsRef = useRef(sessions);
  const pendingStartRef = useRef<Partial<Record<Variant, Promise<SessionDetail>>>>({});
  const beforeLeaveRef = useRef<(() => Promise<boolean>) | null>(null);
  const registerNavigationGuard = useNavigationGuard();
  const [navigating, setNavigating] = useState(false);
  const registerBeforeLeave = useCallback(
    (guard: (() => Promise<boolean>) | null) => {
      beforeLeaveRef.current = guard;
      registerNavigationGuard(guard);
    },
    [registerNavigationGuard],
  );

  async function selectStep(key: string) {
    if (key === activeKey || navigating) return;
    setNavigating(true);
    try {
      if (beforeLeaveRef.current && !(await beforeLeaveRef.current())) return;
      setActiveKey(key);
    } finally {
      setNavigating(false);
    }
  }

  useEffect(() => {
    sessionsRef.current = sessions;
  }, [sessions]);

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
        if (!cancelled)
          setState({ kind: "error", message: errorCopy(error, missionsCopy.loadFailed, undefined, "load") });
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

  /** The active session of a variant, started on first use. Concurrent callers share one request. */
  const ensureSession = useCallback(
    async (variant: Variant): Promise<SessionDetail> => {
      const known = sessionsRef.current[variant];
      if (known) return known;
      const pending = pendingStartRef.current[variant];
      if (pending) return pending;
      // The same request id is reused on retry, so a double click cannot create two sessions;
      // the server also resumes an active session of the same variant.
      const request = apiJson<SessionDetail>("practice/sessions", {
        method: "POST",
        body: { mission_id: missionId, variant },
        requestId: startRequestIdsRef.current[variant],
      })
        .then((detail) => {
          setSessions((current) => ({ ...current, [variant]: detail }));
          sessionsRef.current = { ...sessionsRef.current, [variant]: detail };
          return detail;
        })
        .finally(() => {
          delete pendingStartRef.current[variant];
        });
      pendingStartRef.current[variant] = request;
      return request;
    },
    [missionId],
  );

  async function startSession(variant: Variant) {
    setBusy(true);
    setNotice(null);
    try {
      const detail = await ensureSession(variant);
      setNotice(
        detail.turns.length > 0 || detail.evidence.length > 0
          ? missionsCopy.sessionResumed
          : missionsCopy.sessionStarted,
      );
    } catch (error) {
      setNotice(errorCopy(error, missionsCopy.sessionStartFailed));
    } finally {
      setBusy(false);
    }
  }

  /** Close the active session of a variant and open a fresh one; the old session keeps its turns and evidence. */
  async function restartSession(variant: Variant) {
    const current = sessionsRef.current[variant];
    setBusy(true);
    setNotice(null);
    try {
      if (current && current.session.status === "active") {
        await apiJson(`practice/sessions/${current.session.id}/abandon`, { method: "POST", body: {} });
      }
      sessionsRef.current = { ...sessionsRef.current, [variant]: null };
      setSessions((state) => ({ ...state, [variant]: null }));
      startRequestIdsRef.current = { ...startRequestIdsRef.current, [variant]: newRequestId() };
      const detail = await ensureSession(variant);
      setNotice(
        detail.session.id !== current?.session.id
          ? missionsCopy.sessionRestarted
          : missionsCopy.sessionResumed,
      );
    } catch (error) {
      setNotice(errorCopy(error, missionsCopy.sessionRestartFailed));
    } finally {
      setBusy(false);
    }
  }

  function setDetail(variant: Variant, detail: SessionDetail) {
    // An old in-flight reply must never replace a deliberately restarted session.
    const known = sessionsRef.current[variant];
    if (known && known.session.id !== detail.session.id) return;
    const merged = mergeDetail(sessionsRef.current[variant], detail);
    sessionsRef.current = { ...sessionsRef.current, [variant]: merged };
    setSessions((current) => ({ ...current, [variant]: merged }));
  }

  if (state.kind === "loading") {
    return (
      <p role="status" aria-live="polite">
        <UiText text={missionsCopy.missionLoading} />
      </p>
    );
  }
  if (state.kind === "error") {
    return (
      <div className="card" role="alert">
        <p className="error">
          <UiText text={state.message} tier="guide" />
        </p>

        <button
          type="button"
          className="button"
          onClick={() => {
            setState({ kind: "loading" });
            setAttempt((n) => n + 1);
          }}
        >
          <UiText text={uiCopy.action.retry} inline />
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
      <aside aria-label={missionsCopy.stepsLabel.nl}>
        <div className="card">
          <h1 style={{ fontSize: "1.25rem" }}>
            <LearningText text={mission.title} />
          </h1>
          <p className="muted lesson-title-meta" style={{ fontSize: "0.85rem" }}>
            <UiText
              text={fill(missionsCopy.lessonMeta, { level: mission.cefr_target, count: steps.length })}
              inline
            />
          </p>
          <p>
            <ContentLabel
              status={mission.review.unreviewed === 0 ? "reviewed" : "unreviewed"}
              labelNl={mission.labels.unreviewed_nl}
              labelFa={mission.labels.unreviewed_fa}
            />
          </p>
          <ol className="step-list">
            {steps.map((step, index) => {
              const progress = sessions[step.variant]?.session.step_progress[step.key];
              return (
                <li key={step.key}>
                  <button
                    type="button"
                    disabled={navigating}
                    aria-current={active?.key === step.key ? "step" : undefined}
                    onClick={() => void selectStep(step.key)}
                  >
                    <span className="step-number" aria-hidden="true">
                      {progress?.completed ? "✓" : index + 1}
                    </span>
                    <span>
                      <span className="step-skill">
                        {step.variant === "transfer" ? (
                          <UiText text={missionsCopy.independent} inline />
                        ) : (
                          (SKILL_LABEL[step.skill]?.nl ?? step.skill)
                        )}
                      </span>
                      {step.title.nl}
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </div>
        <div className="card">
          <h2 style={{ fontSize: "1rem" }}>
            <UiText text={missionsCopy.sessionTitle} />
          </h2>
          {baseSession ? (
            <p className="small-text muted" data-testid="session-saved">
              <UiText text={missionsCopy.sessionSaved} tier="guide" />
            </p>
          ) : (
            <button
              type="button"
              className="button"
              onClick={() => void startSession("base")}
              disabled={busy}
            >
              <UiText text={missionsCopy.sessionStart} inline />
            </button>
          )}
          {notice && (
            <p role="status" aria-live="polite">
              <UiText text={notice} tier="guide" />
            </p>
          )}
        </div>
        <div className="card">
          <h2 style={{ fontSize: "1rem" }}>
            <UiText text={missionsCopy.skillsTitle} />
          </h2>
          <ul style={{ paddingInlineStart: "1.1rem", margin: 0 }} data-testid="skill-records">
            {records.map((record) => (
              <li key={record.id}>
                {SKILL_LABEL[record.skill]?.nl ?? record.skill}:{" "}
                <span className="muted">{recordStatus[record.status] ?? record.status}</span>
              </li>
            ))}
            {records.length === 0 && (
              <li className="muted">
                <UiText text={missionsCopy.noRecords} />
              </li>
            )}
          </ul>
        </div>
      </aside>

      <section>
        {active?.payload.type === "reading" ? (
          <ReadingStep
            key={active.key}
            step={active as Step & { payload: ReadingPayload }}
            labels={mission.labels}
            detail={sessions[active.variant]}
            ensureSession={() => ensureSession(active.variant)}
            onDetail={(detail) => setDetail(active.variant, detail)}
            onProgressChanged={refreshRecords}
          />
        ) : active?.payload.type === "listening" ? (
          <ListeningStep
            key={active.key}
            missionId={missionId}
            step={active as Step & { payload: ListeningPayload }}
            labels={mission.labels}
            detail={sessions[active.variant]}
            ensureSession={() => ensureSession(active.variant)}
            onDetail={(detail) => setDetail(active.variant, detail)}
            onProgressChanged={refreshRecords}
          />
        ) : active?.payload.type === "writing" ? (
          <WritingStep
            key={active.key}
            step={active as Step & { payload: WritingPayload }}
            labels={mission.labels}
            detail={sessions[active.variant]}
            ensureSession={() => ensureSession(active.variant)}
            onDetail={(detail) => setDetail(active.variant, detail)}
            onProgressChanged={refreshRecords}
            registerBeforeLeave={registerBeforeLeave}
          />
        ) : active && (active.payload.type === "speaking" || active.payload.type === "checkpoint") ? (
          <SpeakingStep
            key={active.key}
            step={active as Step & { payload: SpeakingPayload | CheckpointPayload }}
            labels={mission.labels}
            detail={sessions[active.variant]}
            starting={busy}
            onStart={() => void startSession(active.variant)}
            onRestart={() => void restartSession(active.variant)}
            onDetail={(detail) => setDetail(active.variant, detail)}
            onProgressChanged={refreshRecords}
          />
        ) : active ? (
          <article className="card" data-step={active.key}>
            <h2>
              <LearningText text={active.title} />
            </h2>
            <p>
              <ContentLabel
                status={active.instructions.review_status}
                labelNl={mission.labels.unreviewed_nl}
                labelFa={mission.labels.unreviewed_fa}
              />
            </p>
            <p>
              <LearningText text={active.instructions} />
            </p>
            <p className="muted">
              <UiText text={fill(missionsCopy.stepNoView, { type: active.payload.type })} tier="guide" />
            </p>
          </article>
        ) : null}
      </section>
    </div>
  );
}
