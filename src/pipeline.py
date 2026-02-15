"""
AeroSentinel Pipeline
Orchestrates: Hunt -> Summarize (bilingual) -> Notify -> (wait for approval) -> Publish

This is the main entry point called by GitHub Actions.

Usage:
    python -m src.pipeline                        # Full pipeline (hunt + summarize + notify)
    python -m src.pipeline --hunt-only            # Only run the hunter (test mode)
    python -m src.pipeline --publish FILENAME_BASE  # Publish both language drafts
    python -m src.pipeline --discard FILENAME_BASE  # Discard both language drafts
    python -m src.pipeline --search '{"tags":["Hypersonic Flow"],"date_from":"2025-12-01","date_to":"2026-02-01"}'
    python -m src.pipeline --weekly-stats         # Send weekly usage summary to Telegram
"""

import json
import os
import re
import sys
import shutil
import time
from collections import Counter
from datetime import datetime, timedelta

from src.hunter import run_hunt
from src.brain import run_brain, generate_hugo_post
from src.notifier import send_draft_preview, send_simple_message
from src.config import (
    DRAFTS_DIR, POSTS_DIR, MIN_PAPERS_PER_POST, LANGUAGES,
    TAG_TO_KEYWORDS, USAGE_STATS_FILE,
)


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
    """Normalize tags and validate paper type for a single-paper Gemini output."""
    from src.config import (
        VALID_TAGS, VALID_TAGS_LOWER, VALID_PAPER_TYPES,
    )

    # --- Normalize tags ---
    raw_tags = gemini_output.get("tags", [])
    normalized = []
    for tag in raw_tags:
        if tag in VALID_TAGS:
            normalized.append(tag)
            continue
        lower = tag.lower()
        if lower in VALID_TAGS_LOWER:
            normalized.append(VALID_TAGS_LOWER[lower])
            continue
        if len(tag) > 10:
            matched = False
            for valid_lower, canonical in VALID_TAGS_LOWER.items():
                if lower in valid_lower or valid_lower in lower:
                    normalized.append(canonical)
                    matched = True
                    break
            if matched:
                continue
        print(f"   ⚠️ Dropping invalid tag: '{tag}'")

    seen = set()
    deduped = []
    for t in normalized:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    if len(deduped) > 7:
        deduped = deduped[:7]
    gemini_output["tags"] = deduped

    # --- Validate paper type ---
    OLD_TO_NEW = {"ml_surrogate": "ml_heating"}
    ptype = gemini_output.get("paper_type", "")
    if ptype in OLD_TO_NEW:
        gemini_output["paper_type"] = OLD_TO_NEW[ptype]
    elif ptype not in VALID_PAPER_TYPES:
        gemini_output["paper_type"] = "numerical_cfd"

    return gemini_output


# ──────────────────────────────────────────────
#  USAGE STATS TRACKING
# ──────────────────────────────────────────────

def load_usage_stats() -> dict:
    """Load usage stats from JSON file."""
    if os.path.exists(USAGE_STATS_FILE):
        try:
            with open(USAGE_STATS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"runs": []}
    return {"runs": []}


