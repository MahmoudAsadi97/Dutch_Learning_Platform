"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Skeleton, SkeletonPanel } from "@/components/ui/Skeleton";
import { needsWelcome } from "@/lib/client/first-run";
import { useProfile } from "@/lib/client/profile";

/**
 * Sends a learner who has not finished the welcome to /welkom before any learning page renders. The
 * profile usually arrives with the server render, so the redirect happens before anything flashes. When
 * the profile cannot be loaded the gate stays open: the page renders as it always did.
 */
export function FirstRunGate({ enabled, children }: { enabled: boolean; children: ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const profile = useProfile();
  const onboardedAt = profile.isError ? undefined : profile.data?.profile.onboarded_at;
  const redirect = needsWelcome(path, onboardedAt, enabled);
  useEffect(() => {
    if (redirect) router.replace("/welkom");
  }, [redirect, router]);
  if (redirect) {
    return (
      <SkeletonPanel label="Je eerste stappen klaarzetten…">
        <Skeleton lines={3} />
      </SkeletonPanel>
    );
  }
  return <>{children}</>;
}
