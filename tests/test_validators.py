import pytest

from src.utils.validators import moderate_text


def test_moderate_text_removes_links_and_emails():
    text = "hello https://example.com test user@mail.com"
    result = moderate_text(text)
    assert "https://" not in result
    assert "user@mail.com" not in result
    assert "hello" in result


def test_moderate_text_rejects_bad_words():
    with pytest.raises(ValueError):
        moderate_text("This contains badword")


def test_moderate_text_rejects_spam_patterns():
    with pytest.raises(ValueError):
        moderate_text("Click here to get free money now")
