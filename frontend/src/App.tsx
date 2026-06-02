import { useEffect, useState } from "react";
import AdminScreen from "./components/screens/AdminScreen";
import MainScreen from "./components/screens/mainScreen";
import AuthCard from "./components/medium/admin/AdminAuth";
import { API_BASE_URL } from "./utils/api";

interface User {
  username: string;
  token?: string;
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [screen, setScreen] = useState<"main" | "sender" | "recipient">("main");
  const [authToken, setAuthToken] = useState<string | null>(() =>
    localStorage.getItem("token")
  );

  const [UUID, setUUID] = useState<string | null>(() => {
    const queryParams = new URLSearchParams(window.location.search);
    return queryParams.get("uuid") || null;
  });

  const isElectron = (() => {
    if (typeof window === "undefined") {
      return false;
    }
    const process = (window as Window & { process?: { type?: string } })
      .process;
    if (process?.type === "renderer") {
      return true;
    }
    return (
      typeof navigator !== "undefined" &&
      navigator.userAgent.toLowerCase().includes("electron")
    );
  })();

  useEffect(() => {
    const autoLogin = async () => {
      if (authToken === null) {
        setUser(null);
        setIsLoading(false);
        return;
      }
      const storedToken = localStorage.getItem("token");

      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${storedToken}`,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          localStorage.removeItem("token");
          setAuthToken(null);
          setUser(null);
        }
      } catch (error) {
        console.error("Ошибка автологина:", error);
      } finally {
        setIsLoading(false);
      }
    };

    autoLogin();
  }, [authToken]);

  if (isLoading) {
    return <div className="text-white p-6">Загрузка сессии...</div>;
  }
  if (isElectron) {
    if (!authToken) {
      return <AuthCard setAuthToken={setAuthToken} setScreen={setScreen} />;
    }
    return (
      <AdminScreen
        setScreen={setScreen}
        user={user}
        setAuthToken={setAuthToken}
      />
    );
  }
  if (authToken && screen === "recipient") {
    return (
      <AdminScreen
        screen={screen}
        setScreen={setScreen}
        user={user}
        setAuthToken={setAuthToken}
      />
    );
  }
  return (
    <MainScreen
      UUID={UUID}
      screen={screen}
      setScreen={setScreen}
      setUUID={setUUID}
      user={user}
      setAuthToken={setAuthToken}
    />
  );
}
