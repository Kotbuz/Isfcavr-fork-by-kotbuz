import { useCallback, useEffect, useState } from "react";
import Button from "../../small/button/button";
import { API_BASE_URL } from "../../../utils/api";
import { getErrorMessage } from "../../../utils/errors";

export default function AdminTelegram() {
  const [linked, setLinked] = useState(false);
  const [linkUrl, setLinkUrl] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copyHint, setCopyHint] = useState<string | null>(null);

  const authHeaders = useCallback(() => {
    const token = localStorage.getItem("token");
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }, []);

  const fetchStatus = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE_URL}/auth/telegram/status`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setLinked(Boolean(data.linked));
      }
    } catch (err) {
      console.error("Telegram status error:", err);
    }
  }, [authHeaders]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleLink = async () => {
    setLoading(true);
    setError(null);
    setCopyHint(null);
    try {
      const res = await fetch(`${API_BASE_URL}/auth/telegram/link-token`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.detail || "Не удалось создать ссылку");
      }
      const data = await res.json();
      setLinkUrl(data.link_url);
      setExpiresAt(data.expires_at);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Ошибка при создании ссылки"));
    } finally {
      setLoading(false);
    }
  };

  const handleUnlink = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/auth/telegram/unlink`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      if (!res.ok && res.status !== 204) {
        const body = await res.json();
        throw new Error(body.detail || "Не удалось отвязать");
      }
      setLinked(false);
      setLinkUrl(null);
      setExpiresAt(null);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Ошибка отвязки"));
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!linkUrl) return;
    try {
      await navigator.clipboard.writeText(linkUrl);
      setCopyHint("Ссылка скопирована");
      setTimeout(() => setCopyHint(null), 3000);
    } catch {
      setCopyHint("Не удалось скопировать — выделите ссылку вручную");
    }
  };

  return (
    <div className="w-full flex flex-col gap-2 border-t border-ui-border/40 pt-3 mt-1">
      <p className="text-xs text-t-muted">Уведомления в Telegram</p>
      {linked ? (
        <>
          <p className="text-[11px] text-t-green">Telegram подключён</p>
          <Button
            text={loading ? "..." : "Отвязать Telegram"}
            w="full"
            onClick={handleUnlink}
          />
        </>
      ) : (
        <>
          <Button
            text={loading ? "..." : "Привязать Telegram"}
            w="full"
            onClick={handleLink}
          />
          {linkUrl && (
            <div className="flex flex-col gap-1.5">
              <a
                href={linkUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[11px] text-t-blue break-all hover:underline"
              >
                Открыть в Telegram
              </a>
              <button
                type="button"
                onClick={handleCopy}
                className="text-[11px] text-t-muted hover:text-white text-left"
              >
                Скопировать ссылку
              </button>
              {expiresAt && (
                <p className="text-[10px] text-t-muted">
                  Действует 10 мин. Обновите страницу после привязки.
                </p>
              )}
              {copyHint && (
                <p className="text-[10px] text-t-green">{copyHint}</p>
              )}
            </div>
          )}
        </>
      )}
      {error && <p className="text-[10px] text-t-red">{error}</p>}
    </div>
  );
}
