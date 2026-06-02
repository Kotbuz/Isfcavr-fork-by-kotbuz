import { useEffect, useState } from "react";
import UUIDLink from "./uuidLink";
import { API_BASE_URL } from "../../../../utils/api";
import { getErrorMessage } from "../../../../utils/errors";

interface BoxData {
  id?: string | number;
  uuid?: string;
  clicks?: string | number;
  date?: string;
  isActive?: "Активна" | "Неактивна" | string;
}

export default function BoxList() {
  const [boxes, setBoxes] = useState<BoxData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBoxes = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        setError("Токен авторизации не найден");
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/auth/my-boxes`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "Не удалось загрузить UUID-ссылки"
          );
        }

        const data = await response.json();
        setBoxes(data.boxes || []);
      } catch (err: unknown) {
        console.error("Ошибка при получении боксов:", err);
        setError(getErrorMessage(err, "Ошибка соединения с сервером"));
      } finally {
        setIsLoading(false);
      }
    };

    fetchBoxes();
  }, []);

  if (isLoading) {
    return <div className="text-white text-sm p-4">Загрузка ссылок...</div>;
  }

  if (error) {
    return <div className="text-t-red text-sm p-4">{error}</div>;
  }

  if (boxes.length === 0) {
    return (
      <div className="text-t-muted text-sm p-4">
        У вас еще нет созданных UUID-ссылок
      </div>
    );
  }

  return (
    <div className="overflow-y-auto flex-1 pr-1 custom-scroll">
      {boxes.map((box, index) => {
        const clicksCount =
          box.clicks !== undefined ? box.clicks.toString() : "0";
        const boxUUID = box.uuid || `ID-${box.id}` || "Неизвестный UUID";
        const creationDate = box.date || "24.05.2026";
        const status = box.isActive || "Активна";

        return (
          <UUIDLink
            key={box.id || index}
            clicks={clicksCount}
            UUID={boxUUID}
            date={creationDate}
            isActive={status}
          />
        );
      })}
    </div>
  );
}
