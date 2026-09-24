"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useRef, type MouseEvent, type ReactNode } from "react";
import { LanguageSwitcher } from "@/components/LanguageSupport";
import { ConnectionBanner } from "@/components/ConnectionBanner";
import { Icon, type IconName } from "@/components/Icon";
import {
  NavigationGuardContext,
  type LeaveGuard,
} from "@/lib/client/navigation";

const links: { href: string; label: string; short: string; icon: IconName }[] =
  [
    { href: "/", label: "Mijn leerpad", short: "Leerpad", icon: "home" },
    {
      href: "/missions",
      label: "Praktijkgesprekken",
      short: "Oefenen",
      icon: "book",
    },
    {
      href: "/progress",
      label: "Mijn voortgang",
      short: "Voortgang",
      icon: "chart",
    },
    {
      href: "/speech-check",
      label: "Spraakstudio",
      short: "Spraak",
      icon: "mic",
    },
    {
      href: "/settings",
      label: "Instellingen",
      short: "Instellingen",
      icon: "settings",
    },
  ];

export function AppShell({
  children,
  environment,
}: {
  children: ReactNode;
  environment: string;
}) {
  const path = usePathname();
  const router = useRouter();
  const guard = useRef<LeaveGuard>(null);
  const leaving = useRef(false);
  const registerGuard = useCallback((value: LeaveGuard) => {
    guard.current = value;
  }, []);
  function navigate(event: MouseEvent<HTMLDivElement>) {
    if (
      !guard.current ||
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    )
      return;
    const anchor =
      event.target instanceof Element
        ? event.target.closest<HTMLAnchorElement>("a[href]")
        : null;
    if (!anchor || anchor.download || anchor.target === "_blank") return;
    const target = new URL(anchor.href, window.location.href);
    if (target.origin !== window.location.origin || target.pathname === path)
      return;
    event.preventDefault();
    event.stopPropagation();
    if (leaving.current) return;
    leaving.current = true;
    void guard
      .current()
      .then((allowed) => {
        if (allowed) router.push(target.pathname + target.search + target.hash);
      })
      .catch(() => undefined)
      .finally(() => {
        leaving.current = false;
      });
  }
  const current = path.startsWith("/learn/") ? links[0] : links.find((link) => link.href === path) ?? links[1];
  return (
    <NavigationGuardContext.Provider value={registerGuard}>
      <div className="app-frame" onClickCapture={navigate}>
        <aside className="app-sidebar">
          <Link
            href="/"
            className="brand"
            aria-label="Taalstudio, naar mijn leerplek"
          >
            <span className="brand-mark">
              t<span>.</span>
            </span>
            <span>
              taalstudio
              <span className="brand-caption">
                Nederlands voor het echte leven
              </span>
            </span>
          </Link>
          <div className="sidebar-label">JOUW LEEROMGEVING</div>
          <nav aria-label="Hoofdmenu" className="primary-nav">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={(path === link.href || (link.href === "/" && path.startsWith("/learn/")) || (link.href === "/missions" && path.startsWith("/missions/"))) ? "page" : undefined}
              >
                <Icon name={link.icon} />
                <span>{link.label}</span>
                {path === link.href && <span className="nav-dot" />}
              </Link>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="sidebar-locale">
              <span className="belgian-flag" aria-hidden="true" />
              <span>
                Standaardnederlands
                <br />
                <strong>Belgische context</strong>
              </span>
            </div>
          </div>
        </aside>
        <div className="app-workspace">
          <header className="workspace-header">
            <Link
              href="/"
              className="mobile-brand"
              aria-label="Taalstudio, startpagina"
            >
              <span className="brand-mark">
                t<span>.</span>
              </span>
              taalstudio
            </Link>
            <div className="breadcrumb">
              <span>Leeromgeving</span>
              <Icon name="chevron" size={14} />
              <strong>{current.label}</strong>
            </div>
            <div className="header-actions">
              <LanguageSwitcher />
              <Link
                href="/settings"
                className="profile-button"
                aria-label="Mijn account en instellingen"
              >
                <Icon name="user" size={19} />
              </Link>
            </div>
          </header>
          <ConnectionBanner />
          <main id="main" className="site-main" tabIndex={-1}>
            {children}
          </main>
          <footer className="site-footer">
            <span>
              taalstudio <span className="footer-dot">·</span> Nederlands, stap
              voor stap.
            </span>
            <span>
              {environment === "production"
                ? "Persoonlijke leeromgeving"
                : "Lokale leeromgeving"}{" "}
              <span className="footer-dot">·</span> Standaardnederlands in België
            </span>
          </footer>
        </div>
        <nav className="mobile-nav" aria-label="Mobiel hoofdmenu">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              aria-current={(path === link.href || (link.href === "/" && path.startsWith("/learn/")) || (link.href === "/missions" && path.startsWith("/missions/"))) ? "page" : undefined}
            >
              <Icon name={link.icon} size={21} />
              <span>{link.short}</span>
            </Link>
          ))}
        </nav>
      </div>
    </NavigationGuardContext.Provider>
  );
}
