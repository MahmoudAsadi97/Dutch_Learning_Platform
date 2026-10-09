import type { Metadata } from "next";
import { MissionCatalog } from "@/components/MissionCatalog";
import { UiText } from "@/components/ui/UiText";
import { missionsCopy } from "@/lib/copy/missions";

export const metadata: Metadata = { title: missionsCopy.pageTitle.nl };
export default function MissionsPage() {
  return (
    <div className="dashboard">
      <header className="page-heading">
        <div>
          <p className="eyebrow">
            <UiText text={missionsCopy.pageEyebrow} />
          </p>
          <h1>
            <UiText text={missionsCopy.pageHeading} />
          </h1>
          <p>
            <UiText text={missionsCopy.pageIntro} tier="guide" />
          </p>
        </div>
      </header>
      <MissionCatalog />
    </div>
  );
}
