"""
AeroSentinel Notifier
Sends draft previews to Telegram with inline Publish/Edit/Discard buttons.
Uses filename_base (without lang suffix) for callback data.
"""

import json
import requests

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_MAX_LENGTH = 4096


def _split_message(text: str, max_length: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    """Split a message into chunks that fit Telegram's character limit."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        # Find a good split point (newline, then space)
        split_at = text.rfind('\n', 0, max_length)
        if split_at == -1 or split_at < max_length // 2:
            split_at = text.rfind(' ', 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    return chunks


def _html_escape(text: str) -> str:
    """Escape HTML special characters in text for Telegram HTML mode."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def send_draft_preview(
    filename_base: str,
    gemini_output: dict,
    paper: dict,
    post_content: str
):
    """
    Send a formatted preview to Telegram with inline keyboard buttons.
    Uses filename_base (no lang suffix) in callback_data.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    # Build the preview message
    title_display = _html_escape(gemini_output.get('title', 'Untitled'))
    paper_title = _html_escape(gemini_output.get('paper_title', ''))
    summary = _html_escape(gemini_output.get('summary', ''))

    # Badge
    from src.brain import PAPER_TYPE_BADGES
    ptype = gemini_output.get('paper_type', 'numerical_cfd')
    badge = PAPER_TYPE_BADGES.get(ptype, f"📄 {ptype}")
    score = gemini_output.get('relevance_score', 0)

    # Source journal
    journal = _html_escape(paper.get('journal', 'Unknown'))

    tags_str = ", ".join(gemini_output.get("tags", [])[:5])

    message = f"""🛰️ <b>AeroSentinel v2.5 — New Paper Review</b>

📋 <b>{title_display}</b>
📄 {paper_title}
{badge} | Relevance: {score}/100

📝 {summary[:300]}{'...' if len(summary) > 300 else ''}

📰 Source: {journal}
🏷️ Tags: {tags_str}
🌐 Languages: EN + TR
"""

    # Truncate preview if exceeding Telegram limit (leave room for buttons)
    if len(message) > TELEGRAM_MAX_LENGTH - 100:
        message = message[:TELEGRAM_MAX_LENGTH - 150] + "\n\n<i>[Preview truncated]</i>"

    # Inline keyboard with 3 buttons
    # Telegram limits callback_data to 64 bytes, so truncate filename_base
    short_name = filename_base[:50]
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Publish", "callback_data": f"PUB_{short_name}"},
                {"text": "✏️ Edit", "callback_data": f"EDT_{short_name}"},
                {"text": "🗑️ Discard", "callback_data": f"DEL_{short_name}"},
            ],
            [
                {"text": "⭐ Bookmark", "callback_data": f"BKM_{short_name}"},
            ]
        ]
    }

    # Send via Telegram Bot API
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(keyboard),
    }

    print(f"\n📱 [Telegram] Sending preview to chat {TELEGRAM_CHAT_ID}...")

    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            print("   ✅ Preview sent successfully!")
            return True
        else:
            print(f"   ⚠️ Telegram error: HTTP {r.status_code}")
            print(f"   Response: {r.text[:300]}")
            return False
    except Exception as e:
        print(f"   ⚠️ Failed to send: {e}")
        return False


def send_simple_message(text: str):
    """Send a plain text message to Telegram (for status updates)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for chunk in _split_message(text):
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "HTML",
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception:
            pass


def send_published_confirmation(filename_base: str, site_url: str):
    """Send confirmation after publishing with links to both languages."""
    message = f"""✅ <b>Published!</b>

🔗 EN: <a href="{site_url}">{filename_base}</a>
🔗 TR: <a href="{site_url}tr/">{filename_base} (Turkish)</a>"""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass


if __name__ == "__main__":
    # Quick test — send a test message
    send_simple_message("🧪 AeroSentinel v2 Telegram bot is connected!")
    print("Test message sent. Check your Telegram.")
