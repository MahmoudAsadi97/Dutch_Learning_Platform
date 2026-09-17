import type { Metadata, Viewport } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Nederlands oefenen",
  description: "Dutch learning platform, release 0.1",
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
        <header className="site-header">
          <nav aria-label="Hoofdmenu" className="site-nav">
            <Link href="/" className="brand">
              Nederlands oefenen
            </Link>
            <ul>
              <li>
                <Link href="/missions/appointment-change">Missie</Link>
              </li>
              <li>
                <Link href="/speech-check">Microfoontest</Link>
              </li>
            </ul>
          </nav>
        </header>
        <main id="main" className="site-main">
          {children}
        </main>
        <footer className="site-footer">
          <span>Release 0.1 · Phase A · lokale ontwikkelomgeving</span>
        </footer>
      </body>
    </html>
  );
}
