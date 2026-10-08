"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { usePrefersReducedMotion } from "@/lib/client/motion";

interface Props {
  open: boolean;
  /** Called when the person closes the dialog (Escape, the close button, the backdrop). */
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
  const titleId = useId();
  const descriptionId = useId();
  const reducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    if (open && !element.open) element.showModal();
    else if (!open && element.open) element.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      className={`dialog ${size}`}
      aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === ref.current) onClose();
      }}
    >
      <div className="dialog-panel" data-anim={open && !reducedMotion ? "pop" : undefined}>
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
