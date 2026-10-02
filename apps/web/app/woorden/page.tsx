import type { Metadata } from "next";
import { WordReview } from "@/components/WordReview";
export const metadata: Metadata = { title: "Woorden" };
export default function WordsPage() {
  return <WordReview />;
}
