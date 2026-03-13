"""
AeroSentinel Brain
Sends a single paper abstract to Gemini API for professional research analysis.
Produces structured, bilingual (EN/TR) output ready for Hugo publishing.
"""
import json
import re
import requests
import time
from datetime import datetime

from src.config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS,
    LANGUAGES, CURATED_TAGS
)

# ──────────────────────────────────────────────
#  SYSTEM PROMPTS
# ──────────────────────────────────────────────

SYSTEM_PROMPT_EN = """You are a senior aerospace research analyst specializing in missile aerothermodynamics, hypersonic flow physics, and AI/ML applications in CFD.

Your domain: "Prediction of Aerodynamic Heating on High-Speed Missiles Using Gaussian Process Based Surrogate Models"

Your task is to analyze the following academic paper and produce a structured single-paper review.

INSTRUCTIONS:

1. RELEVANCE SCORING (0-100): Score the paper based on relevance to the core focus above.
   Scoring rubric:
   - 90-100: GP surrogates for aerodynamic heating prediction
   - 80-89: ML/DL methods for aerothermodynamics
   - 70-79: Non-ML aerothermodynamics (CFD, experimental heating)
   - 50-69: Broader hypersonics/supersonic without heating focus
   - 30-49: General aerospace CFD, tangentially related
   - 0-29: Unrelated to thesis domain

2. PAPER TYPE CLASSIFICATION: Classify the paper as exactly one of:
   ml_heating | ml_aerodynamics | ml_transition | numerical_cfd | experimental | analytical | review | multi_method | thesis

3. SUMMARY: Write like a knowledgeable colleague explaining the paper, not like a structured report. No bullet points, no section headers within the summary. Just clear, direct prose. Include specific numbers where available (Mach ranges, RMSE, speedup factors).
   - First paragraph: what the paper does and the approach taken.
   - Second paragraph: key results and specific numbers.
   - Third paragraph (optional): significance for the aerothermodynamics community.

4. TONE: Technical but accessible. Assume the reader understands M > 5 physics. Direct and honest. BANNED PHRASES (never use these): "groundbreaking", "revolutionary", "delves into", "fascinating", "paving the way", "landscape", "in the realm of", "a testament to", "sheds light on", "pivotal", "underscores", "cutting-edge", "novel approach", "it is worth noting", "notably", "showcases", "leverages", "utilizing", "harnesses", "game-changing", "paradigm shift", "robust" (as praise), "comprehensive study", "innovative".

5. MISSING ABSTRACTS: Papers marked with "[NO ABSTRACT]" — provide only a brief title-based classification. Do not attempt detailed analysis or pad with speculation. Set summary to "Abstract unavailable — classification based on title only."

6. TAGS: Select 3-5 tags from this list ONLY:
{tag_vocabulary}
Tags must ALWAYS be in English regardless of output language.

7. BLOG TITLE: Create a blog-style post title (max 12 words). This is NOT the paper's original title — write a catchy, informative headline.

8. OUTPUT FORMAT: Return ONLY a raw JSON object (no markdown fences, no explanation). The JSON must match this exact schema:
{{
  "title": "Blog-style post title (max 12 words, not the paper's original title)",
  "paper_title": "Exact original paper title",
  "authors": "Author string",
  "paper_type": "ml_heating | ml_aerodynamics | ...",
  "relevance_score": 85,
  "summary": "2-3 paragraphs of natural flowing prose",
  "tags": ["tag1", "tag2", "tag3"]
}}"""

