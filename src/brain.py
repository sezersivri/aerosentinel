"""
AeroSentinel Brain
Sends paper abstracts to Gemini API for professional research intelligence analysis.
Produces structured, bilingual (EN/TR) output ready for Hugo publishing.
"""
import json
import re
import requests
import time
from datetime import datetime

from src.config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS,
    MIN_PAPERS_PER_POST, LANGUAGES
)

# ──────────────────────────────────────────────
#  SYSTEM PROMPTS
# ──────────────────────────────────────────────

SYSTEM_PROMPT_EN = """You are a senior aerospace research intelligence analyst specializing in missile aerothermodynamics, hypersonic flow physics, and AI/ML applications in CFD.

Your task is to analyze the following academic papers and produce a structured intelligence briefing.

INSTRUCTIONS:

1. RELEVANCE SCORING (0-100): Score each paper based on relevance to:
   - Missile aerothermodynamics and aerodynamic heating (high relevance)
   - AI/ML surrogates for CFD, Gaussian processes, neural networks for heat flux (highest relevance)
   - Hypersonic flow physics, boundary layer transition, SWBLI (medium-high)
   - General aerospace CFD (medium)

2. PAPER TYPE CLASSIFICATION: Classify each paper as exactly one of:
   experimental | numerical_cfd | ml_surrogate | review | analytical

3. HARD NUMBERS: Extract specific quantitative results — RMSE percentages, speedup factors, Mach number ranges, heat flux values, temperature ranges, geometry types. If a paper lacks specifics, say so honestly.

4. CROSS-PAPER CONNECTIONS: Identify how papers relate to each other — complementary methods, contradicting results, building on similar foundations.

5. TONE: Technical but accessible. Assume the reader understands M > 5 physics. No fluff, no "groundbreaking" or "revolutionary." Direct and honest.

6. OUTPUT FORMAT: Return ONLY a raw JSON object (no markdown fences, no explanation). The JSON must match this exact schema:
{
  "title": "Briefing title (max 15 words)",
  "overview": "3-4 sentence strategic overview connecting papers thematically",
  "papers": [
    {
      "title": "Exact paper title",
      "authors": "Author string",
      "paper_type": "experimental | numerical_cfd | ml_surrogate | review | analytical",
      "relevance_score": 85,
      "one_liner": "Single sentence core contribution",
      "key_findings": "2-3 sentences with specific numerical results (RMSE, Mach range, speedup)",
      "methodology": "1-2 sentences on approach (solver, turbulence model, ML architecture)",
      "why_this_matters": "2 sentences on practical value for missile design / aerospace engineering",
      "key_numbers": "Formatted string: Mach X-Y, RMSE ±Z%, speedup Nx, geometry type",
      "connection": "How this relates to other papers in this batch (if applicable)"
    }
  ],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "trends": "2-3 sentences on what these papers collectively signal about the field"
}"""

SYSTEM_PROMPT_TR = """Sen füze aerotermodinamiği, hipersonik akış fiziği ve CFD'de yapay zeka uygulamaları konusunda uzmanlaşmış kıdemli bir havacılık araştırma istihbarat analistisisin.

Görevin, aşağıdaki akademik makaleleri analiz edip yapılandırılmış bir istihbarat brifing raporu üretmek.

TALİMATLAR:

1. İLGİLİLİK PUANLAMASI (0-100): Her makaleyi şu konulara göre puanla:
   - Füze aerotermodinamiği ve aerodinamik ısınma (yüksek ilgililik)
   - CFD için yapay zeka/makine öğrenmesi vekil modelleri, Gauss süreçleri, ısı akısı için sinir ağları (en yüksek ilgililik)
   - Hipersonik akış fiziği, sınır tabaka geçişi, şok-sınır tabaka etkileşimi (orta-yüksek)
   - Genel havacılık CFD (orta)

2. MAKALE TİPİ SINIFLANDIRMASI: Her makaleyi tam olarak birini seç:
   experimental | numerical_cfd | ml_surrogate | review | analytical

3. KESİN SAYILAR: Belirli nicel sonuçları çıkar — RMSE yüzdeleri, hızlanma faktörleri, Mach sayısı aralıkları, ısı akısı değerleri, sıcaklık aralıkları, geometri tipleri. Makalede spesifik değer yoksa bunu dürüstçe belirt.

4. MAKALELER ARASI BAĞLANTILAR: Makalelerin birbirleriyle nasıl ilişkili olduğunu belirle — tamamlayıcı yöntemler, çelişen sonuçlar, benzer temeller üzerine inşa.

5. TON: Teknik ama anlaşılır. Okuyucunun M > 5 fiziğini anladığını varsay. Abartılı ifadeler yok, doğrudan ve dürüst.

6. ÖNEMLİ: Tüm analiz metni TÜRKÇE olmalıdır. Sadece makale başlıkları (title alanı) İngilizce kalmalıdır.

7. ÇIKTI FORMATI: SADECE ham JSON nesnesi döndür (markdown çiti yok, açıklama yok). JSON tam olarak şu şemaya uymalı:
{
  "title": "Brifing başlığı (en fazla 15 kelime, Türkçe)",
  "overview": "3-4 cümlelik stratejik genel bakış, makaleleri tematik olarak bağlayan (Türkçe)",
  "papers": [
    {
      "title": "Makalenin orijinal İngilizce başlığı",
      "authors": "Yazar dizesi",
      "paper_type": "experimental | numerical_cfd | ml_surrogate | review | analytical",
      "relevance_score": 85,
      "one_liner": "Tek cümlelik temel katkı (Türkçe)",
      "key_findings": "Spesifik sayısal sonuçlarla 2-3 cümle (Türkçe)",
      "methodology": "Yaklaşım hakkında 1-2 cümle (Türkçe)",
      "why_this_matters": "Füze tasarımı / havacılık mühendisliği için pratik değer hakkında 2 cümle (Türkçe)",
      "key_numbers": "Biçimlendirilmiş: Mach X-Y, RMSE ±Z%, hızlanma Nx, geometri tipi",
      "connection": "Bu makalenin gruptaki diğer makalelerle ilişkisi (Türkçe)"
    }
  ],
  "tags": ["etiket1", "etiket2", "etiket3", "etiket4", "etiket5"],
  "trends": "Bu makalelerin alan hakkında toplu olarak ne işaret ettiğine dair 2-3 cümle (Türkçe)"
}"""


