import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { PropsWithChildren } from "react";
import { fetchMe, login as loginRequest } from "../api/auth";
import { setApiToken, setUnauthorizedHandler } from "../api/client";
import { clearStoredToken, getStoredToken, storeToken } from "./token";
import type { UserRead } from "../types/api";

interface AuthContextValue {
  user: UserRead | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren): JSX.Element {
  const [user, setUser] = useState<UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    clearStoredToken();
    setApiToken(null);
    setUser(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const token = await loginRequest({ email, password });
    storeToken(token.access_token);
    setApiToken(token.access_token);
    const me = await fetchMe();
    setUser(me);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  useEffect(() => {
    const bootstrap = async (): Promise<void> => {
      const token = getStoredToken();
      if (!token) {
        setLoading(false);
        return;
      }

      setApiToken(token);
      try {
        const me = await fetchMe();
        setUser(me);
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    };

    void bootstrap();
  }, [logout]);

  const value = useMemo(
    () => ({ user, loading, login, logout }),
    [user, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
