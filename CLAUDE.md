# AeroSentinel

Automated academic paper feed for aerospace research, focused on the thesis domain: **"Prediction of Aerodynamic Heating on High-Speed Missiles Using Gaussian Process Based Surrogate Models."**

## Architecture

```
GitHub Actions (cron/webhook)
  -> Hunter (7 academic APIs)
    -> Brain (Gemini LLM analysis, bilingual EN/TR)
      -> Notifier (Telegram preview + inline buttons)
        -> Cloudflare Worker (callback handler)
          -> Hugo Publish (GitHub Pages)
```

## Key Files

| File | Purpose |
|------|---------|
| `src/config.py` | All settings: API keys, keyword tiers, journal tiers, curated tag vocabulary, thresholds |
| `src/hunter.py` | Multi-source paper search (OpenAlex, arXiv, NASA NTRS, Crossref, CORE, IEEE, Semantic Scholar), scoring & ranking |
| `src/brain.py` | Gemini system prompts, single-paper analysis, Hugo post generation, paper type badges |
| `src/pipeline.py` | Orchestrator: hunt -> brain -> normalize/validate -> notify -> publish/discard |
| `src/notifier.py` | Telegram Bot API integration (previews, confirmations, status messages) |
| `worker/index.js` | Cloudflare Worker webhook bridge (Telegram commands, callbacks, search sessions) |
| `worker/wrangler.toml` | Cloudflare Worker configuration (KV namespace: SEARCH_SESSIONS) |
| `.github/workflows/search.yml` | Custom search workflow (triggered by `/search` command) |
| `usage_stats.json` | API usage tracking (Gemini tokens, API calls per source) |
| `scripts/google_apps_script.js` | **LEGACY** — Old webhook bridge, replaced by `worker/index.js` |
| `VERSION` | Semantic version (current: 2.5.0) |

## Data Flow

1. **Hunter** searches 7 APIs using keyword tiers, applies journal/institution filters
2. **Recency gate**: papers older than `MAX_PAPER_AGE_DAYS` (90 days) are rejected — this is a NEWS platform
3. **Score gate**: papers below `MIN_HUNTER_SCORE` (30) are dropped
4. **Brain** analyzes each paper individually with Gemini, generates bilingual (EN/TR) prose review; usage tracked in `usage_stats.json`
5. **Normalization**: tags validated against 36-tag curated vocabulary, paper types validated
6. **Notifier** sends Telegram preview per paper with Publish/Edit/Discard/Bookmark buttons
7. **Publish** moves drafts from `content/drafts/` to `content/posts/`

## Post Format

Each paper gets its own individual blog post with:
- **Badge line**: `Type: 🤖 ML/Heating Prediction | Relevance: 95/100`
- **Summary**: 2-3 paragraphs of natural flowing prose (no bullet points, no structured sections)
- **Reference**: Full citation with DOI link

The system selects 1-2 best papers per hunt cycle. No batch digests.

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/scout` | Trigger a paper hunt now |
| `/search` | Interactive custom search with tag selection & date range (uses Cloudflare KV sessions) |
| `/bibtex` | Export latest digest as BibTeX |
| `/bookmarks` | View bookmarked digests |
| `/status` | Check latest workflow status |
| `/help` | Show available commands |

## Curated Tag Vocabulary (36 tags)

Tags are defined in `src/config.py` → `CURATED_TAGS`. Tags are ALWAYS in English, even for Turkish posts.

**Research Domains:** Aerothermodynamics, Hypersonic Aerodynamics, Supersonic Aerodynamics, Thermal Protection Systems, Flight Vehicle Design, Reentry Physics, Scramjet Propulsion

**Methodologies:** Gaussian Process Surrogates, Neural Network Surrogates, Deep Learning, Multi-Fidelity Modeling, Design Optimization, Reduced-Order Modeling, Data-Driven Methods, Analytical Methods

**Physical Phenomena:** Stagnation Point Heating, Shock-Boundary Layer Interaction, Real Gas Effects, Turbulent Heating, Radiative Heating, Ablation Modeling, Laminar Heating, Entropy Layer Effects

**Flow Regimes:** Hypersonic Flow, High Enthalpy Flow, Rarefied Flow

**Applications:** Missile Aerothermodynamics, Reentry Vehicles, Launch Vehicles, Planetary Entry

**Cross-Cutting:** Heat Flux Prediction, Surrogate Modeling, High-Performance Computing, Review Paper, Thesis Research

## Paper Types (9)

| Key | EN Badge | TR Badge |
|-----|----------|----------|
| `ml_heating` | ML/Heating Prediction | MO/Isinma Tahmini |
| `ml_aerodynamics` | ML/Aerodynamics | MO/Aerodinamik |
| `ml_transition` | ML/Transition | MO/Gecis Tahmini |
| `numerical_cfd` | Numerical/CFD | Sayisal/HAD |
| `experimental` | Experimental | Deneysel |
| `analytical` | Analytical | Analitik |
| `review` | Review | Derleme |
| `multi_method` | Multi-Method | Coklu Yontem |
| `thesis` | Thesis/Dissertation | Tez/Doktora |

## Development

```bash
# Test hunter only (dry run, no history saved)
python -m src.pipeline --hunt-only

# Full pipeline (hunt + brain + notify)
python -m src.pipeline

# Publish approved drafts
python -m src.pipeline --publish FILENAME_BASE

# Discard rejected drafts
python -m src.pipeline --discard FILENAME_BASE

# Custom search (from Telegram /search or CLI)
python -m src.pipeline --search '{"tags":["Aerothermodynamics","Deep Learning"],"date_from":"2024-01","date_to":"now"}'

# Weekly usage stats
python -m src.pipeline --weekly-stats

# Test Telegram connection
python -m src.notifier
```

## Conventions

- Python 3.10+, no external type stubs
- Secrets via environment variables (GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, etc.) — never hardcoded
- Emoji in print statements for CLI readability
- Hugo frontmatter uses YAML format
- All tags always in English (cross-language consistency)
- Paper dates must be parseable and within MAX_PAPER_AGE_DAYS to be included
