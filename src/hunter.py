"""
AeroSentinel Hunter
Searches academic APIs for high-quality aerospace research papers.
Sources: OpenAlex + arXiv + NASA NTRS + Crossref + CORE + IEEE Xplore
Enrichment: Semantic Scholar (citation metrics)

Usage:
    python -m src.hunter          # Run the hunt
    python -m src.hunter --dry    # Dry run (don't save history)
"""

import requests
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

from src.config import (
    KEYWORDS, TIER_1_JOURNALS, TIER_2_JOURNALS, ELITE_INSTITUTIONS,
    LOOKBACK_DAYS, CITATION_VELOCITY_THRESHOLD, HISTORY_FILE,
    S2_REQUESTS_PER_SECOND, S2_MAX_RETRIES, MAX_PAPERS_PER_POST,
    KEYWORD_PRIORITY, IEEE_API_KEY, MIN_HUNTER_SCORE, MAX_PAPER_AGE_DAYS
)


# ──────────────────────────────────────────────
#  HISTORY / DEDUPLICATION
# ──────────────────────────────────────────────

def load_history() -> set:
    """Load previously seen DOIs from history file."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return set(data.get("seen_dois", []))
    return set()


def save_history(new_dois: set):
    """Append new DOIs to history file."""
    current = load_history()
    current.update(new_dois)
    with open(HISTORY_FILE, "w") as f:
        json.dump({
            "seen_dois": list(current),
            "last_updated": datetime.now().isoformat()
        }, f, indent=2)


# ──────────────────────────────────────────────
#  UTILITY FUNCTIONS
# ──────────────────────────────────────────────

def reconstruct_abstract(inverted_index: Optional[dict]) -> Optional[str]:
    """
    Convert OpenAlex inverted index format to readable text.
    OpenAlex stores abstracts as {word: [position1, position2, ...]}
    """
    if not inverted_index:
        return None
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join([w for _, w in word_positions])


def normalize_doi(doi_str: str) -> str:
    """Strip URL prefix from DOI, return just the identifier."""
    if not doi_str:
        return ""
    return doi_str.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()


def check_elite_institution(authorships: list) -> tuple[bool, Optional[str]]:
    """Check if any author is affiliated with a whitelisted institution."""
    for author in authorships:
        for inst in author.get("institutions", []):
            name = inst.get("display_name", "")
            for elite in ELITE_INSTITUTIONS:
                if elite.lower() in name.lower():
                    return True, name
    return False, None


def classify_journal(journal_name: str) -> int:
    """Return tier (1, 2, or 0 for unranked) for a given journal."""
    if not journal_name:
        return 0
    jl = journal_name.lower()
    if any(t1.lower() in jl for t1 in TIER_1_JOURNALS):
        return 1
    if any(t2.lower() in jl for t2 in TIER_2_JOURNALS):
        return 2
    return 0


# ──────────────────────────────────────────────
#  SOURCE 1: OPENALEX
# ──────────────────────────────────────────────

def search_openalex(days: int = LOOKBACK_DAYS, keywords=None) -> dict:
    """
    Query OpenAlex API for papers matching our keywords.
    Returns dict of {doi: paper_dict} for deduplication.
    If keywords provided, uses those instead of KEYWORDS and relaxes the Sezer Filter.
    """
    search_keywords = keywords if keywords is not None else KEYWORDS
    is_custom = keywords is not None
    print(f"\n📡 [OpenAlex] Searching last {days} days...")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    candidates = {}

    for keyword in search_keywords:
        print(f"   🔍 '{keyword}'", end="")
        url = "https://api.openalex.org/works"
        params = {
            "search": keyword,
            "filter": f"from_publication_date:{start_date}",
            "per-page": 25,
            "sort": "publication_date:desc",
            "mailto": "aerosentinel@proton.me"  # Polite pool (faster responses)
        }

        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code != 200:
                print(f" ⚠️ HTTP {r.status_code}")
                continue
            data = r.json()
        except Exception as e:
            print(f" ⚠️ Error: {e}")
            continue

        count = 0
        for work in data.get("results", []):
            doi = normalize_doi(work.get("doi", ""))
            if not doi or doi in candidates:
                continue

            title = work.get("title", "")
            venue = work.get("primary_location", {}).get("source", {})
            journal = venue.get("display_name", "Unknown") if venue else "Unknown"
            abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
            authorships = work.get("authorships", [])
            is_elite, inst_name = check_elite_institution(authorships)
            tier = classify_journal(journal)
            cited_by = work.get("cited_by_count", 0)

            # --- THE SEZER FILTER ---
            keep = False
            reason = ""

            if is_custom:
                # Custom/targeted search: keep all results (relaxed filter)
                keep = True
                reason = f"Custom search: {journal}"
            elif tier == 1:
                # Rule 1: Tier 1 journal -> always keep
                keep = True
                reason = f"Tier 1: {journal}"
            elif tier == 2 and is_elite:
                # Rule 2: Tier 2 + elite institution -> keep
                keep = True
                reason = f"Tier 2 + Elite ({inst_name})"
            elif tier == 2 and cited_by >= 3:
                # Rule 3: Tier 2 + high citations -> keep (velocity checked later)
                keep = True
                reason = f"Tier 2 + Citations ({cited_by})"
            elif "arxiv" in journal.lower() and is_elite:
                # Rule 4: arXiv/preprint + elite institution -> keep
                keep = True
                reason = f"Preprint + Elite ({inst_name})"

            if keep:
                # Extract author names
                authors = []
                for a in authorships[:5]:  # Max 5 authors displayed
                    name = a.get("author", {}).get("display_name", "")
                    if name:
                        authors.append(name)

                candidates[doi] = {
                    "doi": doi,
                    "title": title,
                    "journal": journal,
                    "tier": tier,
                    "reason": reason,
                    "abstract": abstract,
                    "authors": authors,
                    "date": work.get("publication_date"),
                    "cited_by": cited_by,
                    "source": "OpenAlex",
                    "url": f"https://doi.org/{doi}",
                }
                count += 1

        print(f" → {count} found")
        time.sleep(0.3)  # Polite rate limiting

    print(f"   ✅ OpenAlex total: {len(candidates)} unique candidates")
    return candidates


# ──────────────────────────────────────────────
#  SOURCE 2: ARXIV (for latest preprints)
# ──────────────────────────────────────────────

def search_arxiv(existing_dois: set, keywords=None) -> dict:
    """
    Query arXiv for recent preprints in physics.flu-dyn and physics.ao-ph.
    Only keeps papers from elite institutions (checked via author affiliations in text).
    If keywords provided, uses those instead of KEYWORDS.
    """
    search_keywords = keywords if keywords is not None else KEYWORDS[:8]
    print(f"\n📡 [arXiv] Searching recent preprints...")
    candidates = {}

    for keyword in search_keywords:
        query = f"all:{keyword}"
        url = "https://export.arxiv.org/api/query"  # HTTPS (security fix)
        params = {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 15,
        }

        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.text)
        except Exception as e:
            print(f"   ⚠️ arXiv error: {e}")
            continue

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            arxiv_id = entry.find("atom:id", ns).text.strip()

            # Extract authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns).text
                if name:
                    authors.append(name)

            # Check if any author affiliation hints at elite institution
            affiliation_text = summary + " ".join(authors)
            is_elite = any(
                inst.lower() in affiliation_text.lower()
                for inst in ELITE_INSTITUTIONS
            )

            # Also check for DOI links (some arXiv papers have them)
            doi = ""
            for link in entry.findall("atom:link", ns):
                href = link.get("href", "")
                if "doi.org" in href:
                    doi = normalize_doi(href)

            # Use arxiv_id as dedup key if no DOI
            dedup_key = doi if doi else arxiv_id
            if dedup_key in existing_dois or dedup_key in candidates:
                continue

            # Only keep arXiv papers from elite institutions
            if is_elite:
                candidates[dedup_key] = {
                    "doi": doi or arxiv_id,
                    "title": title,
                    "journal": "arXiv Preprint",
                    "tier": 0,
                    "reason": "arXiv + Keyword match",
                    "abstract": summary,
                    "authors": authors[:5],
                    "date": entry.find("atom:published", ns).text[:10],
                    "cited_by": 0,
                    "source": "arXiv",
                    "url": arxiv_id,
                }

        time.sleep(3)  # arXiv requires 3-second delay between requests

    print(f"   ✅ arXiv total: {len(candidates)} preprints from elite institutions")
    return candidates


# ──────────────────────────────────────────────
#  SOURCE 3: NASA NTRS (Technical Reports)
# ──────────────────────────────────────────────

def search_nasa_ntrs(keywords=None) -> dict:
    """
    Query NASA Technical Reports Server for recent publications.
    These are gold-tier sources for reentry aerothermodynamics.
    If keywords provided, uses those instead of KEYWORDS.
    """
    search_keywords = keywords if keywords is not None else KEYWORDS[:8]
    print(f"\n📡 [NASA NTRS] Searching technical reports...")
    candidates = {}

    for keyword in search_keywords:
        url = "https://ntrs.nasa.gov/api/citations/search"

        try:
            r = requests.get(
                url,
                params={"q": keyword},
                headers={"Accept": "application/json"},
                timeout=30
            )
            if r.status_code != 200:
                continue
            data = r.json()
        except Exception as e:
            print(f"   ⚠️ NTRS error for '{keyword}': {e}")
            continue

        for item in data.get("results", []):
            ntrs_id = item.get("id", "")
            title = item.get("title", "")
            abstract = item.get("abstract", "")

            if not title or not ntrs_id:
                continue

            # Check publication date — skip papers before 2020 (bug fix)
            pub_date = item.get("publicationDate", "")
            if pub_date:
                try:
                    pd = datetime.strptime(pub_date[:10], "%Y-%m-%d")
                    if pd.year < 2020:
                        continue  # Skip old papers
                    if pd < datetime.now() - timedelta(days=LOOKBACK_DAYS * 2):
                        continue  # Too old
                except ValueError:
                    pass  # Keep if date is unparseable

            dedup_key = f"ntrs:{ntrs_id}"
            if dedup_key in candidates:
                continue

            # Extract authors with fallback (bug fix)
            authors = []
            author_list = item.get("authorList", [])
            if isinstance(author_list, list):
                for author in author_list:
                    if isinstance(author, dict):
                        name = author.get("name", "")
                    elif isinstance(author, str):
                        name = author
                    else:
                        continue
                    if name:
                        authors.append(name)
            if not authors:
                # Fallback: check alternative author fields
                alt_authors = item.get("authors", item.get("creator", []))
                if isinstance(alt_authors, list):
                    for a in alt_authors:
                        name = a if isinstance(a, str) else a.get("name", "")
                        if name:
                            authors.append(name)

            candidates[dedup_key] = {
                "doi": dedup_key,
                "title": title,
                "journal": "NASA Technical Report",
                "tier": 1,  # NASA reports are always Tier 1 quality
                "reason": "NASA NTRS",
                "abstract": abstract,
                "authors": authors[:5],
                "date": pub_date[:10] if pub_date else "Unknown",
                "cited_by": 0,
                "source": "NASA NTRS",
                "url": f"https://ntrs.nasa.gov/citations/{ntrs_id}",
            }

        time.sleep(0.5)

    print(f"   ✅ NTRS total: {len(candidates)} technical reports")
    return candidates


# ──────────────────────────────────────────────
#  SOURCE 4: CROSSREF (70M+ articles, no auth)
# ──────────────────────────────────────────────

def search_crossref(existing_dois: set, keywords=None) -> dict:
    """
    Query Crossref API for papers matching keywords.
    No authentication required. Polite header for faster responses.
    If keywords provided, uses those instead of KEYWORDS.
    """
    search_keywords = keywords if keywords is not None else KEYWORDS[:10]
    print(f"\n📡 [Crossref] Searching 70M+ articles...")
    candidates = {}
    start_date = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    for keyword in search_keywords:
        print(f"   🔍 '{keyword}'", end="")
        url = "https://api.crossref.org/works"
        params = {
            "query": keyword,
            "filter": f"from-pub-date:{start_date}",
            "rows": 20,
            "sort": "published",
            "order": "desc",
        }
        headers = {
            "User-Agent": "AeroSentinel/2.0 (mailto:aerosentinel@proton.me)",
        }

        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            if r.status_code != 200:
                print(f" ⚠️ HTTP {r.status_code}")
                continue
            data = r.json()
        except Exception as e:
            print(f" ⚠️ Error: {e}")
            continue

        count = 0
        for item in data.get("message", {}).get("items", []):
            doi = normalize_doi(item.get("DOI", ""))
            if not doi or doi in existing_dois or doi in candidates:
                continue

            title_parts = item.get("title", [])
            title = title_parts[0] if title_parts else ""
            if not title:
                continue

            # Journal name
            container = item.get("container-title", [])
            journal = container[0] if container else "Unknown"
            tier = classify_journal(journal)

            # Only keep Tier 1 or Tier 2 journals from Crossref
            if tier == 0:
                continue

            # Abstract
            abstract = item.get("abstract", "")
            # Crossref abstracts sometimes have JATS XML tags
            if abstract:
                import re
                abstract = re.sub(r"<[^>]+>", "", abstract).strip()

            # Authors
            authors = []
            for a in item.get("author", [])[:5]:
                given = a.get("given", "")
                family = a.get("family", "")
                if family:
                    authors.append(f"{given} {family}".strip())

            # Publication date
            date_parts = item.get("published", {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                parts = date_parts[0]
                pub_date = f"{parts[0]}"
                if len(parts) > 1:
                    pub_date += f"-{parts[1]:02d}"
                if len(parts) > 2:
                    pub_date += f"-{parts[2]:02d}"
            else:
                pub_date = "Unknown"

            cited_by = item.get("is-referenced-by-count", 0)

            candidates[doi] = {
                "doi": doi,
                "title": title,
                "journal": journal,
                "tier": tier,
                "reason": f"Crossref Tier {tier}: {journal}",
                "abstract": abstract,
                "authors": authors,
                "date": pub_date,
                "cited_by": cited_by,
                "source": "Crossref",
                "url": f"https://doi.org/{doi}",
            }
            count += 1

        print(f" → {count} found")
        time.sleep(0.5)  # Polite rate limiting

    print(f"   ✅ Crossref total: {len(candidates)} unique candidates")
    return candidates


# ──────────────────────────────────────────────
#  SOURCE 5: CORE (200M+ open access, no auth)
# ──────────────────────────────────────────────

def search_core(existing_dois: set, keywords=None) -> dict:
    """
    Query CORE API v3 for open access research papers.
    No authentication required. 200M+ open access articles.
    If keywords provided, uses those instead of KEYWORDS.
    """
    search_keywords = keywords if keywords is not None else KEYWORDS[:8]
    print(f"\n📡 [CORE] Searching 200M+ open access articles...")
    candidates = {}

    for keyword in search_keywords:
        print(f"   🔍 '{keyword}'", end="")
        url = "https://api.core.ac.uk/v3/search/works"
        params = {
            "q": keyword,
            "limit": 15,
        }

        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code != 200:
                print(f" ⚠️ HTTP {r.status_code}")
                continue
            data = r.json()
        except Exception as e:
            print(f" ⚠️ Error: {e}")
            continue

        count = 0
        for item in data.get("results", []):
            doi = normalize_doi(item.get("doi", ""))
            if not doi or doi in existing_dois or doi in candidates:
                continue

            title = item.get("title", "")
            if not title:
                continue

            # CORE doesn't always have structured journal info
            journal = "Unknown"
            journal_obj = item.get("journals", [])
            if journal_obj and isinstance(journal_obj, list) and len(journal_obj) > 0:
                journal = journal_obj[0].get("title", "Unknown")
            elif item.get("publisher", ""):
                journal = item.get("publisher", "Unknown")

            tier = classify_journal(journal)
            # Only keep if we can classify the journal
            if tier == 0:
                continue

            abstract = item.get("abstract", "")

            # Authors
            authors = []
            for a in item.get("authors", [])[:5]:
                if isinstance(a, dict):
                    authors.append(a.get("name", ""))
                elif isinstance(a, str):
                    authors.append(a)

            pub_date = (item.get("publishedDate") or item.get("yearPublished") or "Unknown")
            if isinstance(pub_date, int):
                pub_date = str(pub_date)
            pub_date = str(pub_date)[:10]

            # Skip old papers
            if pub_date != "Unknown":
                try:
                    pd = datetime.strptime(pub_date[:4], "%Y")
                    if pd.year < 2020:
                        continue
                except ValueError:
                    pass

            cited_by = item.get("citationCount", 0) or 0

            candidates[doi] = {
                "doi": doi,
                "title": title,
                "journal": journal,
                "tier": tier,
                "reason": f"CORE Tier {tier}: {journal}",
                "abstract": abstract,
                "authors": authors,
                "date": pub_date,
                "cited_by": cited_by,
                "source": "CORE",
                "url": f"https://doi.org/{doi}",
            }
            count += 1

        print(f" → {count} found")
        time.sleep(0.5)

    print(f"   ✅ CORE total: {len(candidates)} unique candidates")
    return candidates


# ──────────────────────────────────────────────
#  SOURCE 6: IEEE XPLORE (needs API key)
# ──────────────────────────────────────────────

def search_ieee(existing_dois: set, keywords=None) -> dict:
    """
    Query IEEE Xplore API for papers matching keywords.
    Requires IEEE_API_KEY. Returns empty dict if no key set.
    If keywords provided, uses those instead of KEYWORDS.
    """
    if not IEEE_API_KEY:
        print("\n📡 [IEEE] Skipped (no IEEE_API_KEY set)")
        return {}

    search_keywords = keywords if keywords is not None else KEYWORDS[:6]
    print(f"\n📡 [IEEE Xplore] Searching with API key...")
    candidates = {}

    for keyword in search_keywords:
        print(f"   🔍 '{keyword}'", end="")
        url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        params = {
            "apikey": IEEE_API_KEY,
            "querytext": keyword,
            "max_records": 15,
            "sort_order": "desc",
            "sort_field": "publication_date",
        }

        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code != 200:
                print(f" ⚠️ HTTP {r.status_code}")
                continue
            data = r.json()
        except Exception as e:
            print(f" ⚠️ Error: {e}")
            continue

        count = 0
        for item in data.get("articles", []):
            doi = normalize_doi(item.get("doi", ""))
            if not doi or doi in existing_dois or doi in candidates:
                continue

            title = item.get("title", "")
            if not title:
                continue

            journal = item.get("publication_title", "IEEE")
            tier = classify_journal(journal)
            abstract = item.get("abstract", "")

            # Authors
            authors = []
            author_obj = item.get("authors", {})
            if isinstance(author_obj, dict):
                for a in author_obj.get("authors", [])[:5]:
                    authors.append(a.get("full_name", ""))
            elif isinstance(author_obj, list):
                for a in author_obj[:5]:
                    if isinstance(a, dict):
                        authors.append(a.get("full_name", a.get("name", "")))

            pub_date = item.get("publication_date", "Unknown")

            # Skip old papers
            pub_year = item.get("publication_year", "")
            if pub_year and int(pub_year) < 2020:
                continue

            cited_by = item.get("citing_paper_count", 0) or 0

            candidates[doi] = {
                "doi": doi,
                "title": title,
                "journal": journal,
                "tier": tier,
                "reason": f"IEEE: {journal}",
                "abstract": abstract,
                "authors": authors,
                "date": pub_date,
                "cited_by": cited_by,
                "source": "IEEE Xplore",
                "url": f"https://doi.org/{doi}",
            }
            count += 1

        print(f" → {count} found")
        time.sleep(1)

    print(f"   ✅ IEEE total: {len(candidates)} unique candidates")
    return candidates


# ──────────────────────────────────────────────
#  ENRICHMENT: SEMANTIC SCHOLAR
# ──────────────────────────────────────────────

def enrich_with_semantic_scholar(papers: list) -> list:
    """
    Enrich paper data with Semantic Scholar metrics.
    Also fetches clean abstract text as fallback.
    """
    print(f"\n🔬 [Semantic Scholar] Enriching {len(papers)} papers...")
    enriched = []

    for paper in papers:
        doi = paper.get("doi", "")

        # Skip non-DOI identifiers (arXiv IDs, NTRS IDs)
        if not doi or doi.startswith("ntrs:") or doi.startswith("http"):
            paper["velocity"] = 0
            paper["influential_citations"] = 0
            enriched.append(paper)
            continue

        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
        params = {"fields": "citationVelocity,influentialCitationCount,abstract"}

        for attempt in range(S2_MAX_RETRIES):
            try:
                r = requests.get(url, params=params, timeout=15)

                if r.status_code == 200:
                    s2 = r.json()
                    paper["velocity"] = s2.get("citationVelocity") or 0
                    paper["influential_citations"] = s2.get("influentialCitationCount") or 0

                    # Use S2 abstract if OpenAlex reconstruction was empty
                    if not paper.get("abstract") and s2.get("abstract"):
                        paper["abstract"] = s2["abstract"]

                    enriched.append(paper)
                    break

                elif r.status_code == 429:
                    # Rate limited - wait and retry
                    wait = (attempt + 1) * 5
                    print(f"   ⏳ Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue

                else:
                    # Paper not found in S2 - keep if Tier 1
                    paper["velocity"] = 0
                    paper["influential_citations"] = 0
                    enriched.append(paper)
                    break

            except Exception:
                paper["velocity"] = 0
                paper["influential_citations"] = 0
                enriched.append(paper)
                break

        time.sleep(1 / S2_REQUESTS_PER_SECOND)

    return enriched


# ──────────────────────────────────────────────
#  FINAL RANKING & SELECTION
# ──────────────────────────────────────────────

def _is_recent(paper, cutoff):
    """Return True if paper is newer than cutoff date, or if date is unparseable."""
    date_str = paper.get("date", "")
    if not date_str or date_str == "Unknown":
        return False  # No date = reject
    try:
        pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return pub_date >= cutoff
    except ValueError:
        try:
            # Try year-month format
            pub_date = datetime.strptime(date_str[:7], "%Y-%m")
            return pub_date >= cutoff
        except ValueError:
            return False  # Unparseable = reject


def rank_and_select(papers: list, skip_age_filter: bool = False) -> list:
    """
    Rank papers by quality score and select top N for summarization.
    Score = tier_bonus + source_bonus + keyword_priority + citation_metrics + recency + abstract
    If skip_age_filter is True, the MAX_PAPER_AGE_DAYS cutoff is not applied (for custom searches).
    """
    # Hard recency cutoff — reject papers older than MAX_PAPER_AGE_DAYS
    if not skip_age_filter:
        cutoff = datetime.now() - timedelta(days=MAX_PAPER_AGE_DAYS)
        papers = [p for p in papers if _is_recent(p, cutoff)]

    for paper in papers:
        score = 0

        # Tier bonus
        if paper["tier"] == 1:
            score += 50
        elif paper["tier"] == 2:
            score += 20

        # Source bonus
        if paper["source"] == "NASA NTRS":
            score += 30

        # Keyword priority scoring: match title+abstract against tiers
        text = (paper.get("title", "") + " " + (paper.get("abstract", "") or "")).lower()
        best_kw_bonus = 0
        for kw, bonus in KEYWORD_PRIORITY.items():
            if kw in text:
                best_kw_bonus = max(best_kw_bonus, bonus)
        score += best_kw_bonus

        # Citation metrics
        score += min(paper.get("velocity", 0) * 3, 30)
        score += min(paper.get("influential_citations", 0) * 5, 25)
        score += min(paper.get("cited_by", 0), 20)

        # Recency bonus (papers from last 3 days get extra points)
        try:
            pub_date = datetime.strptime(paper["date"][:10], "%Y-%m-%d")
            days_old = (datetime.now() - pub_date).days
            if days_old <= 3:
                score += 15
            elif days_old <= 7:
                score += 10
        except (ValueError, TypeError):
            pass

        # Has abstract bonus (we need this for summarization)
        if paper.get("abstract"):
            score += 10

        paper["score"] = score

    # Sort by score descending
    papers.sort(key=lambda p: p["score"], reverse=True)

    # Select top papers with minimum score threshold
    qualified = [p for p in papers if p["score"] >= MIN_HUNTER_SCORE]
    selected = qualified[:MAX_PAPERS_PER_POST]

    return selected


# ──────────────────────────────────────────────
#  MAIN ENTRY POINT
# ──────────────────────────────────────────────

def run_hunt(dry_run: bool = False, custom_keywords=None, date_from=None, date_to=None) -> list:
    """
    Execute the full hunting pipeline.
    Returns list of selected papers ready for summarization.

    If custom_keywords provided, uses those instead of KEYWORDS for all sources.
    If date_from/date_to provided (YYYY-MM-DD strings), adjusts the lookback window.
    """
    is_custom = custom_keywords is not None
    print("=" * 60)
    if is_custom:
        print(f"🔎 AEROSENTINEL CUSTOM SEARCH — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"🚀 AEROSENTINEL HUNTER — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Calculate custom lookback days from date_from if provided
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d")
            days = (datetime.now() - from_date).days + 1
        except ValueError:
            days = LOOKBACK_DAYS
    else:
        days = LOOKBACK_DAYS

    # 1. Load history
    seen_dois = load_history()
    print(f"📚 History: {len(seen_dois)} previously seen papers")

    # 2. Search all sources
    openalex_papers = search_openalex(days=days, keywords=custom_keywords)
    arxiv_papers = search_arxiv(set(openalex_papers.keys()) | seen_dois, keywords=custom_keywords)
    ntrs_papers = search_nasa_ntrs(keywords=custom_keywords)
    crossref_papers = search_crossref(set(openalex_papers.keys()) | seen_dois, keywords=custom_keywords)
    core_papers = search_core(
        set(openalex_papers.keys()) | set(crossref_papers.keys()) | seen_dois,
        keywords=custom_keywords
    )
    ieee_papers = search_ieee(
        set(openalex_papers.keys()) | set(crossref_papers.keys()) | seen_dois,
        keywords=custom_keywords
    )

    # 3. Merge all sources (DOI-based dedup)
    all_papers = {}
    all_papers.update(openalex_papers)
    all_papers.update(arxiv_papers)
    all_papers.update(ntrs_papers)
    all_papers.update(crossref_papers)
    all_papers.update(core_papers)
    all_papers.update(ieee_papers)

    # 4. Remove previously seen
    new_papers = {
        doi: paper for doi, paper in all_papers.items()
        if doi not in seen_dois
    }
    print(f"\n📊 Total: {len(all_papers)} found, {len(new_papers)} are new")
    print(f"   Sources: OpenAlex={len(openalex_papers)}, arXiv={len(arxiv_papers)}, "
          f"NTRS={len(ntrs_papers)}, Crossref={len(crossref_papers)}, "
          f"CORE={len(core_papers)}, IEEE={len(ieee_papers)}")

    if not new_papers:
        print("\n✅ No new papers found. The field is quiet today.")
        return []

    # 5. Enrich with Semantic Scholar
    enriched = enrich_with_semantic_scholar(list(new_papers.values()))

    # 6. Apply Tier 2 citation velocity filter
    # Papers that are Tier 2 without elite institution need velocity >= threshold
    # Custom searches skip this filter (targeted search, keep all results)
    if is_custom:
        filtered = enriched
    else:
        filtered = []
        for paper in enriched:
            if paper["tier"] == 1 or "Elite" in paper.get("reason", ""):
                filtered.append(paper)
            elif paper["tier"] == 2 and paper.get("velocity", 0) >= CITATION_VELOCITY_THRESHOLD:
                paper["reason"] += f" + High Velocity ({paper['velocity']})"
                filtered.append(paper)
            elif paper["source"] in ("arXiv", "NASA NTRS"):
                filtered.append(paper)
            elif "Tier 1" in paper.get("reason", ""):
                filtered.append(paper)

    print(f"   ✅ After velocity filter: {len(filtered)} papers")

    # 7. Rank and select
    selected = rank_and_select(filtered, skip_age_filter=is_custom)

    # 8. Display results
    print("\n" + "=" * 60)
    print(f"🏆 SELECTED ({len(selected)} papers)")
    print("=" * 60)

    for i, p in enumerate(selected, 1):
        print(f"\n  [{i}] {p['title']}")
        print(f"      📰 {p['journal']} | 🏷️ {p['reason']}")
        print(f"      📈 Score: {p['score']} | Velocity: {p.get('velocity', 0)}")
        print(f"      👤 {', '.join(p['authors'][:3])}")
        print(f"      🔗 {p['url']}")
        if p.get("abstract"):
            print(f"      📝 {p['abstract'][:120]}...")

    # 9. Save history (unless dry run)
    if not dry_run and selected:
        save_history({p["doi"] for p in selected})
        print(f"\n💾 History updated with {len(selected)} new DOIs")
    elif dry_run:
        print("\n🧪 DRY RUN — history not saved")

    return selected


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    papers = run_hunt(dry_run=dry)
    if papers:
        # Save results for brain.py to pick up
        with open("latest_hunt.json", "w") as f:
            json.dump(papers, f, indent=2)
        print(f"\n📄 Results saved to latest_hunt.json")
