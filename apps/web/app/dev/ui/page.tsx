import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { UiGallery } from "@/components/dev/UiGallery";
import { isDevRoute } from "@/lib/client/dev-only";

export const metadata: Metadata = { title: "UI-galerij · Taalstudio", robots: { index: false } };

/** Every primitive in every state, for review while building. Not served in production. */
export default function UiGalleryPage() {
  if (!isDevRoute(process.env.APP_ENV)) notFound();
  return <UiGallery />;
}
