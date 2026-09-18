import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { me, login as loginApi } from "../api/auth";
import { clearSession, getStoredUser, getToken, setSession } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser);
  const [ready, setReady] = useState(!getToken());

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setReady(true);
      return;
    }
    me()
      .then((res) => {
        setUser(res.data);
        setSession(token, res.data);
      })
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setReady(true));
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await loginApi(email, password);
    setSession(res.data.access_token, res.data.user);
    setUser(res.data.user);
    return res.data.user;
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, role: user?.role, ready, login, logout }),
    [user, ready, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
