import type { Metadata } from "next";
import { Suspense } from "react";
import { LegacyStudyRedirect } from "@/components/LegacyStudyRedirect";

export const metadata: Metadata = { title: "Verhalen" };

export default function StoriesPage() {
  return (
    <Suspense>
      <LegacyStudyRedirect skill="reading" />
    </Suspense>
  );
}
