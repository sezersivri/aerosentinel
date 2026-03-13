"""
AeroSentinel Intelligence Module v3.0
Semantic scoring, citation expansion, author tracking,
keyword analytics, concept search, and trend detection.

All features use free APIs (Gemini embeddings, OpenAlex) — no paid services.
"""

import json
import math
import os
import requests
import time
from collections import Counter
from datetime import datetime, timedelta

from src.config import GEMINI_API_KEY

# ── PATHS ──
DATA_DIR = "data"
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist_authors.json")
KEYWORD_STATS_FILE = os.path.join(DATA_DIR, "keyword_stats.json")
TREND_HISTORY_FILE = os.path.join(DATA_DIR, "trend_history.json")
THESIS_EMBEDDING_FILE = os.path.join(DATA_DIR, "thesis_embedding.json")

# ── THESIS ABSTRACT (reference vector for semantic scoring) ──
THESIS_ABSTRACT = (
    "Prediction of aerodynamic heating on high-speed missiles "
    "using Gaussian process based surrogate models. "
    "This research focuses on developing efficient machine learning "
    "surrogate models, particularly Gaussian process regression, "
    "to predict aerodynamic heating distributions on missile geometries "
    "in hypersonic and supersonic flight regimes. The methodology combines "
    "computational fluid dynamics simulations with data-driven approaches "
    "to create fast, accurate heat flux predictions for thermal protection "
    "system design and trajectory optimization."
)


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


# ══════════════════════════════════════════════
#  1. SEMANTIC SCORING (Gemini Embeddings API)
# ══════════════════════════════════════════════

