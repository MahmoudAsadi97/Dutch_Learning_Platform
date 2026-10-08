import { skillAccent } from "@/lib/design/identity";
import { skillOrder, skills } from "@/lib/domain/registry";
import type { Skill } from "@/lib/types";

interface Props {
  /** Which skills count as practised; the four are always shown apart, never summed. */
  done: Partial<Record<Skill, boolean>>;
  label?: string;
  className?: string;
}

/** Four separate segments, one per skill, each read out with its own state. */
export function SkillMeter({ done, label = "Vaardigheden", className = "" }: Props) {
  return (
    // role="list" on a div: the path counts its stages as <li>, so the meter must not add list items
    <div className={`skill-meter ${className}`.trim()} role="list" aria-label={label}>
      {skillOrder.map((skill) => {
        const practised = Boolean(done[skill]);
        return (
          <span
            key={skill}
            role="listitem"
            className={practised ? "skill-meter-item is-done" : "skill-meter-item"}
            data-accent={skillAccent[skill]}
          >
            <span className="skill-meter-bar" aria-hidden="true" />
            <span className="visually-hidden">
              {skills[skill].label.nl}: {practised ? "geoefend" : "nog niet geoefend"}
            </span>
          </span>
        );
      })}
    </div>
  );
}
