import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { LanguageProvider } from "@/components/LanguageSupport";
import { AppShell } from "@/components/AppShell";

import "@fontsource-variable/dm-sans";
import "@fontsource-variable/vazirmatn";

import "./globals.css";
import "./design.css";
import "./learning.css";
import "./learning-tools.css";
import "./library.css";
import "./phrase-audio.css";
import "./topics.css";
import "./learning-agents.css";

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
        <LanguageProvider>
        <AppShell environment={process.env.APP_ENV ?? "development"}>
          {children}
        </AppShell>
        </LanguageProvider>
      </body>
    </html>
  );
}
