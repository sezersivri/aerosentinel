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
from src.brain import run_brain, generate_hugo_post
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


def normalize_and_validate(gemini_output):
    """Normalize tags, validate paper types, filter low-relevance papers."""
    from src.config import VALID_TAGS, VALID_TAGS_LOWER, VALID_PAPER_TYPES, MIN_RELEVANCE_SCORE

    # --- Filter low-relevance papers ---
    gemini_output["papers"] = [
        p for p in gemini_output.get("papers", [])
        if p.get("relevance_score", 0) >= MIN_RELEVANCE_SCORE
    ]

    # --- Normalize tags ---
    raw_tags = gemini_output.get("tags", [])
    normalized = []
    for tag in raw_tags:
        # Exact match
        if tag in VALID_TAGS:
            normalized.append(tag)
            continue
        # Case-insensitive match
        lower = tag.lower()
        if lower in VALID_TAGS_LOWER:
            normalized.append(VALID_TAGS_LOWER[lower])
            continue
        # Substring match (for tags > 10 chars, check if any valid tag contains it or vice versa)
        if len(tag) > 10:
            matched = False
            for valid_lower, canonical in VALID_TAGS_LOWER.items():
                if lower in valid_lower or valid_lower in lower:
                    normalized.append(canonical)
                    matched = True
                    break
            if matched:
                continue
        # Drop unrecognized tag
        print(f"   ⚠️ Dropping invalid tag: '{tag}'")

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for t in normalized:
        if t not in seen:
            seen.add(t)
            deduped.append(t)

    # Enforce 4-7 count
    if len(deduped) > 7:
        deduped = deduped[:7]

    gemini_output["tags"] = deduped

    # --- Validate paper types ---
    OLD_TO_NEW = {"ml_surrogate": "ml_heating"}
    for paper in gemini_output.get("papers", []):
        ptype = paper.get("paper_type", "")
        if ptype in OLD_TO_NEW:
            paper["paper_type"] = OLD_TO_NEW[ptype]
        elif ptype not in VALID_PAPER_TYPES:
            paper["paper_type"] = "numerical_cfd"  # safe default

    return gemini_output


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

    # --- STAGE 2.5: VALIDATE & NORMALIZE ---
    for lang in LANGUAGES:
        if lang not in result:
            continue
        result[lang]["gemini_output"] = normalize_and_validate(result[lang]["gemini_output"])

    # Force TR to use same English tags as EN
    if "en" in result and "tr" in result:
        result["tr"]["gemini_output"]["tags"] = result["en"]["gemini_output"]["tags"]

    # Regenerate post content with cleaned data
    for lang in LANGUAGES:
        if lang not in result:
            continue
        result[lang]["content"] = generate_hugo_post(result[lang]["gemini_output"], papers, lang=lang)

    # Check paper count still sufficient after filtering
    max_papers = max(
        len(result[lang]["gemini_output"].get("papers", []))
        for lang in LANGUAGES if lang in result
    )
    if max_papers < MIN_PAPERS_PER_POST:
        msg = f"⚠️ AeroSentinel: Only {max_papers} papers passed relevance filter (need {MIN_PAPERS_PER_POST}). Skipping."
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
