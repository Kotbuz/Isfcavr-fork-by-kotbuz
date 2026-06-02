import { useState } from "react";
import Button from "../../../small/button/button";
import Card from "../../../small/card/card";
import Input from "../../../small/input/input";

interface Props {
  setUUID: (value: string | null) => void;
  className?: string;
  screen: string;
  setScreen: (value: "main" | "sender" | "recipient") => void;
  UUIDCODE: string | null;
}

export default function UserCode({
  className = "",
  setUUID,
  setScreen,
}: Props) {
  const [UUID, setUuid] = useState<string>("");
  return (
    <Card className={`${className}`}>
      <div className="flex flex-row justify-between">
        <div>
          <h1 className="mb-1 leading-relaxed">Код доступа получателя</h1>
          <p className="text-t-muted mb-3">
            Введите уникальный UUID получателя, чтобы отправить отзыв
          </p>
        </div>
        <button
          onClick={() => {
            setUUID(null);
            setScreen("main");
          }}
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
      </div>
      <Input
        autoComplete="off"
        type="text"
        className="mb-3"
        placeholder="Введите UUID-код"
        w="full"
        value={UUID}
        onChange={setUuid}
      />
      <Button
        className="mb-3"
        text="Продолжить"
        w="full"
        onClick={() => {
          setUUID(UUID);
        }}
      />
      <p className="text-t-muted text-xs mb-2">
        UUID обеспечивает доставку только нужному получателю
      </p>
    </Card>
  );
}
