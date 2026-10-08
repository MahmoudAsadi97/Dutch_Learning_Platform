"use client";

import { useEffect, useId, useRef, type PointerEvent, type ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { usePrefersReducedMotion } from "@/lib/client/motion";

interface Props {
  open: boolean;
  /**
   * Called once when the person asks to close (Escape, the close button, the backdrop). The dialog stays
   * open until the parent sets `open` to false; closes the parent starts never call back.
   */
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  /** Buttons for the footer; the caller owns their behaviour. */
  actions?: ReactNode;
  /** `sheet` slides up from the bottom on narrow screens. */
  size?: "md" | "lg" | "sheet";
  closeLabel?: string;
}

/**
 * A native modal dialog rendered in place, so the navigation guard still sees any links inside it. The
 * browser traps focus, makes the rest inert and returns focus to the opener on close.
 */
export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  actions,
  size = "md",
  closeLabel = "Sluiten",
}: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const pressedOutside = useRef(false);
  const titleId = useId();
  const descriptionId = useId();
  const reducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    if (open && !element.open) element.showModal();
    else if (!open && element.open) element.close();
  }, [open]);

  function outsidePanel(event: { clientX: number; clientY: number }) {
    const box = panel.current?.getBoundingClientRect();
    if (!box) return false;
    return (
      event.clientX < box.left ||
      event.clientX > box.right ||
      event.clientY < box.top ||
      event.clientY > box.bottom
    );
  }

  return (
    <dialog
      ref={ref}
      className={`dialog ${size}`}
      aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      // the panel scrolls inside the dialog; animating the dialog itself adds no scrollable overflow
      data-anim={open && !reducedMotion ? "pop" : undefined}
      onCancel={(event) => {
        // Escape asks the parent; the browser may still force a close, which onClose below reports
        event.preventDefault();
        onClose();
      }}
      onClose={() => {
        // a close the parent started (open is already false) must not call back
        if (open) onClose();
      }}
      onPointerDown={(event: PointerEvent<HTMLDialogElement>) => {
        pressedOutside.current = event.target === ref.current && outsidePanel(event);
      }}
      onClick={(event) => {
        // only a press that starts and ends on the backdrop closes; a text selection dragged out does not
        if (pressedOutside.current && event.target === ref.current && outsidePanel(event)) onClose();
        pressedOutside.current = false;
      }}
    >
      <div className="dialog-panel" ref={panel}>
        <header className="dialog-header">
          <h2 id={titleId}>{title}</h2>
          <Button variant="ghost" size="small" icon="close" aria-label={closeLabel} onClick={onClose} />
        </header>
        {description && (
          <p className="dialog-description" id={descriptionId}>
            {description}
          </p>
        )}
        <div className="dialog-body">{children}</div>
        {actions && <footer className="dialog-actions">{actions}</footer>}
      </div>
    </dialog>
  );
}
