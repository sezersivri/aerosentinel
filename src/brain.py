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

Your task is to analyze the following academic papers and produce a TWO-TIER structured research digest.

CORE FOCUS — papers that get full individual analysis:
  A) Aerodynamic heating (prediction, measurement, simulation of surface heat flux, stagnation heating, thermal protection)
  B) AI/ML methods applied to aerodynamics (surrogate models, neural networks for CFD, Gaussian process regression, data-driven aerodynamic prediction)

PERIPHERAL — everything else (broader CFD, general aerospace, non-heating hypersonics, etc.)

INSTRUCTIONS:

1. RELEVANCE SCORING (0-100): Score each paper based on relevance to the core focus above.
   Scoring rubric:
   - 90-100: GP surrogates for aerodynamic heating prediction
   - 80-89: ML/DL methods for aerothermodynamics
   - 70-79: Non-ML aerothermodynamics (CFD, experimental heating)
   - 50-69: Broader hypersonics/supersonic without heating focus
   - 30-49: General aerospace CFD, tangentially related
   - 0-29: Unrelated to thesis domain

2. CLASSIFY each paper as "core" or "peripheral":
   - "core" = directly about aerodynamic heating/thermal prediction OR AI/ML methods applied to aerodynamics
   - "peripheral" = everything else

3. PAPER TYPE CLASSIFICATION: Classify each paper as exactly one of:
   ml_heating | ml_aerodynamics | ml_transition | numerical_cfd | experimental | analytical | review | multi_method | thesis

4. For CORE papers: Provide full structured analysis with hard numbers, methodology, and practical significance.

5. For PERIPHERAL papers: Provide a brief 1-2 sentence summary with key numbers.

6. PERIPHERAL NARRATIVE: Write a 1-2 paragraph flowing academic narrative that synthesizes ALL peripheral papers. Use in-text citations with reference numbers matching the paper order (e.g., "[3]", "[5]"). Write it like a literature review section — connecting themes, contrasting approaches, noting complementary findings. Technical but accessible. No fluff.

7. CROSS-PAPER CONNECTIONS: For core papers, identify how they relate to each other.

8. TONE: Technical but accessible. Assume the reader understands M > 5 physics. Direct and honest. BANNED PHRASES (never use these): "groundbreaking", "revolutionary", "delves into", "fascinating", "paving the way", "landscape", "in the realm of", "a testament to", "sheds light on", "pivotal", "underscores", "cutting-edge", "novel approach", "it is worth noting", "notably", "showcases", "leverages", "utilizing", "harnesses", "game-changing", "paradigm shift", "robust" (as praise), "comprehensive study", "innovative".

9. MISSING ABSTRACTS: Papers marked with "[NO ABSTRACT]" — provide only a brief title-based classification. Do not attempt detailed analysis or pad with speculation. State "Abstract unavailable — classification based on title only."

10. TAGS: Select 4-7 tags from this list ONLY:
{tag_vocabulary}
Tags must ALWAYS be in English regardless of output language.

11. CRITICAL SCHEMA REQUIREMENT: You MUST use "core_papers" and "peripheral_papers" keys in your JSON output. NEVER use a flat "papers" key. Even if all papers are core or all are peripheral, always use both keys (one may be an empty array).

12. OUTPUT FORMAT: Return ONLY a raw JSON object (no markdown fences, no explanation). The JSON must match this exact schema:
{{
  "title": "Briefing title (max 15 words)",
  "overview": "3-4 sentence strategic overview connecting all papers thematically",
  "core_papers": [
    {{
      "title": "Exact paper title",
      "authors": "Author string",
      "paper_type": "ml_heating | ml_aerodynamics | ...",
      "relevance_score": 85,
      "one_liner": "Single sentence core contribution",
      "key_findings": "2-3 sentences with specific numerical results (RMSE, Mach range, speedup)",
      "methodology": "1-2 sentences on approach (solver, turbulence model, ML architecture)",
      "why_this_matters": "2 sentences on practical value for missile design / aerospace engineering",
      "key_numbers": "Formatted string: Mach X-Y, RMSE ±Z%, speedup Nx, geometry type",
      "connection": "How this relates to other core papers in this batch",
      "limitations": "1-2 sentences on methodological limitations, evidence strength, or scope constraints"
    }}
  ],
  "peripheral_papers": [
    {{
      "title": "Exact paper title",
      "authors": "Author string",
      "paper_type": "numerical_cfd | experimental | ...",
      "relevance_score": 45,
      "brief_summary": "1-2 sentence summary of contribution and key result"
    }}
  ],
  "peripheral_narrative": "1-2 paragraph flowing academic text synthesizing all peripheral papers with [N] in-text citations. Written like a literature review.",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "trends": "2-3 sentences on what these papers collectively signal about the field"
}}"""

SYSTEM_PROMPT_TR = """Sen füze aerotermodinamiği, hipersonik akış fiziği ve CFD'de yapay zeka uygulamaları konusunda uzmanlaşmış kıdemli bir havacılık araştırma analistisisin.

