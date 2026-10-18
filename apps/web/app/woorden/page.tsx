import type { Metadata } from "next";
import { Suspense } from "react";
import { LegacyStudyRedirect } from "@/components/LegacyStudyRedirect";

export const metadata: Metadata = { title: "Woorden" };

export default function WordsPage() {
  return (
    <Suspense>
      <LegacyStudyRedirect vocabulary />
    </Suspense>
  );
}
