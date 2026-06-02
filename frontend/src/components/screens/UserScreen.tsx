import UserCode from "../medium/user/UserCode/UserCode";
import UserInfo from "../medium/user/UserInfo/UserInfo";
import UserReview from "../medium/user/UserReview/UserReview";

interface UserScreenProps {
  screen: string;
  setScreen: (value: "main" | "sender" | "recipient") => void;
  UUIDCODE: string | null;
  UUID: string | null;
  setUUID: (value: string | null) => void;
}

export default function UserScreen({
  screen,
  setScreen,
  UUIDCODE,
  UUID,
  setUUID,
}: UserScreenProps) {
  return (
    <div className="h-full w-screen flex flex-col items-center p-4 md:p-8 pt-8 pb-4 overflow-y-auto overflow-x-hidden select-none text-white relative">
      <div className="flex-1 w-full flex flex-col justify-center items-center gap-6">
        {!UUID ? (
          <div className="w-full flex flex-col items-center gap-6">
            <div className="w-full max-w-110 transition-all duration-300">
              <UserInfo />
            </div>
            <div className="w-full max-w-160 transition-all duration-300">
              <UserCode
                UUIDCODE={UUIDCODE}
                setScreen={setScreen}
                screen={screen}
                setUUID={setUUID}
              />
            </div>
          </div>
        ) : (
          <div className="w-full max-w-140 transition-all duration-300">
            <UserReview
              setUUID={setUUID}
              UUIDCODE={UUIDCODE}
              onBack={() => {
                setUUID(null);
                setScreen("sender");
              }}
            />
          </div>
        )}
      </div>
      <h5 className="text-xs text-t-muted text-center tracking-wide pointer-events-none mt-2.5 shrink-0">
        We don't share your IP
      </h5>
    </div>
  );
}