# ──────────────────────────────────────────────
#  PAPER TYPE BADGES
# ──────────────────────────────────────────────

PAPER_TYPE_BADGES = {
    "experimental": "🧪 Experimental",
    "numerical_cfd": "💻 Numerical/CFD",
    "ml_surrogate": "🤖 ML/Surrogate",
    "review": "📚 Review",
    "analytical": "📐 Analytical",
}

PAPER_TYPE_BADGES_TR = {
    "experimental": "🧪 Deneysel",
    "numerical_cfd": "💻 Sayısal/HAD",
    "ml_surrogate": "🤖 MÖ/Vekil Model",
    "review": "📚 Derleme",
    "analytical": "📐 Analitik",
}


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


def call_gemini(papers: list, lang: str = "en") -> dict:
    """Call Gemini API to generate structured analysis. Returns parsed JSON."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment variables")
    if len(papers) < MIN_PAPERS_PER_POST:
        raise ValueError(f"Need at least {MIN_PAPERS_PER_POST} papers, got {len(papers)}")

    papers_text = prepare_papers_for_prompt(papers)
    system_prompt = SYSTEM_PROMPT_TR if lang == "tr" else SYSTEM_PROMPT_EN

    user_prompt = f"""Here are {len(papers)} recent papers in aerospace/hypersonic research. Analyze them according to your instructions.

{papers_text}"""

    # Security fix: API key in header instead of URL query param
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }

    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": GEMINI_MAX_TOKENS,
            "responseMimeType": "application/json"
        }
    }

    lang_label = "EN" if lang == "en" else "TR"
    print(f"\n🧠 [{GEMINI_MODEL}] Generating {lang_label} analysis from {len(papers)} papers...")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
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

            # Validate required fields
            for field in ["title", "overview", "papers", "tags", "trends"]:
                if field not in result:
                    print(f"   ⚠️ Missing field: {field}")
                    return None

            print(f"   ✅ Title: {result['title']}")
            print(f"   ✅ Papers analyzed: {len(result['papers'])}")
            print(f"   ✅ Tags: {', '.join(result['tags'])}")
            return result

        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"   ⚠️ Gemini error: {e}")
            return None
    return None


def generate_hugo_post(gemini_output: dict, papers: list, lang: str = "en") -> str:
    """Generate a professional intelligence briefing Hugo markdown post."""
    today = datetime.now().strftime("%Y-%m-%d")
    tags_yaml = "\n".join([f'  - "{tag}"' for tag in gemini_output["tags"]])
    badges = PAPER_TYPE_BADGES_TR if lang == "tr" else PAPER_TYPE_BADGES

    # Labels
    if lang == "tr":
        lbl_overview = "İstihbarat Özeti"
        lbl_trends = "Araştırma Trendleri"
        lbl_analysis = "Makale Analizi"
        lbl_type = "Tip"
        lbl_relevance = "İlgililik"
        lbl_findings = "Temel Bulgular"
        lbl_numbers = "Temel Sayılar"
        lbl_methodology = "Metodoloji Detayları"
        lbl_matters = "Neden Önemli"
        lbl_references = "Kaynaklar"
        lbl_connection = "Bağlantı"
    else:
        lbl_overview = "Intelligence Overview"
        lbl_trends = "Research Trends"
        lbl_analysis = "Paper Analysis"
        lbl_type = "Type"
        lbl_relevance = "Relevance"
        lbl_findings = "Key Findings"
        lbl_numbers = "Key Numbers"
        lbl_methodology = "Methodology Details"
        lbl_matters = "Why This Matters"
        lbl_references = "References"
        lbl_connection = "Connection"

    # Build overview section
    overview = gemini_output.get("overview", "")
    trends = gemini_output.get("trends", "")

    # Build paper analysis sections
    paper_sections = []
    for i, p in enumerate(gemini_output.get("papers", []), 1):
        ptype = p.get("paper_type", "numerical_cfd")
        badge = badges.get(ptype, f"📄 {ptype}")
        score = p.get("relevance_score", 0)
        connection = p.get("connection", "")

        section = f"""### {i}. {p.get('title', 'Untitled')}
