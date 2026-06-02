from aiogram.fsm.state import State, StatesGroup


class SenderStates(StatesGroup):
    awaiting_box_uuid = State()
    awaiting_feedback_text = State()


class OwnerStates(StatesGroup):
    awaiting_box_uuid = State()
    awaiting_owner_token = State()
    awaiting_reply_feedback_id = State()
    awaiting_reply_text = State()