Araştırma alanın: "Yüksek Hızlı Füzelerde Aerodinamik Isınmanın Gauss Süreci Tabanlı Vekil Modeller Kullanılarak Tahmini"

Görevin, aşağıdaki akademik makaleleri analiz edip İKİ KATMANLI yapılandırılmış bir araştırma özeti üretmek.

TEMEL ODAK — tam bireysel analiz yapılacak makaleler:
  A) Aerodinamik ısınma (tahmin, ölçüm, yüzey ısı akısı simülasyonu, durma noktası ısınması, termal koruma)
  B) Aerodinamiğe uygulanan YZ/MÖ yöntemleri (vekil modeller, HAD için sinir ağları, Gauss süreci regresyonu, veri güdümlü aerodinamik tahmin)

ÇEVRESel — diğer her şey (genel HAD, genel havacılık, ısınma odağı olmayan hipersonik vb.)

TALİMATLAR:

1. İLGİLİLİK PUANLAMASI (0-100): Her makaleyi yukarıdaki temel odağa göre puanla.
   Puanlama kılavuzu:
   - 90-100: Aerodinamik ısınma tahmini için GP vekil modelleri
   - 80-89: Aerotermodinamik için MÖ/DÖ yöntemleri
   - 70-79: MÖ olmayan aerotermodinamik (HAD, deneysel ısınma)
   - 50-69: Isınma odağı olmayan geniş hipersonik/süpersonik
   - 30-49: Genel havacılık HAD, teğetsel ilişkili
   - 0-29: Tez alanıyla ilgisiz

2. Her makaleyi "core" veya "peripheral" olarak SINIFLANDIR:
   - "core" = doğrudan aerodinamik ısınma/termal tahmin VEYA aerodinamiğe uygulanan YZ/MÖ yöntemleri
   - "peripheral" = diğer her şey

3. MAKALE TİPİ SINIFLANDIRMASI: Her makaleyi tam olarak birini seç:
   ml_heating | ml_aerodynamics | ml_transition | numerical_cfd | experimental | analytical | review | multi_method | thesis

4. TEMEL makaleler için: Kesin sayılar, metodoloji ve pratik önem ile tam yapılandırılmış analiz sağla.

5. ÇEVRESEL makaleler için: Temel sayılarla kısa 1-2 cümlelik özet sağla.

6. ÇEVRESEL ANLATIM: Tüm çevresel makaleleri sentezleyen 1-2 paragraflık akıcı akademik anlatım yaz. Makale sırasına uygun metin içi atıflar kullan (ör. "[3]", "[5]"). Bir literatür taraması bölümü gibi yaz — temaları bağla, yaklaşımları karşılaştır, tamamlayıcı bulguları belirt.

7. ÖNEMLİ: Tüm analiz metni TÜRKÇE olmalıdır. Sadece makale başlıkları (title alanı) İngilizce kalmalıdır.

8. ETİKETLER: SADECE bu listeden 4-7 etiket seç:
{tag_vocabulary}
Etiketler DAIMA İngilizce olmalıdır.

9. KRİTİK ŞEMA GEREKSİNİMİ: JSON çıktınızda MUTLAKA "core_papers" ve "peripheral_papers" anahtarlarını kullanmalısınız. ASLA düz bir "papers" anahtarı kullanmayın. Tüm makaleler core veya peripheral olsa bile, her iki anahtarı da kullanın (biri boş dizi olabilir).