SYSTEM_PROMPT_TR = """Sen fuze aerotermodinamigi, hipersonik akis fizigi ve HAD'de yapay zeka uygulamalari konusunda uzmanlasmus kidemli bir havacilik arastirma analistisin.

Arastirma alanin: "Yuksek Hizli Fuzelerde Aerodinamik Isinmanin Gauss Sureci Tabanli Vekil Modeller Kullanilarak Tahmini"

Gorevin, asagidaki akademik makaleyi analiz edip yapilandirilmis bir tek-makale incelemesi uretmek.

TALIMATLAR:

1. ILGILILIK PUANLAMASI (0-100): Makaleyi yukaridaki temel odaga gore puanla.
   Puanlama kilavuzu:
   - 90-100: Aerodinamik isinma tahmini icin GP vekil modelleri
   - 80-89: Aerotermodinamik icin MO/DO yontemleri
   - 70-79: MO olmayan aerotermodinamik (HAD, deneysel isinma)
   - 50-69: Isinma odagi olmayan genis hipersonik/supersonik
   - 30-49: Genel havacilik HAD, tegetsel iliskili
   - 0-29: Tez alaniyla ilgisiz

2. MAKALE TIPI SINIFLANDIRMASI: Makaleyi tam olarak birini sec:
   ml_heating | ml_aerodynamics | ml_transition | numerical_cfd | experimental | analytical | review | multi_method | thesis

3. OZET: Makaleyi bilgili bir meslektasin anlatir gibi yaz, yapilandirilmis bir rapor gibi degil. Ozet icinde madde isaretleri yok, bolum basliklari yok. Sadece acik, dogrudan duz yazi. Mevcut oldugunca belirli sayilar ekle (Mach araliklari, RMSE, hizlanma faktorleri).
   - Birinci paragraf: makalenin ne yaptigini ve alinan yaklasimi anlat.
   - Ikinci paragraf: temel sonuclar ve belirli sayilar.
   - Ucuncu paragraf (istege bagli): aerotermodinamik toplulugu icin onemi.

4. TON: Teknik ama anlasilir. Okuyucunun M > 5 fizigini anladigini varsay. Dogrudan ve durust. YASAKLI IFADELER (bunlari asla kullanma): "cigiracici", "devrimci", "derinlemesine inceliyor", "buyuleyici", "yol aciyor", "peyzaj", "alaninda", "bir kaniti", "isik tutuyor", "kritik oneme sahip", "alti ciziyor", "son teknoloji", "yenilikci yaklasim", "belirtmek gerekir ki", "ozellikle", "sergiliyor", "kullaniyor", "yararlanarak", "oyun degistirici", "paradigma degisimi", "kapsamli calisma", "inovatif".

5. EKSIK OZETLER: "[NO ABSTRACT]" ile isaretlenmis makaleler — sadece basliga dayali kisa bir siniflandirma yap. Detayli analiz yapma veya spekülasyonla doldurma. Ozeti "Ozet mevcut degil — siniflandirma yalnizca basliga dayalidir." olarak ayarla.

6. ETIKETLER: SADECE bu listeden 3-5 etiket sec:
{tag_vocabulary}
Etiketler DAIMA Ingilizce olmalidir.

7. BLOG BASLIGI: Blog tarzi bir yazi basligi olustur (en fazla 12 kelime, Turkce). Bu makalenin orijinal basligi DEGIL — akici, bilgilendirici bir baslik yaz.

8. CIKTI FORMATI: SADECE ham JSON nesnesi dondur (markdown citi yok, aciklama yok). JSON tam olarak su semaya uymali:
{{
  "title": "Blog tarzi yazi basligi (en fazla 12 kelime, Turkce)",
  "paper_title": "Makalenin orijinal Ingilizce basligi",
  "authors": "Yazar dizesi",
  "paper_type": "ml_heating | ml_aerodynamics | ...",
  "relevance_score": 85,
  "summary": "2-3 paragraflik dogal akan duz yazi (Turkce)",
  "tags": ["tag1", "tag2", "tag3"]
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
    "thesis": "🎓 Thesis/Dissertation",
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
    "thesis": "🎓 Tez/Doktora",
}


def _build_tag_instruction() -> str:
    """Format CURATED_TAGS into a readable prompt section."""
    lines = []
    for category, tags in CURATED_TAGS.items():
        label = category.replace("_", " ").title()
        lines.append(f"  {label}: {', '.join(tags)}")
    return "\n".join(lines)


# Anti-slop patterns — strip AI-generated filler phrases from output
_SLOP_PATTERNS = [
    r'\bgroundbreaking\b', r'\brevolutionary\b', r'\bdelves?\s+into\b',
    r'\bfascinating\b', r'\bpaving\s+the\s+way\b', r'\bin\s+the\s+realm\s+of\b',
    r'\ba\s+testament\s+to\b', r'\bsheds?\s+light\s+on\b', r'\bpivotal\b',
    r'\bunderscore[sd]?\b', r'\bcutting[\s-]edge\b', r'\bnovel\s+approach\b',
    r'\bit\s+is\s+worth\s+noting\b', r'\bshowcase[sd]?\b', r'\bleverages?\b',
    r'\bharnesses?\b', r'\bgame[\s-]changing\b', r'\bparadigm\s+shift\b',
    r'\binnovative\b',
]
_SLOP_RE = re.compile('|'.join(_SLOP_PATTERNS), re.IGNORECASE)


def clean_slop(text: str) -> str:
    """Remove AI-generated filler phrases from text."""
    cleaned = _SLOP_RE.sub('', text)
    # Clean up double spaces left behind
    cleaned = re.sub(r'  +', ' ', cleaned)
    # Clean up orphaned commas/periods
    cleaned = re.sub(r'\s+,', ',', cleaned)
    cleaned = re.sub(r'\s+\.', '.', cleaned)
    return cleaned.strip()


def build_system_prompt(lang: str = "en") -> str:
    """Return the full system prompt with embedded tag vocabulary."""
    tag_vocabulary = _build_tag_instruction()
    template = SYSTEM_PROMPT_TR if lang == "tr" else SYSTEM_PROMPT_EN
    return template.format(tag_vocabulary=tag_vocabulary)


# ──────────────────────────────────────────────
#  FEW-SHOT EXAMPLE (teaches Gemini the desired output style)
# ──────────────────────────────────────────────

FEW_SHOT_EXAMPLE = """{
  "title": "Gaussian Process Surrogates Slash Hypersonic Heat Flux Computation Time",
  "paper_title": "Multi-fidelity Gaussian Process Surrogate for Rapid Aerodynamic Heating Prediction on Hypersonic Vehicles",
  "authors": "Chen et al.",
  "paper_type": "ml_heating",
  "relevance_score": 92,
  "summary": "Chen and colleagues present a multi-fidelity Gaussian process framework that fuses coarse-grid RANS solutions with sparse high-fidelity DNS data to predict surface heat flux distributions on a blunted cone-cylinder at Mach 8. The GP model uses a deep kernel built on the vehicle's surface coordinates and local flow parameters, trained on 120 low-fidelity and 15 high-fidelity CFD snapshots spanning angle-of-attack sweeps from 0 to 15 degrees.\\n\\nThe surrogate achieves an RMSE of 3.2% against held-out DNS data while running 4,200x faster than a single high-fidelity simulation. Stagnation-region predictions stay within 5% of DNS across the entire angle-of-attack envelope, and the model generalizes to interpolated flight conditions not seen during training. Wall-clock time for a full heating map drops from 14 hours (DNS) to 12 seconds.\\n\\nThe multi-fidelity strategy is the real contribution here — single-fidelity GP trained only on RANS data showed 11% RMSE in the stagnation region, confirming that the low-to-high fidelity bridge matters. This is directly applicable to trajectory optimization loops where thousands of heating evaluations are needed.",
  "tags": ["Gaussian Process Surrogates", "Heat Flux Prediction", "Multi-Fidelity Modeling", "Hypersonic Aerodynamics", "Missile Aerothermodynamics"]
}"""


def prepare_paper_for_prompt(paper: dict) -> str:
    """Format a single paper's data into a clean text block for the LLM."""
    author_str = ", ".join(paper.get("authors", [])[:4])
    if len(paper.get("authors", [])) > 4:
        author_str += " et al."
    return f"""Title: {paper.get('title', 'N/A')}
Authors: {author_str}
Journal: {paper.get('journal', 'N/A')}
Date: {paper.get('date', 'N/A')}
DOI: {paper.get('doi', 'N/A')}
Abstract: {paper.get('abstract', 'No abstract available.')}"""