def save_usage_stats(stats: dict):
    """Save usage stats to JSON file."""
    with open(USAGE_STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def record_run_stats(run_type: str, papers_found: int, papers_selected: int,
                     sources: dict, duration: float, gemini_calls: int = 0,
                     token_usage: dict = None):
    """Record stats for a single pipeline run."""
    stats = load_usage_stats()
    run_entry = {
        "type": run_type,
        "timestamp": datetime.now().isoformat(),
        "papers_found": papers_found,
        "papers_selected": papers_selected,
        "sources": sources,
        "gemini_calls": gemini_calls,
        "duration_seconds": round(duration, 1),
    }
    if token_usage:
        run_entry["token_usage"] = token_usage
    stats["runs"].append(run_entry)
    save_usage_stats(stats)


def format_usage_message(stats: dict) -> str:
    """Format usage stats as a Telegram-friendly message."""
    runs = stats.get("runs", [])
    if not runs:
        return "📊 No pipeline runs recorded yet."

    total_found = sum(r.get("papers_found", 0) for r in runs)
    total_selected = sum(r.get("papers_selected", 0) for r in runs)
    total_gemini = sum(r.get("gemini_calls", 0) for r in runs)
    total_duration = sum(r.get("duration_seconds", 0) for r in runs)

    total_prompt_tokens = 0
    total_output_tokens = 0
    for r in runs:
        tu = r.get("token_usage", {})
        if isinstance(tu, dict):
            for lang_data in tu.values():
                if isinstance(lang_data, dict):
                    total_prompt_tokens += lang_data.get("prompt_tokens", 0)
                    total_output_tokens += lang_data.get("candidates_tokens", 0)

    # Aggregate source counts
    agg_sources = Counter()
    for r in runs:
        for src, cnt in r.get("sources", {}).items():
            agg_sources[src] += cnt

    source_str = ", ".join(f"{src}({cnt})" for src, cnt in sorted(agg_sources.items()))
    mins = int(total_duration // 60)
    secs = int(total_duration % 60)

    token_line = ""
    if total_prompt_tokens or total_output_tokens:
        token_line = f"├ Tokens: {total_prompt_tokens + total_output_tokens:,} (prompt: {total_prompt_tokens:,}, output: {total_output_tokens:,})\n"

    return (
        f"📊 Pipeline Stats ({len(runs)} runs)\n"
        f"├ Papers: {total_found} found → {total_selected} selected\n"
        f"├ Gemini calls: {total_gemini}\n"
        f"{token_line}"
        f"├ Sources: {source_str}\n"
        f"└ Duration: {mins}m {secs}s"
    )


def run_weekly_stats():
    """Send weekly usage summary to Telegram (last 4 weeks)."""
    stats = load_usage_stats()
    cutoff = (datetime.now() - timedelta(weeks=4)).isoformat()

    # Filter to last 4 weeks
    recent = {"runs": [
        r for r in stats.get("runs", [])
        if r.get("timestamp", "") >= cutoff
    ]}

    msg = format_usage_message(recent)
    print(msg)
    send_simple_message(msg)


# ──────────────────────────────────────────────
#  CUSTOM SEARCH (Telegram /search command)
# ──────────────────────────────────────────────

def run_custom_search(search_json: str):
    """
    Run a custom tag-based search from Telegram /search command.
    search_json: '{"tags": ["Hypersonic Flow", ...], "date_from": "2025-12-01", "date_to": "2026-02-01"}'
    """
    ensure_dirs()
    t_start = time.time()

    try:
        params = json.loads(search_json)
    except json.JSONDecodeError as e:
        msg = f"⚠️ Invalid search JSON: {e}"
        print(msg)
        send_simple_message(msg)
        return

    tags = params.get("tags", [])
    date_from = params.get("date_from")
    date_to = params.get("date_to")

    if not tags:
        msg = "⚠️ No tags provided in search request."
        print(msg)
        send_simple_message(msg)
        return

    # Convert tags to search keywords via TAG_TO_KEYWORDS
    custom_keywords = []
    for tag in tags:
        kws = TAG_TO_KEYWORDS.get(tag, [])
        if kws:
            custom_keywords.extend(kws)
        else:
            # Use the tag itself as a keyword if not in mapping
            custom_keywords.append(tag.lower())

    # Deduplicate keywords while preserving order
    seen_kw = set()
    deduped_kw = []
    for kw in custom_keywords:
        if kw not in seen_kw:
            seen_kw.add(kw)
            deduped_kw.append(kw)
    custom_keywords = deduped_kw

    print(f"\n🔎 Custom search: tags={tags}, keywords={len(custom_keywords)}, "
          f"date_from={date_from}, date_to={date_to}")

    # --- STAGE 1: HUNT (custom) ---
    papers = run_hunt(dry_run=False, custom_keywords=custom_keywords,
                      date_from=date_from, date_to=date_to)

    if len(papers) < MIN_PAPERS_PER_POST:
        duration = time.time() - t_start
        source_counts = dict(Counter(p.get("source", "Unknown") for p in papers))
        record_run_stats("custom_search", len(papers), 0, source_counts, duration)
        msg = f"🔇 Custom search: Only {len(papers)} papers found (need {MIN_PAPERS_PER_POST}). No briefing generated."
        print(f"\n{msg}")
        send_simple_message(msg)
        return

    # Flag papers with missing abstracts for Gemini
    for paper in papers:
        if not paper.get("abstract") or paper["abstract"].strip() == "":
            paper["abstract"] = "[NO ABSTRACT] " + paper.get("title", "")

    # --- STAGE 2: BRAIN (bilingual, per paper) ---
    results = run_brain(papers)

    if not results:
        duration = time.time() - t_start
        source_counts = dict(Counter(p.get("source", "Unknown") for p in papers))
        record_run_stats("custom_search", len(papers), len(papers), source_counts, duration, gemini_calls=1)
        msg = "⚠️ Custom search: Gemini analysis failed for all papers. Check logs."
        print(f"\n{msg}")
        send_simple_message(msg)
        return

    # --- STAGE 2.5 + 3: VALIDATE, SAVE, NOTIFY per paper ---
    total_token_usage = {}
    papers_published = 0

    for result in results:
        # Validate & normalize each language
        for lang in LANGUAGES:
            if lang not in result:
                continue
            result[lang]["gemini_output"] = normalize_and_validate(result[lang]["gemini_output"])

        # Force TR to use same English tags as EN
        if "en" in result and "tr" in result:
            result["tr"]["gemini_output"]["tags"] = result["en"]["gemini_output"]["tags"]
        elif "tr" in result and "en" not in result:
            from src.config import VALID_TAGS, VALID_TAGS_LOWER
            tr_tags = result["tr"]["gemini_output"].get("tags", [])
            normalized = []
            for tag in tr_tags:
                if tag in VALID_TAGS:
                    normalized.append(tag)
                elif tag.lower() in VALID_TAGS_LOWER:
                    normalized.append(VALID_TAGS_LOWER[tag.lower()])
                else:
                    for valid_lower, canonical in VALID_TAGS_LOWER.items():
                        if tag.lower() in valid_lower or valid_lower in tag.lower():
                            normalized.append(canonical)
                            break
            if normalized:
                result["tr"]["gemini_output"]["tags"] = normalized
                print(f"   🏷️ TR tags normalized to English: {normalized}")

        # Regenerate post content with cleaned data
        for lang in LANGUAGES:
            if lang not in result:
                continue
            result[lang]["content"] = generate_hugo_post(
                result[lang]["gemini_output"], result["paper"], lang=lang
            )

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

        # Save metadata
        paper = result["paper"]
        meta = {
            "filename_base": filename_base,
            "filename_en": result.get("en", {}).get("filename", ""),
            "filename_tr": result.get("tr", {}).get("filename", ""),
            "gemini_output_en": result.get("en", {}).get("gemini_output", {}),
            "gemini_output_tr": result.get("tr", {}).get("gemini_output", {}),
            "paper": {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "journal": paper.get("journal", ""),
                "url": paper.get("url", ""),
                "doi": paper.get("doi", ""),
                "date": paper.get("date", ""),
            },
            "search_params": params,
            "created_at": datetime.now().isoformat(),
        }
        meta_path = os.path.join(DRAFTS_DIR, f"{filename_base}.meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # Send Telegram preview for THIS paper
        en_data = result.get("en", result.get("tr", {}))
        send_draft_preview(
            filename_base,
            en_data.get("gemini_output", {}),
            paper,
            en_data.get("content", ""),
        )

        papers_published += 1

        # Aggregate token usage
        if "token_usage" in result:
            for lang, usage in result["token_usage"].items():
                if lang not in total_token_usage:
                    total_token_usage[lang] = usage
                else:
                    for k, v in usage.items():
                        total_token_usage[lang][k] = total_token_usage[lang].get(k, 0) + v

    # Record usage stats
    duration = time.time() - t_start
    source_counts = dict(Counter(p.get("source", "Unknown") for p in papers))
    record_run_stats("custom_search", len(papers), papers_published, source_counts, duration,
                     gemini_calls=papers_published * len(LANGUAGES),
                     token_usage=total_token_usage if total_token_usage else None)

    print(f"\n✅ Custom search pipeline complete. {papers_published} paper(s) sent for review.")


def run_scout():
    """
    Full scout pipeline: Hunt -> Brain (bilingual per paper) -> Notify.
    Called by the scheduled GitHub Action.
    """
    ensure_dirs()
    t_start = time.time()

    print("\n" + "=" * 60)
    print("🛰️  AEROSENTINEL SCOUT PIPELINE v2.5")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # --- STAGE 1: HUNT ---
    papers = run_hunt(dry_run=False)

    if len(papers) < MIN_PAPERS_PER_POST:
        duration = time.time() - t_start
        source_counts = dict(Counter(p.get("source", "Unknown") for p in papers))
        record_run_stats("scout", len(papers), 0, source_counts, duration)
        msg = f"🔇 AeroSentinel: No papers found above threshold. Skipping this cycle."
        print(f"\n{msg}")
        send_simple_message(msg)
        return

    # Flag papers with missing abstracts for Gemini
    for paper in papers:
        if not paper.get("abstract") or paper["abstract"].strip() == "":
            paper["abstract"] = "[NO ABSTRACT] " + paper.get("title", "")

    # --- STAGE 2: BRAIN (bilingual, per paper) ---
    results = run_brain(papers)

    if not results:
        duration = time.time() - t_start
        source_counts = dict(Counter(p.get("source", "Unknown") for p in papers))
        record_run_stats("scout", len(papers), len(papers), source_counts, duration, gemini_calls=1)
        msg = "⚠️ AeroSentinel: Gemini analysis failed for all papers. Check logs."
        print(f"\n{msg}")
        send_simple_message(msg)
        return

    # --- STAGE 2.5 + 3: VALIDATE, SAVE, NOTIFY per paper ---
    total_token_usage = {}
    papers_published = 0

    for result in results:
        # Validate & normalize each language
        for lang in LANGUAGES:
            if lang not in result:
                continue
            result[lang]["gemini_output"] = normalize_and_validate(result[lang]["gemini_output"])

        # Force TR to use same English tags as EN
        if "en" in result and "tr" in result:
            result["tr"]["gemini_output"]["tags"] = result["en"]["gemini_output"]["tags"]
        elif "tr" in result and "en" not in result:
            from src.config import VALID_TAGS, VALID_TAGS_LOWER
            tr_tags = result["tr"]["gemini_output"].get("tags", [])
            normalized = []
            for tag in tr_tags:
                if tag in VALID_TAGS:
                    normalized.append(tag)
                elif tag.lower() in VALID_TAGS_LOWER:
                    normalized.append(VALID_TAGS_LOWER[tag.lower()])
                else:
                    for valid_lower, canonical in VALID_TAGS_LOWER.items():
                        if tag.lower() in valid_lower or valid_lower in tag.lower():
                            normalized.append(canonical)
                            break
            if normalized:
                result["tr"]["gemini_output"]["tags"] = normalized
                print(f"   🏷️ TR tags normalized to English: {normalized}")

        # Regenerate post content with cleaned data
        for lang in LANGUAGES:
            if lang not in result:
                continue
            result[lang]["content"] = generate_hugo_post(
                result[lang]["gemini_output"], result["paper"], lang=lang
            )

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

        # Save metadata
        paper = result["paper"]
        meta = {
            "filename_base": filename_base,
            "filename_en": result.get("en", {}).get("filename", ""),
            "filename_tr": result.get("tr", {}).get("filename", ""),
            "gemini_output_en": result.get("en", {}).get("gemini_output", {}),
            "gemini_output_tr": result.get("tr", {}).get("gemini_output", {}),
            "paper": {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", []),
                "journal": paper.get("journal", ""),
                "url": paper.get("url", ""),
                "doi": paper.get("doi", ""),
                "date": paper.get("date", ""),
            },
            "created_at": datetime.now().isoformat(),
        }
        meta_path = os.path.join(DRAFTS_DIR, f"{filename_base}.meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # Send Telegram preview for THIS paper
        en_data = result.get("en", result.get("tr", {}))
        send_draft_preview(
            filename_base,
            en_data.get("gemini_output", {}),
            paper,
            en_data.get("content", ""),
        )

        papers_published += 1

        # Aggregate token usage
        if "token_usage" in result:
            for lang, usage in result["token_usage"].items():
                if lang not in total_token_usage:
                    total_token_usage[lang] = usage
                else:
                    for k, v in usage.items():
                        total_token_usage[lang][k] = total_token_usage[lang].get(k, 0) + v

    # Record usage stats
    duration = time.time() - t_start
    source_counts = dict(Counter(p.get("source", "Unknown") for p in papers))
    record_run_stats("scout", len(papers), papers_published, source_counts, duration,
                     gemini_calls=papers_published * len(LANGUAGES),
                     token_usage=total_token_usage if total_token_usage else None)

    print(f"\n✅ Scout pipeline complete. {papers_published} paper(s) sent for review.")


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

    elif "--search" in sys.argv:
        # Custom tag-based search from Telegram
        idx = sys.argv.index("--search")
        if idx + 1 < len(sys.argv):
            run_custom_search(sys.argv[idx + 1])
        else:
            print("Usage: python -m src.pipeline --search '{\"tags\":[...],\"date_from\":\"...\",\"date_to\":\"...\"}'")

    elif "--weekly-stats" in sys.argv:
        # Send weekly usage stats to Telegram
        run_weekly_stats()

    else:
        # Default: full scout pipeline
        run_scout()