def _cosine_similarity(a, b):
    """Pure-Python cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_embedding(text):
    """Get embedding vector from Gemini text-embedding-004 API (free tier)."""
    if not GEMINI_API_KEY:
        return None

    url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text[:2048]}]},
        "taskType": "SEMANTIC_SIMILARITY",
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json().get("embedding", {}).get("values")
    except Exception:
        pass
    return None


def _get_thesis_embedding():
    """Get or cache the thesis abstract embedding."""
    ensure_data_dir()
    if os.path.exists(THESIS_EMBEDDING_FILE):
        try:
            with open(THESIS_EMBEDDING_FILE) as f:
                data = json.load(f)
                if data.get("embedding"):
                    return data["embedding"]
        except (json.JSONDecodeError, IOError):
            pass

    embedding = _get_embedding(THESIS_ABSTRACT)
    if embedding:
        with open(THESIS_EMBEDDING_FILE, "w") as f:
            json.dump({"embedding": embedding, "cached_at": datetime.now().isoformat()}, f)
    return embedding


def compute_semantic_scores(papers):
    """
    Score each paper's abstract against thesis abstract using Gemini embeddings.
    Adds 'semantic_score' (0-100) to each paper dict.
    Falls back gracefully if API is unavailable.
    """
    print("\n🧠 [Intelligence] Computing semantic relevance scores...")

    thesis_emb = _get_thesis_embedding()
    if not thesis_emb:
        print("   ⚠️ Could not get thesis embedding, skipping semantic scoring")
        for p in papers:
            p["semantic_score"] = 0
        return papers

    scored = 0
    for paper in papers:
        abstract = paper.get("abstract", "")
        if not abstract or abstract.startswith("[NO ABSTRACT]"):
            paper["semantic_score"] = 0
            continue

        text = f"{paper.get('title', '')}. {abstract}"
        emb = _get_embedding(text)

        if emb:
            sim = _cosine_similarity(thesis_emb, emb)
            paper["semantic_score"] = round(sim * 100, 1)
            scored += 1
        else:
            paper["semantic_score"] = 0

        time.sleep(0.1)  # Rate limiting

    print(f"   ✅ Scored {scored}/{len(papers)} papers semantically")

    by_score = sorted(papers, key=lambda p: p.get("semantic_score", 0), reverse=True)
    for p in by_score[:3]:
        if p["semantic_score"] > 0:
            print(f"      {p['semantic_score']:.0f}% — {p['title'][:60]}")

    return papers


# ══════════════════════════════════════════════
#  2. CITATION GRAPH EXPANSION
# ══════════════════════════════════════════════

def expand_citation_graph(top_papers, existing_dois, max_new=10):
    """
    For top-scoring papers, fetch citing works and co-citation neighbors
    from OpenAlex. Returns new candidate papers not already seen.
    """
    print(f"\n🔗 [Intelligence] Expanding citation graph from {len(top_papers)} seed papers...")
    new_candidates = {}

    for paper in top_papers[:3]:
        doi = paper.get("doi", "")
        if not doi or doi.startswith("ntrs:") or doi.startswith("http"):
            continue

        openalex_id = _get_openalex_id(doi)
        if not openalex_id:
            continue

        # Fetch works that cite this paper
        try:
            url = "https://api.openalex.org/works"
            params = {
                "filter": f"cites:{openalex_id}",
                "per-page": 10,
                "sort": "publication_date:desc",
                "mailto": "aerosentinel@proton.me",
            }
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                for work in r.json().get("results", []):
                    _try_add_candidate(work, new_candidates, existing_dois, "citing")
        except Exception:
            pass

        # Fetch referenced works to find co-citation neighbors
        try:
            url = f"https://api.openalex.org/works/{openalex_id}"
            params = {"mailto": "aerosentinel@proton.me"}
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                ref_ids = r.json().get("referenced_works", [])[:5]
                for ref_id in ref_ids[:3]:
                    ref_short = ref_id.split("/")[-1] if "/" in ref_id else ref_id
                    cutoff = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
                    try:
                        cr = requests.get(
                            "https://api.openalex.org/works",
                            params={
                                "filter": f"cites:{ref_short},from_publication_date:{cutoff}",
                                "per-page": 5,
                                "sort": "cited_by_count:desc",
                                "mailto": "aerosentinel@proton.me",
                            },
                            timeout=15,
                        )
                        if cr.status_code == 200:
                            for work in cr.json().get("results", []):
                                _try_add_candidate(work, new_candidates, existing_dois, "co-citation")
                    except Exception:
                        pass
                    time.sleep(0.3)
        except Exception:
            pass

        time.sleep(0.5)

    result = dict(list(new_candidates.items())[:max_new])
    print(f"   ✅ Found {len(result)} new papers via citation graph")
    return result


def _get_openalex_id(doi):
    """Look up OpenAlex work ID from DOI."""
    try:
        url = f"https://api.openalex.org/works/doi:{doi}"
        r = requests.get(url, params={"mailto": "aerosentinel@proton.me"}, timeout=10)
        if r.status_code == 200:
            return r.json().get("id", "").split("/")[-1]
    except Exception:
        pass
    return None


def _try_add_candidate(work, candidates, existing_dois, reason):
    """Parse an OpenAlex work and add to candidates if new."""
    from src.hunter import normalize_doi, reconstruct_abstract, classify_journal, check_elite_institution

    doi = normalize_doi(work.get("doi", ""))
    if not doi or doi in existing_dois or doi in candidates:
        return

    title = work.get("title", "")
    if not title:
        return

    venue = work.get("primary_location", {}).get("source", {})
    journal = venue.get("display_name", "Unknown") if venue else "Unknown"
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
    authorships = work.get("authorships", [])
    is_elite, inst_name = check_elite_institution(authorships)

    authors = []
    for a in authorships[:5]:
        name = a.get("author", {}).get("display_name", "")
        if name:
            authors.append(name)

    candidates[doi] = {
        "doi": doi,
        "title": title,
        "journal": journal,
        "tier": classify_journal(journal),
        "reason": f"Citation graph ({reason})",
        "abstract": abstract,
        "authors": authors,
        "date": work.get("publication_date"),
        "cited_by": work.get("cited_by_count", 0),
        "source": "CitationGraph",
        "url": f"https://doi.org/{doi}",
    }


# ══════════════════════════════════════════════
#  3. AUTHOR WATCHLIST
# ══════════════════════════════════════════════

def load_watchlist():
    """Load author watchlist from file."""
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"authors": {}, "last_checked": None}


def save_watchlist(data):
    """Save author watchlist to file."""
    ensure_data_dir()
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)


def update_watchlist_from_published(paper):
    """Add authors from a published paper to the watchlist."""
    watchlist = load_watchlist()

    authors = paper.get("authors", [])
    doi = paper.get("doi", "")

    for author_name in authors[:3]:
        author_id = _lookup_author_id(author_name)
        if not author_id:
            continue

        if author_id in watchlist["authors"]:
            watchlist["authors"][author_id]["papers_seen"] += 1
            watchlist["authors"][author_id]["last_paper"] = doi
        else:
            watchlist["authors"][author_id] = {
                "name": author_name,
                "openalex_id": author_id,
                "papers_seen": 1,
                "last_paper": doi,
                "added_at": datetime.now().isoformat(),
            }

    save_watchlist(watchlist)
    print(f"   👤 Watchlist updated: {len(watchlist['authors'])} authors tracked")


def _lookup_author_id(name):
    """Look up OpenAlex author ID by name."""
    try:
        url = "https://api.openalex.org/authors"
        params = {"search": name, "per-page": 1, "mailto": "aerosentinel@proton.me"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                return results[0].get("id", "").split("/")[-1]
    except Exception:
        pass
    return None


def check_watchlist_authors(existing_dois, days=14):
    """Check if watched authors have new publications."""
    watchlist = load_watchlist()
    authors = watchlist.get("authors", {})

    if not authors:
        return {}

    print(f"\n👤 [Intelligence] Checking {len(authors)} watched authors for new papers...")

    from src.hunter import normalize_doi, reconstruct_abstract, classify_journal

    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    new_papers = {}

    for author_id, info in list(authors.items())[:20]:
        try:
            url = "https://api.openalex.org/works"
            params = {
                "filter": f"author.id:{author_id},from_publication_date:{start_date}",
                "per-page": 5,
                "sort": "publication_date:desc",
                "mailto": "aerosentinel@proton.me",
            }
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                for work in r.json().get("results", []):
                    doi = normalize_doi(work.get("doi", ""))
                    if not doi or doi in existing_dois or doi in new_papers:
                        continue

                    title = work.get("title", "")
                    if not title:
                        continue

                    venue = work.get("primary_location", {}).get("source", {})
                    journal = venue.get("display_name", "Unknown") if venue else "Unknown"
                    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))

                    work_authors = []
                    for a in work.get("authorships", [])[:5]:
                        name = a.get("author", {}).get("display_name", "")
                        if name:
                            work_authors.append(name)

                    new_papers[doi] = {
                        "doi": doi,
                        "title": title,
                        "journal": journal,
                        "tier": classify_journal(journal),
                        "reason": f"Watched author: {info['name']}",
                        "abstract": abstract,
                        "authors": work_authors,
                        "date": work.get("publication_date"),
                        "cited_by": work.get("cited_by_count", 0),
                        "source": "AuthorWatch",
                        "url": f"https://doi.org/{doi}",
                    }
        except Exception:
            pass
        time.sleep(0.3)

    watchlist["last_checked"] = datetime.now().isoformat()
    save_watchlist(watchlist)

    print(f"   ✅ Found {len(new_papers)} new papers from watched authors")
    return new_papers


# ══════════════════════════════════════════════
#  4. KEYWORD SELF-TUNING
# ══════════════════════════════════════════════

def load_keyword_stats():
    """Load keyword performance stats."""
    if os.path.exists(KEYWORD_STATS_FILE):
        try:
            with open(KEYWORD_STATS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"keywords": {}, "updated_at": None}


def save_keyword_stats(data):
    """Save keyword performance stats."""
    ensure_data_dir()
    data["updated_at"] = datetime.now().isoformat()
    with open(KEYWORD_STATS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def identify_matching_keywords(paper, keywords):
    """Return which keywords match this paper's title+abstract."""
    text = (paper.get("title", "") + " " + (paper.get("abstract", "") or "")).lower()
    return [kw for kw in keywords if kw.lower() in text]


