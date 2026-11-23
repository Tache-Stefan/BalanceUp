import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the BalanceUp heading", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok" }),
      }),
    );

    render(<App />);
    expect(screen.getByRole("heading", { name: "BalanceUp" })).toBeInTheDocument();

    vi.unstubAllGlobals();
  });
});
