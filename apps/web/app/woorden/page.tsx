import type { Metadata } from "next";
import { Suspense } from "react";
import { LibraryHub } from "@/components/LibraryHub";

export const metadata: Metadata = { title: "Woorden" };

export default function WordsPage() {
  return (
    <Suspense>
      <LibraryHub kind="words" />
    </Suspense>
  );
}
