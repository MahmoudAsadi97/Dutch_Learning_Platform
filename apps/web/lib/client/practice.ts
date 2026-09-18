/** Calls for the non-conversation steps. Each returns the updated session detail so the caller can store it. */

import { apiJson, newRequestId } from "@/lib/client/api";
import type { AnswerResponse, DraftView, EvidenceView, HelpRung, SessionDetail, WritingResponse } from "@/lib/types";

function withEvidence(detail: SessionDetail, evidence: EvidenceView, session = detail.session): SessionDetail {
  const others = detail.evidence.filter((e) => e.id !== evidence.id);
  return { ...detail, session, evidence: [...others, evidence] };
}

export async function submitAnswer(
  detail: SessionDetail,
  stepKey: string,
  questionId: string,
  chosenIndex: number,
): Promise<{ detail: SessionDetail; correct: boolean; answer_index: number }> {
  const response = await apiJson<AnswerResponse>(`practice/sessions/${detail.session.id}/answers`, {
    method: "POST",
    body: { step_key: stepKey, question_id: questionId, chosen_index: chosenIndex },
    requestId: newRequestId(),
  });
  return { detail: withEvidence(detail, response.evidence, response.session), correct: response.correct, answer_index: response.answer_index };
}

export async function recordHelp(detail: SessionDetail, stepKey: string, rung: HelpRung, questionId = ""): Promise<SessionDetail> {
  const response = await apiJson<{ evidence: EvidenceView; session: SessionDetail["session"] }>(`practice/sessions/${detail.session.id}/help`, {
    method: "POST",
    body: { step_key: stepKey, level: rung.level, kind: rung.kind, question_id: questionId },
    requestId: newRequestId(),
  });
  return withEvidence(detail, response.evidence, response.session);
}

export async function saveDraft(sessionId: string, stepKey: string, text: string): Promise<DraftView> {
  const response = await apiJson<{ draft: DraftView }>(`practice/sessions/${sessionId}/drafts/${stepKey}`, {
    method: "PUT",
    body: { text },
    requestId: newRequestId(),
  });
  return response.draft;
}

export async function submitWriting(
  detail: SessionDetail,
  stepKey: string,
  text: string,
): Promise<{ detail: SessionDetail; word_count: number; missing: string[] }> {
  const response = await apiJson<WritingResponse>(`practice/sessions/${detail.session.id}/writing`, {
    method: "POST",
    body: { step_key: stepKey, text },
    requestId: newRequestId(),
  });
  const next = withEvidence(detail, response.evidence, response.session);
  return {
    detail: { ...next, drafts: { ...next.drafts, [stepKey]: { text, word_count: response.word_count, saved_at: new Date().toISOString(), submitted: true } } },
    word_count: response.word_count,
    missing: response.missing,
  };
}