**{lbl_type}:** {badge} | **{lbl_relevance}:** {score}/100

> **{p.get('one_liner', '')}**

**{lbl_findings}:**
{p.get('key_findings', 'N/A')}

**{lbl_numbers}:** {p.get('key_numbers', 'N/A')}

<details>
<summary><strong>{lbl_methodology}</strong></summary>

{p.get('methodology', 'N/A')}

</details>

> **{lbl_matters}:** {p.get('why_this_matters', 'N/A')}"""

        if connection:
            section += f"\n\n*{lbl_connection}: {connection}*"

        paper_sections.append(section)

    papers_content = "\n\n---\n\n".join(paper_sections)

    # Build references
    references = []
    for i, paper in enumerate(papers, 1):
        author_str = ", ".join(paper.get("authors", [])[:3])
        if len(paper.get("authors", [])) > 3:
            author_str += " et al."
        ref = f'{i}. {author_str}, "{paper["title"]}," *{paper["journal"]}*, {paper.get("date", "2026")}.'
        if paper.get("url"):
            ref += f' [Link]({paper["url"]})'
        references.append(ref)

    summary_text = overview[:150].rsplit(' ', 1)[0] if len(overview) > 150 else overview

    return f"""---
title: "{gemini_output['title']}"
date: {today}
tags:
{tags_yaml}
summary: "{summary_text}..."
draft: false
papers_count: {len(papers)}
ShowToc: true
TocOpen: false
---

## {lbl_overview}

{overview}

> **{lbl_trends}:** {trends}

---

## {lbl_analysis}

{papers_content}

---

## {lbl_references}

{chr(10).join(references)}
"""


def generate_filename(title: str, lang: str = "en") -> str:
    """Generate a URL-friendly filename: {date}-{slug}.{lang}.md"""
    today = datetime.now().strftime("%Y-%m-%d")
    clean = title.lower()
    # Remove non-alphanumeric (keep spaces for splitting)
    clean = re.sub(r"[^a-z0-9\s]", "", clean)
    clean = "-".join(clean.split()[:6])
    return f"{today}-{clean}.{lang}.md"


def run_brain(papers: list) -> dict:
    """
    Full brain pipeline: generate bilingual analysis.
    Returns dict with keys: filename_base, en, tr
    Each language entry has: filename, content, gemini_output
    """
    results = {}

    for lang in LANGUAGES:
        gemini_output = call_gemini(papers, lang=lang)
        if not gemini_output:
            print(f"   ⚠️ Failed to generate {lang.upper()} analysis")
            continue

        post_content = generate_hugo_post(gemini_output, papers, lang=lang)
        # Use EN title for filename consistency
        title_for_filename = gemini_output["title"] if lang == "en" else results.get("en", {}).get("gemini_output", {}).get("title", gemini_output["title"])
        filename = generate_filename(title_for_filename, lang=lang)

        results[lang] = {
            "filename": filename,
            "content": post_content,
            "gemini_output": gemini_output,
        }
        print(f"\n📄 Generated {lang.upper()} post: {filename}")

    if not results:
        return None

    # Derive filename_base (without lang suffix)
    en_data = results.get("en", {})
    if en_data:
        base = en_data["filename"].replace(".en.md", "")
    else:
        first = next(iter(results.values()))
        base = first["filename"].rsplit(".", 2)[0]

    results["filename_base"] = base
    return results


if __name__ == "__main__":
    import os
    if os.path.exists("latest_hunt.json"):
        with open("latest_hunt.json") as f:
            papers = json.load(f)
        result = run_brain(papers)
        if result:
            for lang in LANGUAGES:
                if lang in result:
                    print(f"\n{'=' * 60}")
                    print(f"  {lang.upper()} POST")
                    print(f"{'=' * 60}")
                    print(result[lang]["content"])
    else:
        print("No latest_hunt.json found. Run hunter.py first.")