10. ÇIKTI FORMATI: SADECE ham JSON nesnesi döndür (markdown çiti yok, açıklama yok). JSON tam olarak şu şemaya uymalı:
{{
  "title": "Brifing başlığı (en fazla 15 kelime, Türkçe)",
  "overview": "3-4 cümlelik stratejik genel bakış, tüm makaleleri tematik olarak bağlayan (Türkçe)",
  "core_papers": [
    {{
      "title": "Makalenin orijinal İngilizce başlığı",
      "authors": "Yazar dizesi",
      "paper_type": "ml_heating | ml_aerodynamics | ...",
      "relevance_score": 85,
      "one_liner": "Tek cümlelik temel katkı (Türkçe)",
      "key_findings": "Spesifik sayısal sonuçlarla 2-3 cümle (Türkçe)",
      "methodology": "Yaklaşım hakkında 1-2 cümle (Türkçe)",
      "why_this_matters": "Füze tasarımı / havacılık mühendisliği için pratik değer hakkında 2 cümle (Türkçe)",
      "key_numbers": "Biçimlendirilmiş: Mach X-Y, RMSE ±Z%, hızlanma Nx, geometri tipi",
      "connection": "Bu makalenin gruptaki diğer temel makalelerle ilişkisi (Türkçe)",
      "limitations": "Metodolojik sınırlamalar, kanıt gücü veya kapsam kısıtlamaları hakkında 1-2 cümle (Türkçe)"
    }}
  ],
  "peripheral_papers": [
    {{
      "title": "Makalenin orijinal İngilizce başlığı",
      "authors": "Yazar dizesi",
      "paper_type": "numerical_cfd | experimental | ...",
      "relevance_score": 45,
      "brief_summary": "Katkı ve temel sonucun 1-2 cümlelik özeti (Türkçe)"
    }}
  ],
  "peripheral_narrative": "Tüm çevresel makaleleri [N] metin içi atıflarla sentezleyen 1-2 paragraflık akıcı akademik metin. Literatür taraması gibi yazılmış. (Türkçe)",
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


def call_gemini(papers: list, lang: str = "en") -> tuple:
    """Call Gemini API to generate structured analysis.
    Returns (parsed_json_dict, token_usage_dict) or (None, None) on error."""
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
            for field in ["title", "overview", "tags", "trends"]:
                if field not in result:
                    print(f"   ⚠️ Missing field: {field}")
                    return None, None

            # Enforce two-tier schema — reject old flat "papers" key
            if "core_papers" not in result:
                if "papers" in result and attempt < max_retries - 1:
                    print(f"   ⚠️ Got old flat schema, retrying for two-tier format...")
                    time.sleep(5)
                    continue
                elif "papers" in result:
                    # Last attempt: auto-convert old schema to new
                    print(f"   ⚠️ Converting flat schema to two-tier on final attempt")
                    result["core_papers"] = result.pop("papers")
                    result["peripheral_papers"] = []
                    result["peripheral_narrative"] = ""
                else:
                    print(f"   ⚠️ Missing required field: core_papers")
                    return None, None

            # Extract token usage from response metadata
            usage_meta = response.get("usageMetadata", {})
            token_usage = {
                "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                "candidates_tokens": usage_meta.get("candidatesTokenCount", 0),
                "total_tokens": usage_meta.get("totalTokenCount", 0),
            }

            core_count = len(result.get("core_papers", []))
            periph_count = len(result.get("peripheral_papers", []))
            old_count = len(result.get("papers", []))
            total = core_count + periph_count if core_count else old_count
            print(f"   ✅ Title: {result['title']}")
            if core_count:
                print(f"   ✅ Papers: {core_count} core + {periph_count} peripheral = {total} total")
            else:
                print(f"   ✅ Papers analyzed: {total}")
            print(f"   ✅ Tags: {', '.join(result['tags'])}")
            print(f"   ✅ Tokens: {token_usage['total_tokens']} (prompt: {token_usage['prompt_tokens']}, output: {token_usage['candidates_tokens']})")
            return result, token_usage

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


def generate_hugo_post(gemini_output: dict, papers: list, lang: str = "en") -> str:
    """Generate a professional two-tier research digest Hugo markdown post.

    Tier A (Core): Papers on aerodynamic heating or AI/ML in aerodynamics
                   get full individual analysis sections.
    Tier B (Peripheral): All other papers are synthesized into a flowing
                         academic narrative with in-text citations [N].
    """
    today = datetime.now().strftime("%Y-%m-%d")
    tags_yaml = "\n".join([f'  - "{tag}"' for tag in gemini_output["tags"]])
    badges = PAPER_TYPE_BADGES_TR if lang == "tr" else PAPER_TYPE_BADGES

    # Labels
    if lang == "tr":
        lbl_overview = "Araştırma Özeti"
        lbl_trends = "Araştırma Trendleri"
        lbl_core = "Temel Odak Analizi"
        lbl_context = "Geniş Bağlam"
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
        lbl_core = "Core Analysis"
        lbl_context = "Broader Context"
        lbl_type = "Type"
        lbl_relevance = "Relevance"
        lbl_findings = "Key Findings"
        lbl_numbers = "Key Numbers"
        lbl_methodology = "Methodology Details"
        lbl_matters = "Why This Matters"
        lbl_references = "References"
        lbl_connection = "Connection"

    overview = clean_slop(gemini_output.get("overview", ""))
    trends = clean_slop(gemini_output.get("trends", ""))

    # Detect schema: new two-tier or old flat
    core_papers = gemini_output.get("core_papers", [])
    peripheral_papers = gemini_output.get("peripheral_papers", [])
    peripheral_narrative = gemini_output.get("peripheral_narrative", "")
    if peripheral_narrative:
        peripheral_narrative = clean_slop(peripheral_narrative)

    # Fallback: old flat schema → treat all as core (legacy safety net)
    if not core_papers and "papers" in gemini_output:
        core_papers = gemini_output["papers"]
        print("   ⚠️ WARNING: Using legacy flat schema fallback in Hugo generation")

    # ── Build Core Analysis sections ──
    core_sections = []
    for i, p in enumerate(core_papers, 1):
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

        limitations = p.get("limitations", "")
        if limitations:
            section += f"\n\n> ⚠️ **Limitations:** {limitations}"

        section = clean_slop(section)
        core_sections.append(section)

    core_content = "\n\n---\n\n".join(core_sections) if core_sections else ""

    # ── Build References (core first, then peripheral) ──
    references = []
    ref_num = 1

    for paper in papers:
        # Match paper to core or peripheral by title
        is_core = any(
            cp.get("title", "").lower() == paper.get("title", "").lower()
            for cp in core_papers
        )
        is_peripheral = any(
            pp.get("title", "").lower() == paper.get("title", "").lower()
            for pp in peripheral_papers
        )
        if is_core or is_peripheral or not (core_papers and peripheral_papers):
            author_str = ", ".join(paper.get("authors", [])[:3])
            if len(paper.get("authors", [])) > 3:
                author_str += " et al."
            ref = f'{ref_num}. {author_str}, "{paper["title"]}," *{paper["journal"]}*, {paper.get("date", "2026")}.'
            if paper.get("url"):
                ref += f' [Link]({paper["url"]})'
            references.append(ref)
            ref_num += 1

    # ── Build Broader Context section ──
    context_content = ""
    if peripheral_narrative:
        context_content = peripheral_narrative
    elif peripheral_papers:
        # Fallback: build a simple list if Gemini didn't produce narrative
        items = []
        for pp in peripheral_papers:
            items.append(f"- **{pp.get('title', 'Untitled')}** ({pp.get('authors', 'Unknown')}): {pp.get('brief_summary', 'N/A')}")
        context_content = "\n".join(items)

    summary_text = overview[:150].rsplit(' ', 1)[0] if len(overview) > 150 else overview

    # Attribution footer
    if lang == "tr":
        attribution = "*Bu arastirma ozeti [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v2.4.0 tarafindan duzenlenmistir.*"
    else:
        attribution = "*This research digest was generated by [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) and curated by AeroSentinel v2.4.0.*"

    # ── Frontmatter ──
    core_count = len(core_papers)
    periph_count = len(peripheral_papers)
    total_count = core_count + periph_count if peripheral_papers else len(papers)

    post = f"""---
title: "{gemini_output['title']}"
date: {today}
tags:
{tags_yaml}
summary: "{summary_text}..."
draft: false
papers_count: {total_count}
core_papers: {core_count}
peripheral_papers: {periph_count}
ai_model: "Gemini 2.5 Flash"
ShowToc: true
TocOpen: false
---

## {lbl_overview}

{overview}

> **{lbl_trends}:** {trends}

---

## {lbl_core}

{core_content}"""

    # Add Broader Context only if there are peripheral papers
    if context_content:
        post += f"""

---

## {lbl_context}

{context_content}"""

    post += f"""

---

{attribution}

---

## {lbl_references}

{chr(10).join(references)}
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


def run_brain(papers: list) -> dict:
    """
    Full brain pipeline: generate bilingual analysis.
    Returns dict with keys: filename_base, en, tr, token_usage
    Each language entry has: filename, content, gemini_output
    """
    results = {}
    token_usage = {}

    for lang in LANGUAGES:
        gemini_output, lang_tokens = call_gemini(papers, lang=lang)
        if not gemini_output:
            print(f"   ⚠️ Failed to generate {lang.upper()} analysis")
            continue

        if lang_tokens:
            token_usage[lang] = lang_tokens

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
    if token_usage:
        results["token_usage"] = token_usage
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
