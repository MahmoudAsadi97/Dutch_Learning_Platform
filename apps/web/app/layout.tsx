import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/AppShell";

import "@fontsource-variable/dm-sans";
import "@fontsource-variable/vazirmatn";

import "./globals.css";
import "./design.css";

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

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="nl">
      <body>
        <a className="skip-link" href="#main">
          Naar de inhoud
        </a>
        <AppShell environment={process.env.APP_ENV ?? "development"}>
          {children}
        </AppShell>
      </body>
    </html>
  );
}
