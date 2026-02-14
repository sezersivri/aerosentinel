"""
AeroSentinel Brain
Sends paper abstracts to Gemini API for professional research digest analysis.
Produces structured, bilingual (EN/TR) output ready for Hugo publishing.
"""
import json
import re
import requests
import time
from datetime import datetime

from src.config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS,
    MIN_PAPERS_PER_POST, LANGUAGES, CURATED_TAGS
)

# ──────────────────────────────────────────────
#  SYSTEM PROMPTS
# ──────────────────────────────────────────────

SYSTEM_PROMPT_EN = """You are a senior aerospace research analyst specializing in missile aerothermodynamics, hypersonic flow physics, and AI/ML applications in CFD.

Your domain: "Prediction of Aerodynamic Heating on High-Speed Missiles Using Gaussian Process Based Surrogate Models"

Your task is to analyze the following academic papers and produce a structured research digest.

INSTRUCTIONS:

1. RELEVANCE SCORING (0-100): Score each paper based on relevance to the thesis domain above.
   Scoring rubric:
   - 90-100: GP surrogates for aerodynamic heating prediction
   - 80-89: ML/DL methods for aerothermodynamics
   - 70-79: Non-ML aerothermodynamics (CFD, experimental heating)
   - 50-69: Broader hypersonics/supersonic without heating focus
   - 30-49: General aerospace CFD, tangentially related
   - 0-29: Unrelated to thesis domain

2. PAPER TYPE CLASSIFICATION: Classify each paper as exactly one of:
   ml_heating | ml_aerodynamics | ml_transition | numerical_cfd | experimental | analytical | review | multi_method

3. HARD NUMBERS: Extract specific quantitative results — RMSE percentages, speedup factors, Mach number ranges, heat flux values, temperature ranges, geometry types. If a paper lacks specifics, say so honestly.

4. CROSS-PAPER CONNECTIONS: Identify how papers relate to each other — complementary methods, contradicting results, building on similar foundations.

5. TONE: Technical but accessible. Assume the reader understands M > 5 physics. No fluff, no "groundbreaking" or "revolutionary." Direct and honest.

6. TAGS: Select 4-7 tags from this list ONLY:
{tag_vocabulary}
Tags must ALWAYS be in English regardless of output language.

7. OUTPUT FORMAT: Return ONLY a raw JSON object (no markdown fences, no explanation). The JSON must match this exact schema:
{{
  "title": "Briefing title (max 15 words)",
  "overview": "3-4 sentence strategic overview connecting papers thematically",
  "papers": [
    {{
      "title": "Exact paper title",
      "authors": "Author string",
      "paper_type": "ml_heating | ml_aerodynamics | ml_transition | numerical_cfd | experimental | analytical | review | multi_method",
      "relevance_score": 85,
      "one_liner": "Single sentence core contribution",
      "key_findings": "2-3 sentences with specific numerical results (RMSE, Mach range, speedup)",
      "methodology": "1-2 sentences on approach (solver, turbulence model, ML architecture)",
      "why_this_matters": "2 sentences on practical value for missile design / aerospace engineering",
      "key_numbers": "Formatted string: Mach X-Y, RMSE ±Z%, speedup Nx, geometry type",
      "connection": "How this relates to other papers in this batch (if applicable)"
    }}
  ],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "trends": "2-3 sentences on what these papers collectively signal about the field"
}}"""