def record_keyword_hits(papers, keywords, selected_dois):
    """Record which keywords found selected vs non-selected papers."""
    stats = load_keyword_stats()

    for paper in papers:
        matched_kws = identify_matching_keywords(paper, keywords)
        was_selected = paper.get("doi", "") in selected_dois

        for kw in matched_kws:
            kw_lower = kw.lower()
            if kw_lower not in stats["keywords"]:
                stats["keywords"][kw_lower] = {"found": 0, "selected": 0, "published": 0}

            stats["keywords"][kw_lower]["found"] += 1
            if was_selected:
                stats["keywords"][kw_lower]["selected"] += 1

    save_keyword_stats(stats)


def record_keyword_published(paper, keywords):
    """Record that keywords matching a published paper led to a success."""
    stats = load_keyword_stats()
    matched = identify_matching_keywords(paper, keywords)

    for kw in matched:
        kw_lower = kw.lower()
        if kw_lower in stats["keywords"]:
            stats["keywords"][kw_lower]["published"] += 1

    save_keyword_stats(stats)


def get_keyword_report():
    """Generate a keyword performance report."""
    stats = load_keyword_stats()
    keywords = stats.get("keywords", {})

    if not keywords:
        return "📊 No keyword stats recorded yet."

    lines = ["📊 <b>Keyword Performance</b>\n"]

    sorted_kw = sorted(
        keywords.items(),
        key=lambda x: (x[1]["published"] / max(x[1]["found"], 1), x[1]["found"]),
        reverse=True,
    )

    for kw, data in sorted_kw[:15]:
        found = data["found"]
        selected = data["selected"]
        published = data["published"]
        precision = published / found * 100 if found > 0 else 0

        if precision >= 50:
            indicator = "🟢"
        elif precision >= 20:
            indicator = "🟡"
        else:
            indicator = "🔴"

        lines.append(f"{indicator} <code>{kw[:40]}</code>")
        lines.append(f"   found:{found} sel:{selected} pub:{published} ({precision:.0f}%)")

    return "\n".join(lines)


