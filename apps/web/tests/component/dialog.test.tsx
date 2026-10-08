import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { beforeAll, describe, expect, it, vi } from "vitest";

import { Dialog } from "@/components/ui/Dialog";

/**
 * The dialog is controlled: it reports a request to close exactly once and never calls back for a close
 * the parent started. jsdom has no modal dialog, so showModal and close are stubbed the way browsers act.
 */
beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    if (!this.hasAttribute("open")) return;
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
  window.matchMedia ??= ((query: string) => ({
    matches: false,
    media: query,
    addEventListener() {},
    removeEventListener() {},
  })) as unknown as typeof window.matchMedia;
});

function Harness({ onClose }: { onClose: () => void }) {
  const [open, setOpen] = useState(true);
  return (
    <Dialog
      open={open}
      title="Titel"
      onClose={() => {
        onClose();
        setOpen(false);
      }}
      actions={
        <button type="button" onClick={() => setOpen(false)}>
          Klaar
        </button>
      }
    >
      <p>Inhoud</p>
    </Dialog>
  );
}

function dialog() {
  return document.querySelector("dialog") as HTMLDialogElement;
}

describe("Dialog", () => {
  it("reports the close button once", () => {
    const onClose = vi.fn();
    render(<Harness onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Sluiten", hidden: true }));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(dialog().hasAttribute("open")).toBe(false);
  });

  it("reports Escape once and lets the parent close it", () => {
    const onClose = vi.fn();
    render(<Harness onClose={onClose} />);
    const cancel = new Event("cancel", { cancelable: true });
    fireEvent(dialog(), cancel);
    expect(cancel.defaultPrevented).toBe(true);
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(dialog().hasAttribute("open")).toBe(false);
  });

  it("does not call back when the parent closes it", () => {
    const onClose = vi.fn();
    render(<Harness onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: "Klaar", hidden: true }));
    expect(onClose).not.toHaveBeenCalled();
    expect(dialog().hasAttribute("open")).toBe(false);
  });

  it("reports a close the browser forces while the dialog is still open", () => {
    const onClose = vi.fn();
    render(<Harness onClose={onClose} />);
    dialog().close();
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes on a press that starts and ends on the backdrop, not on a drag out of the panel", () => {
    const onClose = vi.fn();
    render(<Harness onClose={onClose} />);
    const text = screen.getByText("Inhoud");
    fireEvent.pointerDown(text, { clientX: 500, clientY: 500 });
    fireEvent.click(dialog(), { clientX: 500, clientY: 500 });
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.pointerDown(dialog(), { clientX: 500, clientY: 500 });
    fireEvent.click(dialog(), { clientX: 500, clientY: 500 });
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
