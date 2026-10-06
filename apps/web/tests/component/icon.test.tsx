import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Icon } from "@/components/Icon";

describe("Icon", () => {
  it("renders a decorative svg for a known name", () => {
    const { container } = render(<Icon name="home" />);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg).toHaveAttribute("aria-hidden", "true");
  });
});
