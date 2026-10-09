"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Skeleton, SkeletonPanel } from "@/components/ui/Skeleton";
import { gateFor } from "@/lib/client/first-run";
import { useProfile } from "@/lib/client/profile";
import { uiCopy } from "@/lib/ui-copy";

/**
 * Sends a learner who has not finished the welcome to /welkom before any learning page renders. The
 * profile usually arrives with the server render, so the redirect happens before anything flashes. While it
 * is still loading the page waits; when it cannot be loaded the gate opens and the page renders as before.
 */
export function FirstRunGate({ enabled, children }: { enabled: boolean; children: ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const profile = useProfile();
  const onboardedAt = profile.isError ? undefined : profile.data?.profile.onboarded_at;
  const gate = gateFor(path, onboardedAt, enabled, profile.isPending);
  useEffect(() => {
    if (gate === "welcome") router.replace("/welkom");
  }, [gate, router]);
  if (gate !== "open") {
    return (
      <SkeletonPanel label={uiCopy.state.loading.nl}>
        <Skeleton lines={3} />
      </SkeletonPanel>
    );
  }
  return <>{children}</>;
}
