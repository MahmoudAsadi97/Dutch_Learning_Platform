import type { Metadata } from "next";
import { MissionCatalog } from "@/components/MissionCatalog";

export const metadata: Metadata = { title: "Oefenmissies" };
export default function MissionsPage() {
  return <div className="dashboard"><header className="page-heading"><div><h1>Uw oefenbibliotheek</h1><p>Kies een situatie en oefen op uw eigen tempo.</p></div></header><MissionCatalog /></div>;
}
