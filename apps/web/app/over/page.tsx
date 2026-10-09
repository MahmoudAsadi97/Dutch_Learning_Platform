import type { Metadata } from "next";

import { AboutContent } from "@/components/AboutContent";

export const metadata: Metadata = { title: "Over de inhoud" };

export default function AboutPage() {
  return <AboutContent />;
}
