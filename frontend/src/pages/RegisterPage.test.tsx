import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { register } from "../api/auth";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { RegisterPage } from "./RegisterPage";

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("../api/auth", () => ({
  register: vi.fn().mockResolvedValue({
    id: "broker-1",
    email: "broker@example.com",
    role: "broker",
    is_active: true,
    created_at: "2026-06-02T00:00:00Z",
  }),
}));

describe("RegisterPage", () => {
  it("submits broker registration", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email"), "broker@example.com");
    await user.type(screen.getByLabelText("Password"), "secret-password");
    await user.type(screen.getByLabelText("Confirm password"), "secret-password");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(register).toHaveBeenCalledWith({
        email: "broker@example.com",
        password: "secret-password",
      });
    });
  });
});