# ══════════════════════════════════════════════
#  5. OPENALEX CONCEPT SEARCH
# ══════════════════════════════════════════════

# Targeted compound queries that simulate concept-pair filtering.
# More precise than single keywords — finds papers at the intersection
# of two relevant concepts (e.g., ML + aerodynamic heating).
CONCEPT_QUERIES = [
    "gaussian process surrogate aerodynamic heating",
    "machine learning hypersonic heating prediction",
    "neural network heat flux missile reentry",
    "surrogate model computational fluid dynamics thermal",
    "kriging aerothermodynamic prediction",
    "deep learning boundary layer transition hypersonic",
    "physics-informed neural network supersonic flow",
    "multi-fidelity surrogate aerodynamics optimization",
]


def search_by_concepts(existing_dois, days=14):
    """
    Search OpenAlex using targeted compound queries designed to find
    papers at the intersection of thesis-relevant concepts.
    More precise than the keyword tier system.
    """
    from src.hunter import normalize_doi, reconstruct_abstract, classify_journal, check_elite_institution

    print(f"\n🏷️ [Intelligence] Running concept-based search...")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    candidates = {}

    for query in CONCEPT_QUERIES:
        try:
            url = "https://api.openalex.org/works"
            params = {
                "search": query,
                "filter": f"from_publication_date:{start_date}",
                "per-page": 10,
                "sort": "relevance_score:desc",
                "mailto": "aerosentinel@proton.me",
            }
            r = requests.get(url, params=params, timeout=15)
            if r.status_code != 200:
                continue

            for work in r.json().get("results", []):
                doi = normalize_doi(work.get("doi", ""))
                if not doi or doi in existing_dois or doi in candidates:
                    continue

                title = work.get("title", "")
                if not title:
                    continue

                venue = work.get("primary_location", {}).get("source", {})
                journal = venue.get("display_name", "Unknown") if venue else "Unknown"
                abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
                authorships = work.get("authorships", [])
                is_elite, inst_name = check_elite_institution(authorships)

                # Extract OpenAlex concepts for this paper
                concepts = [c.get("display_name", "") for c in work.get("concepts", [])[:5]]

                authors = []
                for a in authorships[:5]:
                    name = a.get("author", {}).get("display_name", "")
                    if name:
                        authors.append(name)

                candidates[doi] = {
                    "doi": doi,
                    "title": title,
                    "journal": journal,
                    "tier": classify_journal(journal),
                    "reason": f"Concept match: {query[:40]}",
                    "abstract": abstract,
                    "authors": authors,
                    "date": work.get("publication_date"),
                    "cited_by": work.get("cited_by_count", 0),
                    "source": "ConceptSearch",
                    "url": f"https://doi.org/{doi}",
                    "concepts": concepts,
                }
        except Exception:
            pass
        time.sleep(0.3)

    print(f"   ✅ Concept search found {len(candidates)} candidates")
    return candidates


