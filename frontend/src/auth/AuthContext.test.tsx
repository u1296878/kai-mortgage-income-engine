import { waitFor } from "@testing-library/react";
import { useEffect } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthContext";
import { renderWithQueryClient } from "../test/renderWithQueryClient";

const mocks = vi.hoisted(() => ({
  loginRequestSpy: vi.fn(),
  fetchMeSpy: vi.fn(),
  setApiTokenSpy: vi.fn(),
  setUnauthorizedHandlerSpy: vi.fn(),
  storeTokenSpy: vi.fn(),
  clearStoredTokenSpy: vi.fn(),
  getStoredTokenSpy: vi.fn(() => null),
}));

vi.mock("../api/auth", () => ({
  login: mocks.loginRequestSpy,
  fetchMe: mocks.fetchMeSpy,
}));

vi.mock("../api/client", () => ({
  setApiToken: mocks.setApiTokenSpy,
  setUnauthorizedHandler: mocks.setUnauthorizedHandlerSpy,
}));

vi.mock("./token", () => ({
  storeToken: mocks.storeTokenSpy,
  clearStoredToken: mocks.clearStoredTokenSpy,
  getStoredToken: mocks.getStoredTokenSpy,
}));

function LoginRunner({ email, password }: { email: string; password: string }): JSX.Element {
  const { login } = useAuth();

  useEffect(() => {
    void login(email, password).catch(() => null);
  }, [login, email, password]);

  return <></>;
}

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("clears auth state when fetchMe fails after login token issuance", async () => {
    mocks.loginRequestSpy.mockResolvedValue({ access_token: "token-123", token_type: "bearer" });
    mocks.fetchMeSpy.mockRejectedValue(new Error("me failed"));

    renderWithQueryClient(
      <AuthProvider>
        <LoginRunner email="broker@example.com" password="secret-password" />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(mocks.setApiTokenSpy).toHaveBeenCalledWith("token-123");
    });
    expect(mocks.clearStoredTokenSpy).toHaveBeenCalled();
    expect(mocks.setApiTokenSpy).toHaveBeenCalledWith(null);
    expect(mocks.storeTokenSpy).not.toHaveBeenCalled();
  });
});
