"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useRef, type MouseEvent, type ReactNode } from "react";

import { ConnectionBanner } from "@/components/ConnectionBanner";
import { Icon } from "@/components/Icon";
import { LanguageSwitcher } from "@/components/LanguageSupport";
import { destinations, navItemFor, navSection, rooms, type NavItem } from "@/components/shell/nav";
import { IconTile } from "@/components/ui/IconTile";
import { ToastProvider } from "@/components/ui/Toast";
import { NavigationGuardContext, type LeaveGuard } from "@/lib/client/navigation";

function NavLink({ item, section }: { item: NavItem; section: string | null }) {
  return (
    <Link
      href={item.href}
      className="nav-link"
      data-accent={item.accent}
      aria-current={section === item.href ? "page" : undefined}
    >
      <IconTile name={item.icon} size="small" accent={item.accent} iconSize={19} />
      <span>{item.label}</span>
    </Link>
  );
}

function Sidebar({ section }: { section: string | null }) {
  return (
    <aside className="app-sidebar">
      <Link href="/" className="brand" aria-label="Taalstudio, naar vandaag">
        <span className="brand-mark">
          t<span>.</span>
        </span>
        <span>
          taalstudio
          <span className="brand-caption">Nederlands voor het echte leven</span>
        </span>
      </Link>
      <nav aria-label="Hoofdmenu">
        <div className="nav-group">
          {destinations.map((item) => (
            <NavLink key={item.href} item={item} section={section} />
          ))}
        </div>
        <div className="nav-group">
          <p className="nav-group-label">Jouw plek</p>
          {rooms.map((item) => (
            <NavLink key={item.href} item={item} section={section} />
          ))}
        </div>
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
  );
}

function Header({ current }: { current: NavItem }) {
  return (
    <header className="workspace-header">
      <Link href="/" className="mobile-brand" aria-label="Taalstudio, startpagina">
        <span className="brand-mark">
          t<span>.</span>
        </span>
        <span className="mobile-brand-word">taalstudio</span>
      </Link>
      <div className="header-title" aria-hidden="true">
        <IconTile name={current.icon} size="small" accent={current.accent} iconSize={18} />
        <span>{current.label}</span>
      </div>
      <div className="header-actions">
        <LanguageSwitcher />
        <Link href="/settings" className="profile-button" aria-label="Mijn account en instellingen">
          <Icon name="user" size={20} />
        </Link>
      </div>
    </header>
  );
}

function MobileTabs({ section }: { section: string | null }) {
  return (
    <nav className="mobile-nav" aria-label="Mobiel hoofdmenu">
      {destinations.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          data-accent={item.accent}
          aria-current={section === item.href ? "page" : undefined}
        >
          <Icon name={item.icon} size={22} />
          <span>{item.short}</span>
        </Link>
      ))}
    </nav>
  );
}

/**
 * The frame around every screen: sidebar, header, main, footer and the bottom tabs. Every navigation
 * element is a link inside `.app-frame`, where the click capture below lets a screen with unsaved work
 * (a writing draft) finish saving before the route changes.
 */
export function AppShell({ children, environment }: { children: ReactNode; environment: string }) {
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
      event.target instanceof Element ? event.target.closest<HTMLAnchorElement>("a[href]") : null;
    if (!anchor || anchor.download || anchor.target === "_blank") return;
    const target = new URL(anchor.href, window.location.href);
    if (target.origin !== window.location.origin || target.pathname === path) return;
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
  const section = navSection(path);
  const current = navItemFor(path);
  return (
    <NavigationGuardContext.Provider value={registerGuard}>
      <div className="app-frame" onClickCapture={navigate}>
        <ToastProvider>
          <Sidebar section={section} />
          <div className="app-workspace" data-accent={current.accent}>
            <Header current={current} />
            <ConnectionBanner />
            <main id="main" className="site-main" tabIndex={-1}>
              {children}
            </main>
            <footer className="site-footer">
              <span>
                taalstudio <span className="footer-dot">·</span> Nederlands, stap voor stap.
              </span>
              <span>
                {environment === "production" ? "Persoonlijke leeromgeving" : "Lokale leeromgeving"}{" "}
                <span className="footer-dot">·</span> Standaardnederlands in België
              </span>
            </footer>
          </div>
          <MobileTabs section={section} />
        </ToastProvider>
      </div>
    </NavigationGuardContext.Provider>
  );
}
