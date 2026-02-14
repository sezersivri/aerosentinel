"""
AeroSentinel Notifier
Sends draft previews to Telegram with inline Publish/Edit/Discard buttons.
"""

import json
import requests

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_draft_preview(
    filename: str,
    gemini_output: dict,
    papers: list,
    post_content: str
):
    """
    Send a formatted preview to Telegram with inline keyboard buttons.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    # Build the preview message
    journal_list = list(set(p["journal"] for p in papers))
    journal_str = ", ".join(journal_list[:4])
    tags_str = ", ".join(gemini_output["tags"][:5])

    message = f"""🛰️ <b>AeroSentinel — New Draft Ready</b>

📋 <b>{gemini_output['title']}</b>

📝 {gemini_output['summary'][:500]}{'...' if len(gemini_output['summary']) > 500 else ''}

📚 Papers: {len(papers)} | Sources: {journal_str}
🏷️ Tags: {tags_str}

💼 LinkedIn: <i>{gemini_output['linkedin_snippet'][:200]}</i>"""

    # Inline keyboard with 3 buttons
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Publish", "callback_data": f"PUBLISH_{filename}"},
                {"text": "✏️ Edit", "callback_data": f"EDIT_{filename}"},
                {"text": "🗑️ Discard", "callback_data": f"DISCARD_{filename}"},
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
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass


def send_published_confirmation(filename: str, site_url: str, linkedin_text: str):
    """Send confirmation after publishing with LinkedIn copy-paste text."""
    message = f"""✅ <b>Published!</b>

🔗 <a href="{site_url}">{filename}</a>

📋 <b>Copy for LinkedIn:</b>
<code>{linkedin_text}</code>"""

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
    send_simple_message("🧪 AeroSentinel Telegram bot is connected!")
    print("Test message sent. Check your Telegram.")