SYSTEM_PROMPT_TR = """Sen füze aerotermodinamiği, hipersonik akış fiziği ve CFD'de yapay zeka uygulamaları konusunda uzmanlaşmış kıdemli bir havacılık araştırma analistisisin.

Araştırma alanın: "Yüksek Hızlı Füzelerde Aerodinamik Isınmanın Gauss Süreci Tabanlı Vekil Modeller Kullanılarak Tahmini"

Görevin, aşağıdaki akademik makaleleri analiz edip yapılandırılmış bir araştırma özeti üretmek.

TALİMATLAR:

1. İLGİLİLİK PUANLAMASI (0-100): Her makaleyi yukarıdaki tez alanına göre puanla.
   Puanlama kılavuzu:
   - 90-100: Aerodinamik ısınma tahmini için GP vekil modelleri
   - 80-89: Aerotermodinamik için MÖ/DÖ yöntemleri
   - 70-79: MÖ olmayan aerotermodinamik (HAD, deneysel ısınma)
   - 50-69: Isınma odağı olmayan geniş hipersonik/süpersonik
   - 30-49: Genel havacılık HAD, teğetsel ilişkili
   - 0-29: Tez alanıyla ilgisiz

2. MAKALE TİPİ SINIFLANDIRMASI: Her makaleyi tam olarak birini seç:
   ml_heating | ml_aerodynamics | ml_transition | numerical_cfd | experimental | analytical | review | multi_method

3. KESİN SAYILAR: Belirli nicel sonuçları çıkar — RMSE yüzdeleri, hızlanma faktörleri, Mach sayısı aralıkları, ısı akısı değerleri, sıcaklık aralıkları, geometri tipleri. Makalede spesifik değer yoksa bunu dürüstçe belirt.

4. MAKALELER ARASI BAĞLANTILAR: Makalelerin birbirleriyle nasıl ilişkili olduğunu belirle — tamamlayıcı yöntemler, çelişen sonuçlar, benzer temeller üzerine inşa.

5. TON: Teknik ama anlaşılır. Okuyucunun M > 5 fiziğini anladığını varsay. Abartılı ifadeler yok, doğrudan ve dürüst.

6. ÖNEMLİ: Tüm analiz metni TÜRKÇE olmalıdır. Sadece makale başlıkları (title alanı) İngilizce kalmalıdır.

7. ETİKETLER: SADECE bu listeden 4-7 etiket seç:
{tag_vocabulary}
Etiketler DAIMA İngilizce olmalıdır.

8. ÇIKTI FORMATI: SADECE ham JSON nesnesi döndür (markdown çiti yok, açıklama yok). JSON tam olarak şu şemaya uymalı:
{{
  "title": "Brifing başlığı (en fazla 15 kelime, Türkçe)",
  "overview": "3-4 cümlelik stratejik genel bakış, makaleleri tematik olarak bağlayan (Türkçe)",
  "papers": [
    {{
      "title": "Makalenin orijinal İngilizce başlığı",
      "authors": "Yazar dizesi",
      "paper_type": "ml_heating | ml_aerodynamics | ml_transition | numerical_cfd | experimental | analytical | review | multi_method",
      "relevance_score": 85,
      "one_liner": "Tek cümlelik temel katkı (Türkçe)",
      "key_findings": "Spesifik sayısal sonuçlarla 2-3 cümle (Türkçe)",
      "methodology": "Yaklaşım hakkında 1-2 cümle (Türkçe)",
      "why_this_matters": "Füze tasarımı / havacılık mühendisliği için pratik değer hakkında 2 cümle (Türkçe)",
      "key_numbers": "Biçimlendirilmiş: Mach X-Y, RMSE ±Z%, hızlanma Nx, geometri tipi",
      "connection": "Bu makalenin gruptaki diğer makalelerle ilişkisi (Türkçe)"
    }}
  ],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "trends": "Bu makalelerin alan hakkında toplu olarak ne işaret ettiğine dair 2-3 cümle (Türkçe)"
}}"""


# ──────────────────────────────────────────────
#  PAPER TYPE BADGES
# ──────────────────────────────────────────────

PAPER_TYPE_BADGES = {
    "ml_heating": "🤖 ML/Heating Prediction",
    "ml_aerodynamics": "🤖 ML/Aerodynamics",
    "ml_transition": "🤖 ML/Transition",
    "numerical_cfd": "💻 Numerical/CFD",
    "experimental": "🧪 Experimental",
    "analytical": "📐 Analytical",
    "review": "📚 Review",
    "multi_method": "🔬 Multi-Method",
}

PAPER_TYPE_BADGES_TR = {
    "ml_heating": "🤖 MO/Isinma Tahmini",
    "ml_aerodynamics": "🤖 MO/Aerodinamik",
    "ml_transition": "🤖 MO/Gecis Tahmini",
    "numerical_cfd": "💻 Sayisal/HAD",
    "experimental": "🧪 Deneysel",
    "analytical": "📐 Analitik",
    "review": "📚 Derleme",
    "multi_method": "🔬 Coklu Yontem",
}


def _build_tag_instruction() -> str:
    """Format CURATED_TAGS into a readable prompt section."""
    lines = []
    for category, tags in CURATED_TAGS.items():
        label = category.replace("_", " ").title()
        lines.append(f"  {label}: {', '.join(tags)}")
    return "\n".join(lines)


def build_system_prompt(lang: str = "en") -> str:
    """Return the full system prompt with embedded tag vocabulary."""
    tag_vocabulary = _build_tag_instruction()
    template = SYSTEM_PROMPT_TR if lang == "tr" else SYSTEM_PROMPT_EN
    return template.format(tag_vocabulary=tag_vocabulary)


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
    system_prompt = build_system_prompt(lang)

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
    """Generate a professional research digest Hugo markdown post."""
    today = datetime.now().strftime("%Y-%m-%d")
    tags_yaml = "\n".join([f'  - "{tag}"' for tag in gemini_output["tags"]])
    badges = PAPER_TYPE_BADGES_TR if lang == "tr" else PAPER_TYPE_BADGES

    # Labels
    if lang == "tr":
        lbl_overview = "Araştırma Özeti"
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
        lbl_overview = "Research Overview"
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
