"""
AeroSentinel Pipeline
Orchestrates: Hunt -> Summarize (bilingual) -> Notify -> (wait for approval) -> Publish

This is the main entry point called by GitHub Actions.

Usage:
    python -m src.pipeline              # Full pipeline (hunt + summarize + notify)
    python -m src.pipeline --hunt-only  # Only run the hunter (test mode)
    python -m src.pipeline --publish FILENAME_BASE  # Publish both language drafts
    python -m src.pipeline --discard FILENAME_BASE  # Discard both language drafts
"""

import json
import os
import re
import sys
import shutil
from datetime import datetime

from src.hunter import run_hunt
from src.brain import run_brain
from src.notifier import send_draft_preview, send_simple_message
from src.config import DRAFTS_DIR, POSTS_DIR, MIN_PAPERS_PER_POST, LANGUAGES


def ensure_dirs():
    """Create content directories if they don't exist."""
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    os.makedirs(POSTS_DIR, exist_ok=True)


def validate_filename(filename: str) -> bool:
    """
    Validate filename to prevent path traversal attacks.
    Only allows alphanumeric, hyphens, dots, and underscores.
    """
    # Block path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        print(f"SECURITY: Blocked path traversal attempt: {filename}")
        return False

    # Only allow safe characters
    if not re.match(r'^[a-zA-Z0-9\-_.]+$', filename):
        print(f"SECURITY: Invalid characters in filename: {filename}")
        return False

    # Verify resolved path stays within expected directory
    for directory in [DRAFTS_DIR, POSTS_DIR]:
        test_path = os.path.realpath(os.path.join(directory, filename))
        expected_dir = os.path.realpath(directory)
        if not test_path.startswith(expected_dir):
            print(f"SECURITY: Path escape detected: {test_path}")
            return False

    return True


def run_scout():
    """
    Full scout pipeline: Hunt -> Brain (bilingual) -> Notify.
    Called by the scheduled GitHub Action.
    """
    ensure_dirs()

    print("\n" + "=" * 60)
    print("🛰️  AEROSENTINEL SCOUT PIPELINE v2")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # --- STAGE 1: HUNT ---
    papers = run_hunt(dry_run=False)

    if len(papers) < MIN_PAPERS_PER_POST:
        msg = f"🔇 AeroSentinel: Only {len(papers)} papers found (need {MIN_PAPERS_PER_POST}). Skipping this cycle."
        print(f"\n{msg}")
        send_simple_message(msg)
        return

    # --- STAGE 2: BRAIN (bilingual) ---
    result = run_brain(papers)

    if result is None:
        msg = "⚠️ AeroSentinel: Gemini summarization failed. Check logs."
        print(f"\n{msg}")
        send_simple_message(msg)
        return

    filename_base = result["filename_base"]

    # Save drafts for each language
    for lang in LANGUAGES:
        if lang not in result:
            continue
        lang_data = result[lang]
        draft_path = os.path.join(DRAFTS_DIR, lang_data["filename"])
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(lang_data["content"])
        print(f"💾 Draft saved: {draft_path}")

    # Save metadata (shared across languages)
    meta = {
        "filename_base": filename_base,
        "filename_en": result.get("en", {}).get("filename", ""),
        "filename_tr": result.get("tr", {}).get("filename", ""),
        "gemini_output_en": result.get("en", {}).get("gemini_output", {}),
        "gemini_output_tr": result.get("tr", {}).get("gemini_output", {}),
        "papers_count": len(papers),
        "created_at": datetime.now().isoformat(),
    }
    meta_path = os.path.join(DRAFTS_DIR, f"{filename_base}.meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # --- STAGE 3: NOTIFY (use EN data for preview) ---
    en_data = result.get("en", result.get("tr", {}))
    send_draft_preview(
        filename_base,
        en_data.get("gemini_output", {}),
        papers,
        en_data.get("content", ""),
    )

    print("\n✅ Scout pipeline complete. Awaiting your approval on Telegram.")


def run_publish(filename_base: str):
    """
    Publish drafts: move both language files from drafts/ to posts/.
    Called by GitHub Action triggered from Telegram approval.
    """
    ensure_dirs()

    if not validate_filename(filename_base + ".en.md"):
        print(f"⚠️ Invalid filename base: {filename_base}")
        return False

    published = False
    for lang in LANGUAGES:
        filename = f"{filename_base}.{lang}.md"
        draft_path = os.path.join(DRAFTS_DIR, filename)
        post_path = os.path.join(POSTS_DIR, filename)

        if os.path.exists(draft_path):
            shutil.move(draft_path, post_path)
            print(f"✅ Published: {draft_path} → {post_path}")
            published = True
        else:
            print(f"⚠️ Draft not found: {draft_path}")

    # Clean up metadata file
    meta_path = os.path.join(DRAFTS_DIR, f"{filename_base}.meta.json")
    if os.path.exists(meta_path):
        os.remove(meta_path)

    return published


def run_discard(filename_base: str):
    """Delete drafts that were rejected (both languages)."""
    if not validate_filename(filename_base + ".en.md"):
        print(f"⚠️ Invalid filename base: {filename_base}")
        return

    for lang in LANGUAGES:
        filename = f"{filename_base}.{lang}.md"
        draft_path = os.path.join(DRAFTS_DIR, filename)
        if os.path.exists(draft_path):
            os.remove(draft_path)
            print(f"🗑️ Discarded: {draft_path}")

    meta_path = os.path.join(DRAFTS_DIR, f"{filename_base}.meta.json")
    if os.path.exists(meta_path):
        os.remove(meta_path)


if __name__ == "__main__":
    if "--hunt-only" in sys.argv:
        # Test mode: just run the hunter
        run_hunt(dry_run=True)

    elif "--publish" in sys.argv:
        # Publish mode: move drafts to posts
        idx = sys.argv.index("--publish")
        if idx + 1 < len(sys.argv):
            run_publish(sys.argv[idx + 1])
        else:
            print("Usage: python -m src.pipeline --publish FILENAME_BASE")

    elif "--discard" in sys.argv:
        idx = sys.argv.index("--discard")
        if idx + 1 < len(sys.argv):
            run_discard(sys.argv[idx + 1])

    else:
        # Default: full scout pipeline
        run_scout()
