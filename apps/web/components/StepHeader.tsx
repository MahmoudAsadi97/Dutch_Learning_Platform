import { ContentLabel } from "@/components/ContentLabel";
import type { Step } from "@/lib/types";

interface Props {
  step: Step;
  labels: { unreviewed_nl: string; unreviewed_fa: string };
  children?: React.ReactNode;
}

/** Title, review label and bilingual instructions, shared by every step. */
export function StepHeader({ step, labels, children }: Props) {
  return (
    <header className="step-header">
      <h2 id="step-title">
        {step.title.nl}
        <span className="fa" lang="fa" style={{ display: "block", fontSize: "1rem", fontWeight: 400 }}>
          {step.title.fa}
        </span>
      </h2>
      <p>
        <ContentLabel status={step.instructions.review_status} labelNl={labels.unreviewed_nl} labelFa={labels.unreviewed_fa} />
      </p>
      <p lang="nl">{step.instructions.nl}</p>
      <p className="fa" lang="fa">
        {step.instructions.fa}
      </p>
      {children}
    </header>
  );
}
