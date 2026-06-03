from src.services.telegram_notify_service import format_box_uuid


def test_format_box_uuid_shortens():
    assert format_box_uuid("a1b2c3d4-e5f6-7890-abcd-ef1234567890") == "a1b2…7890"
