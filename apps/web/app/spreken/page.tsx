import type { Metadata } from "next";

import { SpeakHub } from "@/components/speak/SpeakHub";

export const metadata: Metadata = { title: "Spreken" };

export default function SpeakPage() {
  return <SpeakHub />;
}
