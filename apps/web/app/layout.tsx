import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { LanguageProvider } from "@/components/LanguageSupport";
import { AppShell } from "@/components/shell/AppShell";
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
import "./styles/shell.css";
import "./styles/features/gallery.css";
import "./styles/features/speak.css";
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
import "./videos.css";

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

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="nl">
      <body>
        <a className="skip-link" href="#main">
          Naar de inhoud
        </a>
        <Providers>
          <LanguageProvider>
            <AppShell environment={process.env.APP_ENV ?? "development"}>{children}</AppShell>
          </LanguageProvider>
        </Providers>
      </body>
    </html>
  );
}
