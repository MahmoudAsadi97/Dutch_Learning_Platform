"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { navSection } from "@/components/shell/nav";

interface Tab {
  href: string;
  label: string;
}

/** Second-level links inside one destination, as plain anchors so the navigation guard sees them. */
export function SectionTabs({ label, tabs }: { label: string; tabs: Tab[] }) {
  const path = usePathname();
  const segment = `/${path.replace(/^\/+/, "").split("/")[0] ?? ""}`;
  return (
    <nav className="section-tabs" aria-label={label}>
      {tabs.map((tab) => (
        <Link key={tab.href} href={tab.href} aria-current={segment === tab.href ? "page" : undefined}>
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}

/** Personal episodes are reached inside the story library. */
export function MediaTabs() {
  return null;
}

/** The two rooms beside the destinations. */
export function AccountTabs() {
  return (
    <SectionTabs
      label="Voortgang en instellingen"
      tabs={[
        { href: "/progress", label: "Voortgang" },
        { href: "/settings", label: "Instellingen" },
      ]}
    />
  );
}

export { navSection };
