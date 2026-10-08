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
  duration: number;
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

/** Mounted once in the shell; toasts stack in a live region so screen readers announce them. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const counter = useRef(0);
  const timers = useRef(new Map<number, ReturnType<typeof setTimeout>>());
  const reducedMotion = usePrefersReducedMotion();

  const dismiss = useCallback((id: number) => {
    const timer = timers.current.get(id);
    if (timer) clearTimeout(timer);
    timers.current.delete(id);
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback<ToastApi["notify"]>(
    (message, options = {}) => {
      const id = ++counter.current;
      const duration = options.duration ?? 5000;
      setItems((current) => [
        ...current.slice(-2),
        { id, message, tone: options.tone ?? "neutral", duration },
      ]);
      if (duration > 0)
        timers.current.set(
          id,
          setTimeout(() => dismiss(id), duration),
        );
      return () => dismiss(id);
    },
    [dismiss],
  );

  useEffect(() => {
    const active = timers.current;
    return () => {
      for (const timer of active.values()) clearTimeout(timer);
      active.clear();
    };
  }, []);

  const api = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toast-region" role="status" aria-live="polite" aria-atomic="false">
        {items.map((item) => {
          const glyph = icons[item.tone];
          return (
            <div
              key={item.id}
              className={["toast", item.tone === "neutral" ? "" : item.tone].filter(Boolean).join(" ")}
              data-anim={reducedMotion ? undefined : "rise"}
            >
              {glyph && <Icon name={glyph} size={18} />}
              <div className="toast-body">{item.message}</div>
              <button
                type="button"
                className="toast-close"
                aria-label="Sluiten"
                onClick={() => dismiss(item.id)}
              >
                <Icon name="close" size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
