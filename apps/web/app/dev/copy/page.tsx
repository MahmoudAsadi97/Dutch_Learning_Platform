import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CopyReview } from "@/components/dev/CopyReview";
import { isDevRoute } from "@/lib/client/dev-only";

export const metadata: Metadata = { title: "Teksten nakijken · Taalstudio", robots: { index: false } };

/** The interface copy in three languages, for the Persian review (O2). Not served in production. */
export default function CopyReviewPage() {
  if (!isDevRoute(process.env.APP_ENV)) notFound();
  return <CopyReview />;
}
