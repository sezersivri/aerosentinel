"""
AeroSentinel Pipeline
Orchestrates: Hunt → Summarize → Notify → (wait for approval) → Publish

This is the main entry point called by GitHub Actions.

Usage:
    python -m src.pipeline              # Full pipeline (hunt + summarize + notify)
    python -m src.pipeline --hunt-only  # Only run the hunter (test mode)
    python -m src.pipeline --publish FILENAME  # Publish a specific draft
"""

import json
import os
import sys
import shutil
from datetime import datetime

from src.hunter import run_hunt
from src.brain import run_brain
from src.notifier import send_draft_preview, send_simple_message
from src.config import DRAFTS_DIR, POSTS_DIR, MIN_PAPERS_PER_POST


def ensure_dirs():
    """Create content directories if they don't exist."""
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    os.makedirs(POSTS_DIR, exist_ok=True)


def run_scout():
    """
    Full scout pipeline: Hunt → Brain → Notify.
    Called by the scheduled GitHub Action (every 2 days).
    """
    ensure_dirs()

    print("\n" + "=" * 60)
    print("🛰️  AEROSENTINEL SCOUT PIPELINE")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # --- STAGE 1: HUNT ---
    papers = run_hunt(dry_run=False)

    if len(papers) < MIN_PAPERS_PER_POST:
        msg = f"🔇 AeroSentinel: Only {len(papers)} papers found (need {MIN_PAPERS_PER_POST}). Skipping this cycle."
        print(f"\n{msg}")
        send_simple_message(msg)
        return

    # --- STAGE 2: BRAIN ---
    result = run_brain(papers)

    if result is None:
        msg = "⚠️ AeroSentinel: Gemini summarization failed. Check logs."
        print(f"\n{msg}")
        send_simple_message(msg)
        return

    filename, post_content, gemini_output = result

    # Save draft to _drafts/
    draft_path = os.path.join(DRAFTS_DIR, filename)
    with open(draft_path, "w") as f:
        f.write(post_content)
    print(f"\n💾 Draft saved: {draft_path}")

    # Also save metadata for the publisher
    meta_path = os.path.join(DRAFTS_DIR, filename.replace(".md", ".meta.json"))
    with open(meta_path, "w") as f:
        json.dump({
            "filename": filename,
            "gemini_output": gemini_output,
            "papers_count": len(papers),
            "created_at": datetime.now().isoformat(),
        }, f, indent=2)

    # --- STAGE 3: NOTIFY ---
    send_draft_preview(filename, gemini_output, papers, post_content)

    print("\n✅ Scout pipeline complete. Awaiting your approval on Telegram.")


def run_publish(filename: str):
    """
    Publish a draft: move from _drafts/ to _posts/.
    Called by GitHub Action triggered from Telegram approval.
    """
    ensure_dirs()

    draft_path = os.path.join(DRAFTS_DIR, filename)
    post_path = os.path.join(POSTS_DIR, filename)

    if not os.path.exists(draft_path):
        print(f"⚠️ Draft not found: {draft_path}")
        return False

    # Move draft to posts
    shutil.move(draft_path, post_path)
    print(f"✅ Published: {draft_path} → {post_path}")

    # Clean up metadata file
    meta_path = draft_path.replace(".md", ".meta.json")
    if os.path.exists(meta_path):
        os.remove(meta_path)

    return True


def run_discard(filename: str):
    """Delete a draft that was rejected."""
    draft_path = os.path.join(DRAFTS_DIR, filename)
    if os.path.exists(draft_path):
        os.remove(draft_path)
        print(f"🗑️ Discarded: {draft_path}")

    meta_path = draft_path.replace(".md", ".meta.json")
    if os.path.exists(meta_path):
        os.remove(meta_path)


if __name__ == "__main__":
    if "--hunt-only" in sys.argv:
        # Test mode: just run the hunter
        run_hunt(dry_run=True)

    elif "--publish" in sys.argv:
        # Publish mode: move a specific draft to posts
        idx = sys.argv.index("--publish")
        if idx + 1 < len(sys.argv):
            run_publish(sys.argv[idx + 1])
        else:
            print("Usage: python -m src.pipeline --publish FILENAME")

    elif "--discard" in sys.argv:
        idx = sys.argv.index("--discard")
        if idx + 1 < len(sys.argv):
            run_discard(sys.argv[idx + 1])

    else:
        # Default: full scout pipeline
        run_scout()
