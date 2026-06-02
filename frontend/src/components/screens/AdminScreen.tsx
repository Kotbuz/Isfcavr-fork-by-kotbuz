import AdminPanel from "../medium/admin/AdminStats";
import AuthCard from "../medium/admin/AdminAuth";

interface User {
  username: string;
  token?: string;
}

interface AdminScreenProps {
  user: User | null;
  screen?: string;
  setScreen: (value: "main" | "sender" | "recipient") => void;
  setAuthToken: (value: string | null) => void;
}

export default function AdminScreen({
  user,
  screen,
  setScreen,
  setAuthToken,
}: AdminScreenProps) {
  return (
    <>
      {user != null ? (
        <AdminPanel setAuthToken={setAuthToken} setScreen={setScreen} />
      ) : (
        <AuthCard
          screen={screen}
          setScreen={setScreen}
          setAuthToken={setAuthToken}
        />
      )}
    </>
  );
}
