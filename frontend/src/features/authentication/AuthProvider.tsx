import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { BASE_URL } from "../../services/apiBase";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  mustChangePassword: boolean;
  login: (mustChangePassword?: boolean) => void;
  logout: () => void;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [mustChangePassword, setMustChangePassword] = useState(false);

  async function refreshAuth() {
    setIsLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/user`, {
        method: "GET",
        credentials: "include",
      });

      if (!res.ok) {
        setIsAuthenticated(false);
        setMustChangePassword(false);
        return;
      }

      const user = await res.json();
      setIsAuthenticated(true);
      setMustChangePassword(Boolean(user?.must_change_password));
    } catch {
      setIsAuthenticated(false);
      setMustChangePassword(false);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(function () {
    refreshAuth();
  }, []);

  function login(shouldChangePassword = false) {
    setIsAuthenticated(true);
    setMustChangePassword(shouldChangePassword);
  }

  function logout() {
    setIsAuthenticated(false);
    setMustChangePassword(false);
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        mustChangePassword,
        login,
        logout,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined)
    throw new Error("AuthContext was used outside of AuthProvider");
  return context;
}

export { AuthProvider, useAuth };
