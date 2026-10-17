"use client";
import { LearningText } from "@/components/LanguageSupport";
import type { StageCoverage } from "@/lib/client/curriculum";
import { workspaceCopy as copy } from "@/lib/copy/workspace";
import { fill } from "@/lib/ui-copy";

export function ContentCoverage({
  coverage,
  compact = false,
}: {
  coverage?: StageCoverage;
  compact?: boolean;
}) {
  if (!coverage) return null;
  const summary = (
    <dl className="coverage-summary" data-testid="content-counts">
      <div>
        <dt>
          <LearningText text={copy.totalWords} />
        </dt>
        <dd>{coverage.words}</dd>
      </div>
      <div>
        <dt>
          <LearningText text={copy.grammar} />
        </dt>
        <dd>{coverage.grammar_questions}</dd>
      </div>
      <div>
        <dt>
          <LearningText text={copy.authored} />
        </dt>
        <dd>
          {coverage.eligible_authored_stories} / {coverage.targets.authored_stories}
        </dd>
      </div>
    </dl>
  );
  if (compact) return summary;
  const rows = [
    { label: copy.totalWords, count: coverage.words, target: coverage.targets.words },
    { label: copy.core, count: coverage.productive_core, target: coverage.targets.productive_core },
    {
      label: copy.grammarCount,
      count: coverage.grammar_questions,
      target: coverage.targets.grammar_questions,
    },
    {
      label: copy.authored,
      count: coverage.eligible_authored_stories,
      target: coverage.targets.authored_stories,
    },
    ...(["reading", "listening", "speaking", "writing"] as const).map((skill) => ({
      label: copy[skill],
      count: coverage.skill_topics[skill],
      target: coverage.targets.skill_topics,
    })),
  ];
  return (
    <details className="content-coverage">
      <summary>
        <LearningText text={copy.details} />
      </summary>
      <div className="coverage-table-scroll">
        <table>
          <caption>
            <LearningText text={copy.coverage} />
          </caption>
          <thead>
            <tr>
              <th scope="col">
                <LearningText text={copy.activity} />
              </th>
              <th scope="col">
                <LearningText text={copy.available} />
              </th>
              <th scope="col">
                <LearningText text={copy.target} />
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                <th scope="row">
                  <LearningText text={row.label} />
                </th>
                <td>{row.count}</td>
                <td>{row.target}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {coverage.shortfalls.authored_stories > 0 && (
        <p className="coverage-shortfall">
          <LearningText
            text={fill(copy.missing, {
              n: coverage.shortfalls.authored_stories,
              target: coverage.targets.authored_stories,
            })}
          />
        </p>
      )}
      <p>
        <LearningText text={copy.legacy} />: {coverage.legacy_stories}
      </p>
      <p>
        <LearningText text={copy.contexts} />: {coverage.productive_contexts}
      </p>
      <p className="small-text muted">
        <LearningText text={copy.countNote} />
      </p>
    </details>
  );
}
