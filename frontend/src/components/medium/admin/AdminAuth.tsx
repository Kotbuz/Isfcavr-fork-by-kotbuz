import { useState } from "react";
import Button from "../../small/button/button";
import Card from "../../small/card/card";
import Input from "../../small/input/input";
import { useAuthStore } from "../../../utils/useAuthStore";
import { API_BASE_URL } from "../../../utils/api";
import {
  getErrorMessage,
  type ValidationErrorItem,
} from "../../../utils/errors";

interface AuthCardProps {
  setAuthToken: (value: string | null) => void;
  screen?: string;
  setScreen: (value: "main" | "sender" | "recipient") => void;
  isAuth?: boolean; // Добавили знак ?, теперь они не ломают сборку
  setIsAuth?: (value: boolean) => void; // Добавили знак ?
}

interface CardProps {
  setIsLogin: (value: boolean) => void;
  setAuthToken: (value: string | null) => void; // Передаем её строго в подкомпоненты
  screen?: string;
  setScreen: (value: "main" | "sender" | "recipient") => void;
}

const isElectron =
  typeof window !== "undefined" &&
  navigator.userAgent.toLowerCase().includes("electron");

const translateError = (msg: string): string => {
  const lower = msg.toLowerCase();
  if (lower.includes("field required")) return "Field is required";
  if (lower.includes("already exists"))
    return "User with this username already exists";
  if (lower.includes("value is not a valid")) return "Invalid value entered";
  if (lower.includes("ensure this value has at least")) {
    const match = lower.match(/\d+/);
    return `Password is too short (minimum ${match ? match : 6} characters)`;
  }
  if (lower.includes("passwords do not match") || lower.includes("match"))
    return "Passwords do not match";
  return msg;
};

const registerFunc = async (
  username: string,
  password: string,
  confirm_password: string
) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password, confirm_password }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      if (Array.isArray(errorData.detail)) {
        const textError = errorData.detail
          .map((err: ValidationErrorItem) => translateError(err.msg))
          .join(". ");
        throw new Error(textError);
      }
      if (
        errorData.detail === "User already exists" ||
        errorData.detail === "User already registered"
      ) {
        throw new Error("User with this username already exists");
      }
      throw new Error(
        errorData.detail || "An error occurred during registration"
      );
    }
    const data = await response.json();
    const token = data.access_token || data.token;
    if (token) {
      localStorage.setItem("token", token);
      useAuthStore.getState().setAuth(token, { username });
    }
    return data;
  } catch (error: unknown) {
    console.error("Request error:", error);
    throw new Error(
      getErrorMessage(
        error,
        "Failed to connect to the server. Check your connection"
      )
    );
  }
};

const loginFunc = async (username: string, password: string) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      const detailMsg = String(errorData.detail || "").toLowerCase();
      if (
        detailMsg.includes("invalid credentials") ||
        detailMsg.includes("incorrect username") ||
        detailMsg.includes("invalid username")
      ) {
        throw new Error("Incorrect username or password");
      }
      if (Array.isArray(errorData.detail)) {
        const textError = errorData.detail
          .map((err: ValidationErrorItem) => translateError(err.msg))
          .join(". ");
        throw new Error(textError);
      }
      throw new Error(
        errorData.detail || "An error occurred during authorization"
      );
    }
    const data = await response.json();
    const token = data.access_token || data.token;
    if (token) {
      localStorage.setItem("token", token);
      useAuthStore.getState().setAuth(token, { username });
    }
    return data;
  } catch (error: unknown) {
    console.error("Request error:", error);
    throw new Error(
      getErrorMessage(
        error,
        "Failed to connect to the server. Check your connection"
      )
    );
  }
};

