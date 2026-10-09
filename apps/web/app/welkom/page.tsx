import type { Metadata } from "next";

import { WelcomeFlow } from "@/components/welcome/WelcomeFlow";

export const metadata: Metadata = { title: "Welkom" };

/** The first visit; `?stap=uitleg` opens only the explanation, for learners who come back to it. */
export default async function WelcomePage({ searchParams }: { searchParams: Promise<{ stap?: string }> }) {
  const { stap } = await searchParams;
  return <WelcomeFlow explainOnly={stap === "uitleg"} />;
}
