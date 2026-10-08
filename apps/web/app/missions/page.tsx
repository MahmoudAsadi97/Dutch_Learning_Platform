import type { Metadata } from "next";
import { MissionCatalog } from "@/components/MissionCatalog";

export const metadata: Metadata = { title: "Oefenmissies" };
export default function MissionsPage() {
  return (
    <div className="dashboard">
      <header className="page-heading">
        <div>
          <p className="eyebrow">SPREKEN</p>
          <h1>Praktijkgesprekken</h1>
          <p>Kies een situatie en oefen op je eigen tempo.</p>
        </div>
      </header>
      <MissionCatalog />
    </div>
  );
}
