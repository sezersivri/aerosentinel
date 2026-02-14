"""
AeroSentinel Brain
Sends paper abstracts to Gemini 2.5 Pro API for professional summarization.
Produces structured output ready for Hugo publishing.
"""
import json
import requests
from datetime import datetime

from src.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS, MIN_PAPERS_PER_POST

# ──────────────────────────────────────────────
#  SYSTEM PROMPT (Co-designed by Claude + Gemini)
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Principal Aerodynamicist at a major defense/aerospace research organization.
Your task is to synthesize the following academic paper abstracts into a professional research intelligence briefing.

Instructions:
1. SYNTHESIS OVER SUMMARY: Do not list papers one by one. Write a single, cohesive narrative paragraph (150-200 words) that weaves the findings together thematically. Use connecting phrases like "In a complementary study..." or "Addressing the specific challenge of..."

2. TECHNICAL DEPTH: Presume the reader understands high-speed flow physics (M > 5). Use precise terminology: entropy layer swallowing, shock-boundary layer interaction, catalytic wall effects, stagnation-point heating, laminar-turbulent transition, conjugate heat transfer, etc.

3. NO FLUFF: Remove all introductory filler ("In recent years...", "This paper discusses..."). Start directly with the physics and findings.

4. ATTRIBUTION: Cite authors naturally in the narrative (e.g., "Chen et al. demonstrate that..." or "The DLR group's approach to...").

5. SPECIFICITY: Mention specific methods, Mach numbers, geometries, and quantitative results when available. Never use words like "groundbreaking," "revolutionary," or "novel."

6. OUTPUT FORMAT: Return ONLY a raw JSON object (no markdown fences, no explanation). The JSON must have exactly these fields:
{
  "title": "A precise technical title (max 15 words)",
  "summary": "The narrative synthesis paragraph (150-200 words)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "linkedin_snippet": "A 2-sentence teaser in casual-professional tone for LinkedIn, with 3 relevant hashtags"
}"""


def prepare_papers_for_prompt(papers: list) -> str:
    """Format paper data into a clean text block for the LLM."""
    blocks = []
    for i, paper in enumerate(papers, 1):
        author_str = ", ".join(paper.get("authors", [])[:4])
        if len(paper.get("authors", [])) > 4:
            author_str += " et al."
        block = f"""--- Paper {i} ---
Title: {paper.get('title', 'N/A')}
Authors: {author_str}
Journal: {paper.get('journal', 'N/A')}
Date: {paper.get('date', 'N/A')}
DOI: {paper.get('doi', 'N/A')}
Abstract: {paper.get('abstract', 'No abstract available.')}"""
        blocks.append(block)
    return "\n\n".join(blocks)


def call_gemini(papers: list) -> dict:
    """Call Google Gemini 2.5 Pro API to generate the summary."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment variables")
    if len(papers) < MIN_PAPERS_PER_POST:
        raise ValueError(f"Need at least {MIN_PAPERS_PER_POST} papers, got {len(papers)}")

    papers_text = prepare_papers_for_prompt(papers)
    user_prompt = f"""Here are {len(papers)} recent papers in aerospace/hypersonic research. Synthesize them according to your instructions.

{papers_text}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": GEMINI_MAX_TOKENS,
            "responseMimeType": "application/json"
        }
    }

    print(f"\n🧠 [{GEMINI_MODEL}] Generating summary from {len(papers)} papers...")

    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(url, json=payload, timeout=120)
            if r.status_code == 429 and attempt < max_retries - 1:
                wait = 30 * (attempt + 1)
                print(f"   ⏳ Rate limited, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue
            if r.status_code != 200:
                print(f"   ⚠️ Gemini API error: HTTP {r.status_code}")
                print(f"   Response: {r.text[:500]}")
                return None

            response = r.json()
            text = response["candidates"][0]["content"]["parts"][0]["text"]

            # Clean markdown fences if present
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)

            for field in ["title", "summary", "tags", "linkedin_snippet"]:
                if field not in result:
                    print(f"   ⚠️ Missing field: {field}")
                    return None

            print(f"   ✅ Title: {result['title']}")
            print(f"   ✅ Summary: {len(result['summary'])} chars")
            print(f"   ✅ Tags: {', '.join(result['tags'])}")
            return result

        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"   ⚠️ Gemini error: {e}")
            return None
    return None


def generate_hugo_post(gemini_output: dict, papers: list) -> str:
    """Generate a complete Hugo markdown post."""
    today = datetime.now().strftime("%Y-%m-%d")
    tags_yaml = "\n".join([f'  - "{tag}"' for tag in gemini_output["tags"]])

    references = []
    for i, paper in enumerate(papers, 1):
        author_str = ", ".join(paper.get("authors", [])[:3])
        if len(paper.get("authors", [])) > 3:
            author_str += " et al."
        ref = f'[{i}] {author_str}, "{paper["title"]}," *{paper["journal"]}*, {paper.get("date", "2026")}.'
        if paper.get("url"):
            ref += f' [Link]({paper["url"]})'
        references.append(ref)

    return f"""---
title: "{gemini_output['title']}"
date: {today}
tags:
{tags_yaml}
summary: "{gemini_output['linkedin_snippet'].split('.')[0]}."
draft: false
papers_count: {len(papers)}
---

{gemini_output['summary']}

## References

{chr(10).join(references)}
"""


def generate_filename(title: str) -> str:
    """Generate a URL-friendly filename from the title."""
    today = datetime.now().strftime("%Y-%m-%d")
    clean = title.lower()
    clean = "".join(c if c.isalnum() or c == " " else "" for c in clean)
    clean = "-".join(clean.split()[:6])
    return f"{today}-{clean}.md"


def run_brain(papers: list) -> tuple:
    """Full brain pipeline: summarize → generate Hugo post."""
    result = call_gemini(papers)
    if not result:
        return None
    post_content = generate_hugo_post(result, papers)
    filename = generate_filename(result["title"])
    print(f"\n📄 Generated post: {filename}")
    return filename, post_content, result


if __name__ == "__main__":
    import os
    if os.path.exists("latest_hunt.json"):
        with open("latest_hunt.json") as f:
            papers = json.load(f)
        result = run_brain(papers)
        if result:
            filename, content, _ = result
            print("\n" + "=" * 60)
            print(content)
    else:
        print("No latest_hunt.json found. Run hunter.py first.")
