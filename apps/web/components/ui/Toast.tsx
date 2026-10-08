"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { Icon, type IconName } from "@/components/Icon";
import { usePrefersReducedMotion } from "@/lib/client/motion";

export type ToastTone = "neutral" | "success" | "warning" | "danger";

interface ToastItem {
  id: number;
  message: ReactNode;
  tone: ToastTone;
}

interface Timer {
  handle: ReturnType<typeof setTimeout> | null;
  /** Milliseconds left when paused; the deadline while running. */
  remaining: number;
  startedAt: number;
}

interface ToastApi {
  /** Shows a short message; returns a function that dismisses it early. */
  notify: (message: ReactNode, options?: { tone?: ToastTone; duration?: number }) => () => void;
}

const ToastContext = createContext<ToastApi>({ notify: () => () => undefined });

const icons: Record<ToastTone, IconName | null> = {
  neutral: null,
  success: "check",
  warning: "alert",
  danger: "alert",
};

export function useToast(): ToastApi {
  return useContext(ToastContext);
}

/**
 * Mounted once in the shell. The visible stack holds the messages and their close buttons; two visually
 * hidden live regions carry only the text of the latest message, so a screen reader hears the message
 * once and not the button. Timers pause while the stack is hovered or holds focus.
 *
 * While a modal dialog is open the page behind it, this stack included, is inert: report the outcome of
 * an action inside the dialog itself and notify after it closes.
 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const [latest, setLatest] = useState<ToastItem | null>(null);
  const counter = useRef(0);
  const timers = useRef(new Map<number, Timer>());
  const paused = useRef(false);
  const stack = useRef<HTMLDivElement>(null);
  const reducedMotion = usePrefersReducedMotion();

  const dismiss = useCallback((id: number) => {
    const timer = timers.current.get(id);
    if (timer?.handle) clearTimeout(timer.handle);
    timers.current.delete(id);
    const element = stack.current?.querySelector(`[data-toast="${id}"]`);
    if (element && element.contains(document.activeElement)) {
      // the close button had focus; send it to the content instead of letting it fall to <body>
      document.getElementById("main")?.focus();
    }
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  const run = useCallback(
    (id: number, timer: Timer) => {
      timer.startedAt = Date.now();
      timer.handle = setTimeout(() => dismiss(id), timer.remaining);
    },
    [dismiss],
  );

  const notify = useCallback<ToastApi["notify"]>(
    (message, options = {}) => {
      const id = ++counter.current;
      const duration = options.duration ?? 5000;
      const item = { id, message, tone: options.tone ?? "neutral" };
      setItems((current) => {
        for (const old of current.slice(0, -2)) {
          const timer = timers.current.get(old.id);
          if (timer?.handle) clearTimeout(timer.handle);
          timers.current.delete(old.id);
        }
        return [...current.slice(-2), item];
      });
      setLatest(item);
      if (duration > 0) {
        const timer: Timer = { handle: null, remaining: duration, startedAt: 0 };
        timers.current.set(id, timer);
        if (!paused.current) run(id, timer);
      }
      return () => dismiss(id);
    },
    [dismiss, run],
  );

  const pause = useCallback(() => {
    if (paused.current) return;
    paused.current = true;
    for (const timer of timers.current.values()) {
      if (!timer.handle) continue;
      clearTimeout(timer.handle);
      timer.handle = null;
      timer.remaining = Math.max(0, timer.remaining - (Date.now() - timer.startedAt));
    }
  }, []);

  const resume = useCallback(() => {
    const region = stack.current;
    if (!paused.current) return;
    if (region && (region.matches(":hover") || region.contains(document.activeElement))) return;
    paused.current = false;
    for (const [id, timer] of timers.current) if (!timer.handle) run(id, timer);
  }, [run]);

  useEffect(() => {
    const active = timers.current;
    return () => {
      for (const timer of active.values()) if (timer.handle) clearTimeout(timer.handle);
      active.clear();
    };
  }, []);

  const api = useMemo(() => ({ notify }), [notify]);
  const urgent = latest?.tone === "danger";

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        ref={stack}
        className="toast-region"
        onPointerEnter={pause}
        onPointerLeave={resume}
        onFocus={pause}
        onBlur={() => requestAnimationFrame(resume)}
      >
        {items.map((item) => {
          const glyph = icons[item.tone];
          return (
            <div
              key={item.id}
              data-toast={item.id}
              className={["toast", item.tone === "neutral" ? "" : item.tone].filter(Boolean).join(" ")}
              data-anim={reducedMotion ? undefined : "rise"}
            >
              {glyph && <Icon name={glyph} size={18} />}
              <div className="toast-body">{item.message}</div>
              <button
                type="button"
                className="toast-close"
                aria-label="Melding sluiten"
                onClick={() => dismiss(item.id)}
              >
                <Icon name="close" size={16} />
              </button>
            </div>
          );
        })}
      </div>
      <div className="visually-hidden" role="status" aria-live="polite" aria-atomic="true">
        {latest && !urgent && <span key={latest.id}>{latest.message}</span>}
      </div>
      <div className="visually-hidden" role="alert" aria-atomic="true">
        {latest && urgent && <span key={latest.id}>{latest.message}</span>}
      </div>
    </ToastContext.Provider>
  );
}
