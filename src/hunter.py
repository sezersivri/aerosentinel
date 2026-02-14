"""
AeroSentinel Hunter
Searches academic APIs for high-quality aerospace research papers.
Sources: OpenAlex (primary) + Semantic Scholar (enrichment) + arXiv + NASA NTRS

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
    S2_REQUESTS_PER_SECOND, S2_MAX_RETRIES, MAX_PAPERS_PER_POST
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

def search_openalex(days: int = LOOKBACK_DAYS) -> dict:
    """
    Query OpenAlex API for papers matching our keywords.
    Returns dict of {doi: paper_dict} for deduplication.
    """
    print(f"\n📡 [OpenAlex] Searching last {days} days...")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    candidates = {}

    for keyword in KEYWORDS:
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

            # Rule 1: Tier 1 journal → always keep
            if tier == 1:
                keep = True
                reason = f"Tier 1: {journal}"

            # Rule 2: Tier 2 + elite institution → keep
            elif tier == 2 and is_elite:
                keep = True
                reason = f"Tier 2 + Elite ({inst_name})"

            # Rule 3: Tier 2 + high citations → keep (velocity checked later)
            elif tier == 2 and cited_by >= 3:
                keep = True
                reason = f"Tier 2 + Citations ({cited_by})"

            # Rule 4: arXiv/preprint + elite institution → keep
            elif "arxiv" in journal.lower() and is_elite:
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

def search_arxiv(existing_dois: set) -> dict:
    """
    Query arXiv for recent preprints in physics.flu-dyn and physics.ao-ph.
    Only keeps papers from elite institutions (checked via author affiliations in text).
    """
    print(f"\n📡 [arXiv] Searching recent preprints...")
    candidates = {}

    # arXiv categories relevant to us
    categories = ["physics.flu-dyn", "physics.ao-ph", "cs.CE"]

    for keyword in KEYWORDS[:6]:  # Use top keywords only
        query = f"all:{keyword}"
        url = "http://export.arxiv.org/api/query"
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
            # arXiv doesn't always have structured affiliations, so we check
            # the summary text and author names as proxies
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

def search_nasa_ntrs() -> dict:
    """
    Query NASA Technical Reports Server for recent publications.
    These are gold-tier sources for reentry aerothermodynamics.
    """
    print(f"\n📡 [NASA NTRS] Searching technical reports...")
    candidates = {}

    for keyword in KEYWORDS[:6]:
        url = "https://ntrs.nasa.gov/api/citations/search"
        params = {
            "q": keyword,
            "sort": "dateSort desc",
            "page": {"size": 10, "from": 0},
        }

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

            # Check publication date (NTRS format varies)
            pub_date = item.get("publicationDate", "")
            if pub_date:
                try:
                    pd = datetime.strptime(pub_date[:10], "%Y-%m-%d")
                    if pd < datetime.now() - timedelta(days=LOOKBACK_DAYS * 2):
                        continue  # Too old
                except ValueError:
                    pass  # Keep if date is unparseable

            dedup_key = f"ntrs:{ntrs_id}"
            if dedup_key in candidates:
                continue

            # Extract authors
            authors = []
            for author in item.get("authorList", []):
                name = author.get("name", "")
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
                    # Rate limited — wait and retry
                    wait = (attempt + 1) * 5
                    print(f"   ⏳ Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue

                else:
                    # Paper not found in S2 — keep if Tier 1
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

def rank_and_select(papers: list) -> list:
    """
    Rank papers by quality score and select top N for summarization.
    Score = tier_bonus + citation_velocity + influential_citations + recency_bonus
    """
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

    # Select top papers
    selected = papers[:MAX_PAPERS_PER_POST]

    return selected


# ──────────────────────────────────────────────
#  MAIN ENTRY POINT
# ──────────────────────────────────────────────

def run_hunt(dry_run: bool = False) -> list:
    """
    Execute the full hunting pipeline.
    Returns list of selected papers ready for summarization.
    """
    print("=" * 60)
    print(f"🚀 AEROSENTINEL HUNTER — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 1. Load history
    seen_dois = load_history()
    print(f"📚 History: {len(seen_dois)} previously seen papers")

    # 2. Search all sources
    openalex_papers = search_openalex()
    arxiv_papers = search_arxiv(set(openalex_papers.keys()) | seen_dois)
    ntrs_papers = search_nasa_ntrs()

    # 3. Merge all sources (DOI-based dedup)
    all_papers = {}
    all_papers.update(openalex_papers)
    all_papers.update(arxiv_papers)
    all_papers.update(ntrs_papers)

    # 4. Remove previously seen
    new_papers = {
        doi: paper for doi, paper in all_papers.items()
        if doi not in seen_dois
    }
    print(f"\n📊 Total: {len(all_papers)} found, {len(new_papers)} are new")

    if not new_papers:
        print("\n✅ No new papers found. The field is quiet today.")
        return []

    # 5. Enrich with Semantic Scholar
    enriched = enrich_with_semantic_scholar(list(new_papers.values()))

    # 6. Apply Tier 2 citation velocity filter
    # Papers that are Tier 2 without elite institution need velocity >= threshold
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
    selected = rank_and_select(filtered)

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
