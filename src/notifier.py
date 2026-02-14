"""
AeroSentinel Notifier
Sends draft previews to Telegram with inline Publish/Edit/Discard buttons.
Uses filename_base (without lang suffix) for callback data.
"""

import json
import requests

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_draft_preview(
    filename_base: str,
    gemini_output: dict,
    papers: list,
    post_content: str
):
    """
    Send a formatted preview to Telegram with inline keyboard buttons.
    Uses filename_base (no lang suffix) in callback_data.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    # Build the preview message
    journal_list = list(set(p["journal"] for p in papers))
    journal_str = ", ".join(journal_list[:4])
    tags_str = ", ".join(gemini_output.get("tags", [])[:5])

    # Use overview instead of summary for the new rich format
    overview = gemini_output.get("overview", gemini_output.get("summary", ""))

    # Paper type summary (support both schemas)
    paper_types = {}
    all_analyzed = (
        gemini_output.get("core_papers", [])
        + gemini_output.get("peripheral_papers", [])
        + gemini_output.get("papers", [])
    )
    for p in all_analyzed:
        ptype = p.get("paper_type", "unknown")
        paper_types[ptype] = paper_types.get(ptype, 0) + 1
    type_str = ", ".join(f"{v}x {k}" for k, v in paper_types.items())

    # Core / peripheral counts
    core_count = len(gemini_output.get("core_papers", []))
    periph_count = len(gemini_output.get("peripheral_papers", []))
    if core_count:
        structure_str = f"🎯 Core: {core_count} (full analysis) | 📄 Context: {periph_count} (narrative)"
    else:
        structure_str = f"📚 Papers: {len(papers)} | Types: {type_str}"

    message = f"""🛰️ <b>AeroSentinel v2.3 — New Research Digest</b>

📋 <b>{gemini_output.get('title', 'Untitled')}</b>

📝 {overview[:500]}{'...' if len(overview) > 500 else ''}

{structure_str}
📰 Sources: {journal_str}
🏷️ Tags: {tags_str}
🌐 Languages: EN + TR
"""

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
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
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