def call_gemini(paper: dict, lang: str = "en") -> tuple:
    """Call Gemini API to generate structured single-paper analysis.
    Returns (parsed_json_dict, token_usage_dict) or (None, None) on error."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment variables")

    paper_text = prepare_paper_for_prompt(paper)
    system_prompt = build_system_prompt(lang)

    user_prompt = f"""Here is an example of an excellent analysis output for reference:

{FEW_SHOT_EXAMPLE}

Now analyze this new paper:

{paper_text}"""

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
    paper_title = paper.get("title", "Unknown")
    print(f"\n🧠 [{GEMINI_MODEL}] Generating {lang_label} analysis for: {paper_title}...")

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
                return None, None

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
            for field in ["title", "paper_title", "paper_type", "relevance_score", "summary", "tags"]:
                if field not in result:
                    print(f"   ⚠️ Missing field: {field}")
                    if attempt < max_retries - 1:
                        print(f"   ⏳ Retrying (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(5)
                        break
                    return None, None
            else:
                # Apply anti-slop cleaning to summary
                result["summary"] = clean_slop(result["summary"])

                # Extract token usage from response metadata
                usage_meta = response.get("usageMetadata", {})
                token_usage = {
                    "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                    "candidates_tokens": usage_meta.get("candidatesTokenCount", 0),
                    "total_tokens": usage_meta.get("totalTokenCount", 0),
                }

                print(f"   ✅ Title: {result['title']}")
                print(f"   ✅ Type: {result['paper_type']} | Relevance: {result['relevance_score']}/100")
                print(f"   ✅ Tags: {', '.join(result['tags'])}")
                print(f"   ✅ Tokens: {token_usage['total_tokens']} (prompt: {token_usage['prompt_tokens']}, output: {token_usage['candidates_tokens']})")
                return result, token_usage
            continue

        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON parse error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return None, None
        except Exception as e:
            print(f"   ⚠️ Gemini error: {e}")
            return None, None
    return None, None


def generate_hugo_post(gemini_output: dict, paper: dict, lang: str = "en") -> str:
    """Generate a single-paper review Hugo markdown post."""
    today = datetime.now().strftime("%Y-%m-%d")
    tags_yaml = "\n".join([f'  - "{tag}"' for tag in gemini_output["tags"]])
    badges = PAPER_TYPE_BADGES_TR if lang == "tr" else PAPER_TYPE_BADGES

    ptype = gemini_output.get("paper_type", "numerical_cfd")
    badge = badges.get(ptype, f"📄 {ptype}")
    score = gemini_output.get("relevance_score", 0)
    summary = gemini_output.get("summary", "")

    # Build summary preview for frontmatter (first ~150 chars)
    summary_text = summary[:150].rsplit(' ', 1)[0] if len(summary) > 150 else summary
    # Remove newlines from frontmatter summary
    summary_text = summary_text.replace("\n", " ").strip()

    # Build reference
    author_str = ", ".join(paper.get("authors", [])[:3])
    if len(paper.get("authors", [])) > 3:
        author_str += " et al."
    journal = paper.get("journal", "N/A")
    date = paper.get("date", "2026")
    paper_title = gemini_output.get("paper_title", paper.get("title", "Untitled"))
    ref = f'1. {author_str}, "{paper_title}," *{journal}*, {date}.'
    if paper.get("url"):
        ref += f' [Link]({paper["url"]})'

    # Attribution footer
    if lang == "tr":
        attribution = "*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v3.0.0 tarafindan duzenlenmistir.*"
        lbl_reference = "Kaynak"
    else:
        attribution = "*This paper review was generated by [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) and curated by AeroSentinel v3.0.0.*"
        lbl_reference = "Reference"

    post = f"""---
