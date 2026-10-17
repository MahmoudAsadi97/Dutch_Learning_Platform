import type { Metadata } from "next";
import { Suspense } from "react";
import { LibraryHub } from "@/components/LibraryHub";

export const metadata: Metadata = { title: "Verhalen" };

export default function StoriesPage() {
  return (
    <Suspense>
      <LibraryHub kind="stories" />
    </Suspense>
  );
}
