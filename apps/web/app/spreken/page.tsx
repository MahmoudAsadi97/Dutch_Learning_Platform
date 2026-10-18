import type { Metadata } from "next";
import { Suspense } from "react";
import { LegacyStudyRedirect } from "@/components/LegacyStudyRedirect";

export const metadata: Metadata = { title: "Spreken" };

export default function SpeakPage() {
  return (
    <Suspense>
      <LegacyStudyRedirect skill="speaking" />
    </Suspense>
  );
}