title: "{gemini_output['title']}"
date: {today}
tags:
{tags_yaml}
summary: "{summary_text}..."
draft: false
paper_type: "{ptype}"
relevance_score: {score}
ai_model: "Gemini 2.5 Flash"
---

**Type:** {badge} | **Relevance:** {score}/100

{summary}

---

{attribution}

---

## {lbl_reference}

{ref}
"""
    return post


def generate_filename(title: str, lang: str = "en") -> str:
    """Generate a URL-friendly filename: {date}-{slug}.{lang}.md"""
    today = datetime.now().strftime("%Y-%m-%d")
    clean = title.lower()
    # Remove non-alphanumeric (keep spaces for splitting)
    clean = re.sub(r"[^a-z0-9\s]", "", clean)
    clean = "-".join(clean.split()[:6])
    return f"{today}-{clean}.{lang}.md"


def run_brain(papers: list) -> list:
    """
    Full brain pipeline: generate bilingual analysis for each paper individually.
    Returns list of dicts, each with keys: filename_base, en, tr, paper, token_usage
    Each language entry has: filename, content, gemini_output
    Returns empty list on total failure.
    """
    all_results = []

    for paper in papers:
        paper_title = paper.get("title", "Unknown")
        print(f"\n{'=' * 60}")
        print(f"  Processing: {paper_title}")
        print(f"{'=' * 60}")

        result = {}
        token_usage = {}

        for lang in LANGUAGES:
            gemini_output, lang_tokens = call_gemini(paper, lang=lang)
            if not gemini_output:
                print(f"   ⚠️ Failed to generate {lang.upper()} analysis for: {paper_title}")
                continue

            if lang_tokens:
                token_usage[lang] = lang_tokens

            post_content = generate_hugo_post(gemini_output, paper, lang=lang)
            # Use EN title for filename consistency
            title_for_filename = gemini_output["title"] if lang == "en" else result.get("en", {}).get("gemini_output", {}).get("title", gemini_output["title"])
            filename = generate_filename(title_for_filename, lang=lang)

            result[lang] = {
                "filename": filename,
                "content": post_content,
                "gemini_output": gemini_output,
            }
            print(f"\n📄 Generated {lang.upper()} post: {filename}")

        if not result:
            print(f"   ⚠️ Skipping paper (no analysis generated): {paper_title}")
            continue

        # Derive filename_base (without lang suffix)
        en_data = result.get("en", {})
        if en_data:
            base = en_data["filename"].replace(".en.md", "")
        else:
            first = next(iter(result.values()))
            base = first["filename"].rsplit(".", 2)[0]

        result["filename_base"] = base
        result["paper"] = paper
        if token_usage:
            result["token_usage"] = token_usage

        all_results.append(result)

    return all_results


if __name__ == "__main__":
    import os
    if os.path.exists("latest_hunt.json"):
        with open("latest_hunt.json") as f:
            papers = json.load(f)
        results = run_brain(papers)
        if results:
            for result in results:
                for lang in LANGUAGES:
                    if lang in result:
                        print(f"\n{'=' * 60}")
                        print(f"  {lang.upper()} POST: {result[lang]['filename']}")
                        print(f"{'=' * 60}")
                        print(result[lang]["content"])
        else:
            print("No results generated.")
    else:
        print("No latest_hunt.json found. Run hunter.py first.")
