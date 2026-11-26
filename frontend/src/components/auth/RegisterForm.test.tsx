import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RegisterForm } from "./RegisterForm";

describe("RegisterForm", () => {
  it("shows validation errors for invalid inputs without calling onSubmit", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<RegisterForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Display name"), { target: { value: "A" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "invalid" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "short" } });
    fireEvent.change(screen.getByLabelText("Confirm password"), { target: { value: "mismatch" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByText("Display name must be at least 2 characters."),
    ).toBeInTheDocument();
    expect(screen.getByText("Please enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Password must be at least 8 characters.")).toBeInTheDocument();
    expect(screen.getByText("Passwords do not match.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits trimmed payload without confirmPassword and shows loading state", async () => {
    let resolveSubmit!: () => void;
    const onSubmit = vi.fn().mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          resolveSubmit = resolve;
        }),
    );

    render(<RegisterForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Display name"), { target: { value: "  Maria  " } });
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "  maria@example.com  " },
    });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(onSubmit).toHaveBeenCalledWith({
      display_name: "Maria",
      email: "maria@example.com",
      password: "password123",
    });
    expect(screen.getByRole("button", { name: "Creating account..." })).toBeDisabled();

    resolveSubmit();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Create account" })).toBeEnabled();
    });
  });

  it("renders server error alert when registration fails", async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error("Email already registered"));
    render(<RegisterForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Display name"), { target: { value: "Maria" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "maria@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Email already registered");
  });
});
