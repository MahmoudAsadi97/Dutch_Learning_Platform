import type { Metadata } from "next";
import { Suspense } from "react";
import { SpeakHub } from "@/components/speak/SpeakHub";

export const metadata: Metadata = { title: "Spreken" };

export default function SpeakPage() {
  return (
    <Suspense>
      <SpeakHub />
    </Suspense>
  );
}