const Login = ({ setIsLogin, setAuthToken, setScreen }: CardProps) => {
  const [login, setLogin] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    try {
      setError(null);
      const result = await loginFunc(login, password);
      if (result) {
        // Вытаскиваем токен, который только что записал loginFunc, и передаем в App.tsx
        const savedToken = localStorage.getItem("token");
        setAuthToken(savedToken);
      }
    } catch (errMessage: unknown) {
      setError(getErrorMessage(errMessage));
    }
  };

  return (
    <Card className="w-2xl h-auto flex flex-col gap-4">
      <div className="flex flex-row justify-between">
        <div className="space-y-1">
          <h1 className="text-[19px]">Авторизация получателя</h1>
          <p className="text-sm text-t-muted">Введите логин и пароль</p>
        </div>
        {isElectron ? null : (
          <button
            onClick={() => setScreen("main")}
            className="p-2 max-h-8 flex items-center border border-ui-border rounded-lg text-xs text-t-muted hover:text-white hover:bg-zinc-900 transition-all cursor-pointer select-none"
            title="Вернуться назад"
          >
            <svg
              xmlns="http://w3.org"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m15 18-6-6 6-6" />
            </svg>
            <span>Назад</span>
          </button>
        )}
      </div>
      <Input
        value={login}
        onChange={setLogin}
        w="full"
        placeholder="Введите логин"
      />
      <Input
        type="password"
        value={password}
        onChange={setPassword}
        w="full"
        placeholder="Введите пароль"
      />
      {error && <p className="text-t-red text-xs mt-1">{error}</p>}
      <Button text="Продолжить" w="full" onClick={handleLogin} />
      <p
        className="text-sm text-t-muted text-center cursor-pointer hover:text-t-muted/50"
        onClick={() => setIsLogin(false)}
      >
        Нет аккаунта
      </p>
    </Card>
  );
};

const Registration = ({ setIsLogin, setAuthToken, setScreen }: CardProps) => {
  const [login, setLogin] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [repPassword, setRepPassword] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const handleRegister = async () => {
    try {
      setError(null);
      const result = await registerFunc(login, password, repPassword);
      if (result) {
        const savedToken = localStorage.getItem("token");
        setAuthToken(savedToken);
      }
    } catch (errMessage: unknown) {
      setError(getErrorMessage(errMessage));
    }
  };

  return (
    <Card className="w-2xl h-auto flex flex-col gap-4">
      <div className="flex flex-row justify-between">
        <div className="space-y-1">
          <h1 className="text-[19px]">Регистрация получателя</h1>
          <p className="text-sm text-t-muted">Введите логин и пароль</p>
        </div>
        {isElectron ? null : (
          <button
            onClick={() => setScreen("main")}
            className="p-2 max-h-8 flex items-center border border-ui-border rounded-lg text-xs text-t-muted hover:text-white hover:bg-zinc-900 transition-all cursor-pointer select-none"
            title="Вернуться назад"
          >
            <svg
              xmlns="http://w3.org"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m15 18-6-6 6-6" />
            </svg>
            <span>Назад</span>
          </button>
        )}
      </div>
      <Input
        autoComplete="off"
        value={login}
        onChange={setLogin}
        w="full"
        placeholder="Введите логин"
      />
      <Input
        autoComplete="off"
        type="password"
        value={password}
        onChange={setPassword}
        w="full"
        placeholder="Введите пароль"
      />
      <Input
        autoComplete="off"
        type="password"
        value={repPassword}
        onChange={setRepPassword}
        w="full"
        placeholder="Введите пароль повторно"
      />
      {error && <p className="text-t-red text-xs mt-1">{error}</p>}
      <Button text="Продолжить" w="full" onClick={handleRegister} />
      <p
        className="text-sm text-t-muted text-center cursor-pointer hover:text-t-muted/50"
        onClick={() => setIsLogin(true)}
      >
        Есть аккаунт
      </p>
    </Card>
  );
};

export default function AuthCard({ setAuthToken, setScreen }: AuthCardProps) {
  const [isLogin, setIsLogin] = useState<boolean>(true);
  return (
    <div className="h-screen p-6 flex text-white items-center justify-center">
      {isLogin ? (
        <Login
          setScreen={setScreen}
          setIsLogin={setIsLogin}
          setAuthToken={setAuthToken}
        />
      ) : (
        <Registration
          setScreen={setScreen}
          setIsLogin={setIsLogin}
          setAuthToken={setAuthToken}
        />
      )}
    </div>
  );
}
