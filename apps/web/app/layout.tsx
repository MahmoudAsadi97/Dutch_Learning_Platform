import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { LanguageProvider } from "@/components/LanguageSupport";
import { AppShell } from "@/components/shell/AppShell";
import { prefetchMe } from "@/lib/server/me";
import { Providers } from "./providers";

import "@fontsource-variable/dm-sans";
import "@fontsource-variable/vazirmatn";

import "./styles/layers.css";
import "./styles/tokens.css";
import "./styles/reset.css";
import "./styles/base.css";
import "./styles/ui/button.css";
import "./styles/ui/card.css";
import "./styles/ui/badge.css";
import "./styles/ui/notice.css";
import "./styles/ui/icon-tile.css";
import "./styles/ui/field.css";
import "./styles/ui/skeleton.css";
import "./styles/ui/empty-state.css";
import "./styles/ui/dialog.css";
import "./styles/ui/toast.css";
import "./styles/ui/tabs.css";
import "./styles/ui/segmented.css";
import "./styles/ui/stepper.css";
import "./styles/ui/gloss.css";
import "./styles/ui/honesty.css";
import "./styles/ui/progress.css";
import "./styles/ui/illustration.css";
import "./styles/ui/answer-option.css";
import "./styles/shell.css";
import "./styles/features/gallery.css";
import "./styles/features/preferences.css";
import "./styles/features/welcome.css";
import "./styles/features/about.css";
import "./styles/features/speak.css";
import "./styles/features/exercise.css";
import "./styles/features/alignment.css";
import "./styles/motion.css";
import "./globals.css";
import "./design.css";
import "./learning.css";
import "./learning-tools.css";
import "./library.css";
import "./phrase-audio.css";
import "./topics.css";
import "./learning-agents.css";
import "./stories.css";
import "./study.css";

export const metadata: Metadata = {
  title: {
    default: "Taalstudio · Jouw Nederlands, elke dag",
    template: "%s · Taalstudio",
  },
  description:
    "Een persoonlijke leeromgeving voor Nederlands in België. Lees, luister, spreek en schrijf in situaties uit het echte leven.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

// Environment labels must reflect the running container, not the image builder's environment.
export const dynamic = "force-dynamic";

/**
 * The first-run redirect to /welkom ships behind a switch: on by default outside production, and in
 * production only once FIRST_RUN_GATE=on, so the owner can look at the flow live before turning it on.
 */
function firstRunGateEnabled(): boolean {
  const flag = process.env.FIRST_RUN_GATE;
  if (flag === "on") return true;
  if (flag === "off") return false;
  return (process.env.APP_ENV ?? "development") !== "production";
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const me = await prefetchMe();
  return (
    <html lang="nl">
      <body>
        <a className="skip-link" href="#main">
          Naar de inhoud
        </a>
        <Providers initialMe={me}>
          <LanguageProvider>
            <AppShell environment={process.env.APP_ENV ?? "development"} firstRunGate={firstRunGateEnabled()}>
              {children}
            </AppShell>
          </LanguageProvider>
        </Providers>
      </body>
    </html>
  );
}
