import { screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { RequireAuth } from "./RequireAuth";
import { renderWithQueryClient } from "../test/renderWithQueryClient";

vi.mock("./AuthContext", () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

describe("RequireAuth", () => {
  it("redirects unauthenticated users to login", () => {
    renderWithQueryClient(
      <MemoryRouter initialEntries={["/cases"]}>
        <Routes>
          <Route path="/login" element={<div>Login route</div>} />
          <Route element={<RequireAuth />}>
            <Route path="/cases" element={<div>Cases route</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Login route")).toBeInTheDocument();
  });
});
