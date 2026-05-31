import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { LoginPage } from "./LoginPage";
import { renderWithQueryClient } from "../test/renderWithQueryClient";

const loginSpy = vi.fn();

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    login: loginSpy,
    logout: vi.fn(),
  }),
}));

describe("LoginPage", () => {
  it("submits credentials", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email"), "broker@example.com");
    await user.type(screen.getByLabelText("Password"), "secret-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith("broker@example.com", "secret-password");
    });
  });
});
