import re
from html import unescape

BAD_WORDS = ["badword", "spam", "viagra", "casino", "click here"]
SPAM_PATTERNS = [r"free money", r"click here", r"visit .*\.com", r"buy now"]


def moderate_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text is required")

    text = unescape(text).strip()
    if len(text) > 500:
        raise ValueError("Text is too long")

    text = re.sub(r"https?://\S+|www\.\S+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s{2,}", " ", text)

    lowered = text.lower()
    if any(word in lowered for word in BAD_WORDS):
        raise ValueError("Bad word detected")

    spam_hits = sum(bool(re.search(pattern, lowered)) for pattern in SPAM_PATTERNS)
    if spam_hits > 1:
        raise ValueError("Spam-like content")

    if len(re.findall(r"[!?.]", text)) > 10 and len(text) < 40:
        raise ValueError("Spam-like content")

    return text