# ══════════════════════════════════════════════
#  6. TREND DETECTION
# ══════════════════════════════════════════════

def load_trend_history():
    """Load trend tracking history."""
    if os.path.exists(TREND_HISTORY_FILE):
        try:
            with open(TREND_HISTORY_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"snapshots": []}


def save_trend_history(data):
    """Save trend tracking history."""
    ensure_data_dir()
    with open(TREND_HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_trend_snapshot(papers, gemini_results=None):
    """Record tag/topic frequencies for this run."""
    history = load_trend_history()

    tag_counts = Counter()
    source_counts = Counter()

    for paper in papers:
        source_counts[paper.get("source", "Unknown")] += 1
        for concept in paper.get("concepts", []):
            tag_counts[concept] += 1

    # Also count tags from Gemini analysis if available
    if gemini_results:
        for result in gemini_results:
            for lang in ("en", "tr"):
                if lang in result:
                    for tag in result[lang].get("gemini_output", {}).get("tags", []):
                        tag_counts[tag] += 1

    snapshot = {
        "date": datetime.now().isoformat(),
        "paper_count": len(papers),
        "tags": dict(tag_counts),
        "sources": dict(source_counts),
    }

    history["snapshots"].append(snapshot)

    # Keep last 52 snapshots (~1 year of weekly runs)
    if len(history["snapshots"]) > 52:
        history["snapshots"] = history["snapshots"][-52:]

    save_trend_history(history)


def detect_trends(window=8):
    """
    Analyze tag frequency trends over recent snapshots.
    Returns trending (increasing) and cooling (decreasing) topics.
    """
    history = load_trend_history()
    snapshots = history.get("snapshots", [])

    if len(snapshots) < 3:
        return None

    recent = snapshots[-window:] if len(snapshots) >= window else snapshots
    older = snapshots[:-len(recent)] if len(snapshots) > len(recent) else []

    if not older:
        return None

    recent_tags = Counter()
    older_tags = Counter()

    for s in recent:
        for tag, count in s.get("tags", {}).items():
            recent_tags[tag] += count

    for s in older:
        for tag, count in s.get("tags", {}).items():
            older_tags[tag] += count

    recent_norm = {k: v / len(recent) for k, v in recent_tags.items()}
    older_norm = {k: v / len(older) for k, v in older_tags.items()}

    trending = []
    cooling = []

    all_tags = set(list(recent_tags.keys()) + list(older_tags.keys()))
    for tag in all_tags:
        recent_rate = recent_norm.get(tag, 0)
        older_rate = older_norm.get(tag, 0)

        if recent_rate > older_rate * 1.5 and recent_rate >= 1:
            trending.append((tag, recent_rate, older_rate))
        elif older_rate > recent_rate * 1.5 and older_rate >= 1:
            cooling.append((tag, recent_rate, older_rate))

    trending.sort(key=lambda x: x[1] - x[2], reverse=True)
    cooling.sort(key=lambda x: x[2] - x[1], reverse=True)

    return {"trending": trending[:5], "cooling": cooling[:5]}


def format_trend_report():
    """Format trend detection results as a Telegram message."""
    trends = detect_trends()
    if not trends:
        return "📈 Not enough data for trend detection yet (need 3+ runs)."

    lines = ["📈 <b>Research Trend Report</b>\n"]

    if trends["trending"]:
        lines.append("🔥 <b>Trending Up:</b>")
        for tag, recent, older in trends["trending"]:
            lines.append(f"   📈 {tag} ({older:.1f} → {recent:.1f}/run)")

    if trends["cooling"]:
        lines.append("\n❄️ <b>Cooling Down:</b>")
        for tag, recent, older in trends["cooling"]:
            lines.append(f"   📉 {tag} ({older:.1f} → {recent:.1f}/run)")

    if not trends["trending"] and not trends["cooling"]:
        lines.append("   No significant trend changes detected.")

    return "\n".join(lines)
