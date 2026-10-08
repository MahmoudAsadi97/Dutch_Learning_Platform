"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon } from "@/components/Icon";
import { LearningText } from "@/components/LanguageSupport";
import { MissionCatalog } from "@/components/MissionCatalog";
import { IconTile } from "@/components/ui/IconTile";
import { apiJson } from "@/lib/client/api";
import { topicHref, type ConversationCatalog, type ConversationChoice } from "@/lib/client/learning-agents";
import { stageLabel } from "@/lib/domain/registry";

/** The short conversations the learner can start, grouped by stage; the catalogue itself is free. */
function ConversationStarters() {
  const [choices, setChoices] = useState<ConversationChoice[] | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    apiJson<ConversationCatalog>("topic-conversations", { signal: controller.signal })
      .then((catalog) => {
        if (!controller.signal.aborted) setChoices(catalog.items);
      })
      .catch(() => {
        if (!controller.signal.aborted) setChoices([]);
      });
    return () => controller.abort();
  }, []);
  const stages = new Map<string, ConversationChoice[]>();
  for (const choice of choices ?? []) {
    const list = stages.get(choice.stage_id) ?? [];
    list.push(choice);
    stages.set(choice.stage_id, list);
  }
  return (
    <section className="card speak-room" aria-labelledby="speak-conversations-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">KORTE GESPREKKEN</p>
          <h2 id="speak-conversations-title">Om de beurt antwoorden en vragen</h2>
          <p className="muted">
            <LearningText
              text={{
                nl: "Bij deze onderwerpen uit je leerpad kun je een kort gesprek voeren.",
                en: "These topics from your path let you hold a short conversation.",
                fa: "با این موضوع‌های مسیرت می‌توانی گفت‌وگوی کوتاهی داشته باشی.",
              }}
            />
          </p>
        </div>
        <IconTile name="message" accent="conversations" />
      </div>
      {choices === null ? (
        <p className="muted" role="status">
          Gesprekken ophalen…
        </p>
      ) : stages.size === 0 ? (
        <p className="muted">
          <LearningText
            text={{
              nl: "Nog geen korte gesprekken. Oefen eerst een spreekonderwerp in je leerpad.",
              en: "No short conversations yet. Practise a speaking topic in your path first.",
              fa: "هنوز گفت‌وگوی کوتاهی نیست. اول یک موضوع گفتاری در مسیرت تمرین کن.",
            }}
          />
        </p>
      ) : (
        [...stages.entries()].map(([stageId, items]) => (
          <div className="speak-stage" key={stageId}>
            <p className="speak-stage-label">{stageLabel(stageId)}</p>
            <ul className="speak-choices">
              {items.map((choice) => {
                const href = topicHref(choice.stage_id, "speaking", choice.topic_id);
                return href ? (
                  <li key={choice.id}>
                    <Link className="button secondary small" href={href}>
                      <Icon name="mic" size={16} />
                      <LearningText text={choice.title} />
                    </Link>
                  </li>
                ) : null;
              })}
            </ul>
          </div>
        ))
      )}
    </section>
  );
}

/** Spreken: practice conversations with four skills, short conversations, and the studio. */
export function SpeakHub() {
  return (
    <div className="speak-hub">
      <header className="page-heading">
        <div>
          <p className="eyebrow">SPREKEN</p>
          <h1>Zeg het in het Nederlands.</h1>
          <p>
            Praktijkgesprekken met vier vaardigheden, korte gesprekken bij je onderwerpen en de spraakstudio
            om je eigen stem te horen.
          </p>
        </div>
      </header>
      <div className="speak-rooms">
        <ConversationStarters />
        <Link className="card speak-room speak-studio" href="/speech-check">
          <div className="section-heading">
            <div>
              <p className="eyebrow">SPRAAKSTUDIO</p>
              <h2>Hoor je eigen stem</h2>
              <p className="muted">
                Test je microfoon, lees een zin voor en vergelijk met een voorbeeld. Geen uitspraakscore.
              </p>
            </div>
            <IconTile name="mic" accent="speaking" />
          </div>
          <span className="speak-studio-link">
            Naar de spraakstudio <Icon name="arrow" size={16} />
          </span>
        </Link>
      </div>
      <MissionCatalog />
    </div>
  );
}
