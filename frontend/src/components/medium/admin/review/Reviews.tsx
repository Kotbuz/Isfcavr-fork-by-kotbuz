import { useEffect, useState } from "react";
import Review from "./review";
import { API_BASE_URL } from "../../../../utils/api";
import { getErrorMessage } from "../../../../utils/errors";

interface FeedbackData {
  id?: string | number;
  text?: string;
  box_uuid?: string;
  created_at?: string;
}

export default function LatestReviewsCard() {
  const [feedbacks, setFeedbacks] = useState<FeedbackData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFeedbacks = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        setError("Токен авторизации не найден");
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/auth/my-feedbacks`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Не удалось загрузить отзывы");
        }

        const data = await response.json();
        // Записываем массив из поля "feedbacks", как показано в Swagger
        setFeedbacks(data.feedbacks || []);
      } catch (err: unknown) {
        console.error("Ошибка при получении отзывов:", err);
        setError(getErrorMessage(err, "Ошибка соединения с сервером"));
      } finally {
        setIsLoading(false);
      }
    };

    fetchFeedbacks();
  }, []);

  return (
    <div className="overflow-y-auto flex-1 pr-1 custom-scroll">
      {isLoading ? (
        <div className="text-t-muted text-sm p-2">Загрузка отзывов...</div>
      ) : error ? (
        <div className="text-t-red text-sm p-2">{error}</div>
      ) : feedbacks.length === 0 ? (
        <div className="text-t-muted text-sm p-2">
          У вас еще нет полученных отзывов
        </div>
      ) : (
        feedbacks.map((item, index) => {
          const reviewText = item.text || "Без текста";
          const targetUUID = item.box_uuid || "Неизвестный UUID";
          const timeLabel = item.created_at || "Недавно";

          return (
            <Review
              key={item.id || index}
              title={reviewText}
              UUID={targetUUID}
              timeAgo={timeLabel}
            />
          );
        })
      )}
    </div>
  );
}
