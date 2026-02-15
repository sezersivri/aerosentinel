# AeroSentinel

[![Hugo](https://img.shields.io/badge/Hugo-PaperMod-blue?logo=hugo)](https://gohugo.io/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/sezersivri/aerosentinel/actions)
[![Bilingual](https://img.shields.io/badge/lang-EN%20%7C%20TR-brightgreen)](#)
[![Cost](https://img.shields.io/badge/cost-%240%2Fmonth-success)](#cost-0month)
[![Version](https://img.shields.io/badge/version-2.4.0-orange)](#changelog)

**Automated Research Intelligence for Aerospace & Hypersonic Aerothermodynamics**

AeroSentinel is an automated academic paper intelligence system built for a specific thesis domain:
**"Prediction of Aerodynamic Heating on High-Speed Missiles Using Gaussian Process Based Surrogate Models."**

It continuously scans 7 academic databases, filters and ranks papers using a multi-tier quality system,
classifies them into core (aerodynamic heating & AI/ML in aerodynamics) and peripheral research,
generates bilingual (EN/TR) AI-powered research digests via Gemini 2.5 Flash,
and publishes approved briefings to a Hugo static site -- all orchestrated through Telegram with
one-tap approval. Total cost: **$0/month**.

**Live site:** [sezersivri.github.io/aerosentinel](https://sezersivri.github.io/aerosentinel/)

---

## Architecture

```
GitHub Actions (cron: weekly Saturday 08:00 UTC)
  |
  |  scout.yml (concurrency-controlled)
  v
+-------------------------------------------------------------+
|                  SCOUT PIPELINE (Python)                     |
|                                                              |
|  HUNTER ──────> ENRICHMENT ──────> BRAIN ──────> NOTIFIER    |
|  7 sources:    Semantic Scholar    Gemini 2.5    Telegram    |
|   - OpenAlex   (citations,         Flash         preview    |
|   - Crossref    velocity,          (bilingual     with      |
|   - CORE        abstracts)          two-tier      approve/  |
|   - arXiv                           analysis)     edit/     |
|   - NASA NTRS                                     discard/  |
|   - IEEE Xplore                                   bookmark  |
|   - Semantic Scholar                              buttons   |
+-------------------------------------------------------------+
        |                                    |
        |  Title dedup, score gate,          |  Anti-slop filter,
        |  recency gate, thesis bypass       |  tag normalization,
        |                                    |  schema validation
        v                                    v
+-------------------------------------------------------------+
|              QUALITY GATES                                   |
|                                                              |
|  MIN_HUNTER_SCORE: 30    MAX_PAPER_AGE_DAYS: 90             |
|  MIN_PERIPHERAL_SCORE: 20    Title-based deduplication       |
|  Tier 1/2 journal filter    Thesis/dissertation bypass       |
|  arXiv: category + topic relevance + elite institution       |
+-------------------------------------------------------------+
                              |
                User taps button in Telegram
                              |
                              v
                 +------------------------+
                 | Cloudflare Worker      |
                 | (webhook bridge)       |
                 | /scout /search /bibtex |
                 | /bookmarks /status     |
                 | /help                  |
                 | KV-backed sessions     |
                 +------------------------+
                              |
                repository_dispatch event
                              |
                              v
                 +------------------------+
                 | GitHub Actions         |
                 | publish.yml            |
                 |  - Move draft to posts |
                 |  - Hugo build --minify |
                 |  - Deploy to GH Pages  |
                 +------------------------+
                              |
                              v
                 +------------------------+
                 |   GitHub Pages (LIVE)  |
                 | sezersivri.github.io/  |
                 |       aerosentinel     |
                 +------------------------+
```

## Thesis Domain

This system is specifically tuned for research related to:

> **"Prediction of Aerodynamic Heating on High-Speed Missiles Using Gaussian Process Based Surrogate Models"**

**Core focus areas** (papers get full individual deep-dive reviews):
- Aerodynamic heating prediction, measurement, and simulation
- Stagnation point heating, surface heat flux, thermal protection systems
- AI/ML surrogates for aerodynamics (Gaussian process, neural networks, deep learning)
- Physics-informed neural networks for CFD
- Data-driven aerodynamic prediction methods

**Peripheral coverage** (grouped into academic narrative with citations):
- Broader hypersonic/supersonic flow physics
- General computational fluid dynamics
- Shock-boundary layer interaction, boundary layer transition
- Scramjet propulsion, reentry physics
- Experimental aerothermodynamics

## Features

### Paper Discovery & Filtering
- **7 Academic Sources** -- OpenAlex, Crossref, CORE, Semantic Scholar, arXiv, NASA NTRS, IEEE Xplore
- **3-Tier Journal Filter** -- Tier 1 (AIAA, JFM, PoF) always kept; Tier 2 requires elite institution or citation velocity; Tier 0 blocked except theses
- **Thesis Discovery** -- Crossref dissertations and CORE theses bypass the tier-0 filter, enabling discovery of PhD/MSc work in the field
- **arXiv Category Gating** -- Restricted to physics.flu-dyn, physics.ao-ph, physics.comp-ph, cs.CE with aerospace topic relevance check
- **Title Deduplication** -- Same paper from different sources merged by normalized title comparison
- **Recency Gate** -- Papers older than 90 days rejected (this is a news platform)
- **Score Threshold** -- Papers below score 30 dropped; below 20 discarded entirely

### AI Analysis
- **Two-Tier Digests** -- Core papers (aerodynamic heating & AI/ML) get full solo reviews with methodology, key numbers, limitations, and cross-paper connections; peripheral papers synthesized into flowing academic narrative with [N] in-text citations
- **9 Paper Types** -- ml_heating, ml_aerodynamics, ml_transition, numerical_cfd, experimental, analytical, review, multi_method, thesis
- **36 Curated Tags** -- Strict English-only vocabulary across 6 categories (research domains, methodologies, physical phenomena, flow regimes, applications, cross-cutting)
- **Critical Analysis** -- Limitations field identifies methodological weaknesses and evidence strength
- **Anti-Slop Filter** -- 24 banned AI filler phrases in prompts + post-generation regex scrub
- **Missing Abstract Handling** -- Papers without abstracts flagged as [NO ABSTRACT] for title-only classification
- **Bilingual** -- Every post in English and Turkish with forced English tags

### Telegram Bot
- **Interactive Commands** -- `/scout`, `/search`, `/bibtex`, `/bookmarks`, `/status`, `/help`
- **Custom Search** -- Pick from 36 curated tags, set date range, trigger parameterized hunt
- **One-Tap Approval** -- Publish / Edit / Discard / Bookmark inline buttons
- **HTML-Safe Messages** -- Scientific text with `<`, `>`, `&` properly escaped
- **Message Splitting** -- Long messages auto-split to respect Telegram's 4096-char limit
- **Session Management** -- Expired search sessions detected with helpful feedback

### Infrastructure
- **Cloudflare Worker** -- Webhook bridge with KV-backed search sessions and bookmarks
- **Workflow Security** -- Shell injection protection (client_payload in env: blocks only)
- **Concurrency Control** -- All workflows share a concurrency group to prevent parallel conflicts
- **Usage Tracking** -- Gemini token counts, API calls per source, duration -- persisted to usage_stats.json
- **Weekly Stats** -- `/weekly-stats` CLI command for pipeline activity summary
- **Full-Text Search** -- Client-side Fuse.js via PaperMod JSON index
- **RSS Feed** -- Full-text RSS for feed readers
- **Privacy First** -- No analytics, no tracking, no cookies

## File Structure

```
aerosentinel/
├── .github/workflows/
│   ├── scout.yml                 # Weekly paper hunt + summarize + notify
│   ├── publish.yml               # Telegram approval -> Hugo build -> deploy
│   └── search.yml                # Custom /search from Telegram
├── content/
│   ├── drafts/                   # AI-generated drafts awaiting approval
│   ├── posts/                    # Published posts (EN + TR)
│   └── ...                       # About, archives, search pages
├── src/
│   ├── __init__.py               # Package init with version
│   ├── config.py                 # Keywords, journal tiers, curated tags, thresholds
│   ├── hunter.py                 # Paper discovery (7 APIs, scoring, dedup, thesis bypass)
│   ├── brain.py                  # Gemini analysis (two-tier, anti-slop, limitations)
│   ├── notifier.py               # Telegram (HTML-safe, message splitting)
│   └── pipeline.py               # Orchestrator + search + usage tracking + tag normalization
├── worker/
│   ├── index.js                  # Cloudflare Worker (commands, callbacks, KV sessions)
│   └── wrangler.toml             # Wrangler config + KV namespace binding
├── themes/
│   └── PaperMod/                 # Hugo theme (git submodule)
├── hugo.yaml                     # Hugo site config (bilingual, PaperMod)
├── seen_papers.json              # Deduplication history
├── usage_stats.json              # Pipeline usage tracking (tokens, calls, duration)
├── requirements.txt              # Python dependencies
├── VERSION                       # Semantic version (2.4.0)
└── README.md
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/sezersivri/aerosentinel.git
cd aerosentinel
git submodule update --init --recursive
pip install -r requirements.txt
```

### 2. GitHub Secrets

Set these in **Settings > Secrets and variables > Actions**:

| Secret              | Description                          |
|---------------------|--------------------------------------|
| `GEMINI_API_KEY`    | Google AI Studio API key             |
| `TELEGRAM_BOT_TOKEN`| Telegram bot token from @BotFather  |
| `TELEGRAM_CHAT_ID` | Your Telegram chat/group ID          |
| `IEEE_API_KEY`      | IEEE Xplore API key (optional)       |

`GITHUB_TOKEN` is provided automatically by GitHub Actions.

### 3. Deploy Cloudflare Worker

```bash
cd worker
npx wrangler login

# Create KV namespace for search sessions & bookmarks
npx wrangler kv:namespace create SEARCH_SESSIONS
# Copy the ID into wrangler.toml

npx wrangler secret put TELEGRAM_TOKEN
npx wrangler secret put GITHUB_TOKEN
npx wrangler secret put GITHUB_REPO          # e.g. sezersivri/aerosentinel
npx wrangler secret put AUTHORIZED_CHAT_ID   # your Telegram chat ID
npx wrangler deploy
```

Then set the Telegram webhook:

```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<worker>.workers.dev/
```

### 4. Hugo theme

The PaperMod theme is included as a git submodule. If missing:

```bash
git submodule add https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod
```

### 5. Run

- **Manual trigger:** Go to Actions > "AeroSentinel Scout" > Run workflow
- **Telegram:** Send `/scout` to your bot
- **Automatic:** Runs every Saturday at 08:00 UTC

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/scout` | Trigger a paper hunt now |
| `/search` | Interactive search: pick from 36 tags, set date range |
| `/bibtex` | Export latest digest as BibTeX |
| `/bookmarks` | View your bookmarked digests |
| `/status` | Check latest workflow status |
| `/help` | Show available commands |

## Data Flow

1. **Hunter** searches 7 APIs using 22 keyword phrases across 3 priority tiers
2. **Recency gate**: papers older than 90 days rejected
3. **Score gate**: papers below score 30 dropped; below 20 discarded entirely
4. **Title dedup**: normalized title comparison removes cross-source duplicates
5. **Two-tier classification**: papers matching core focus keywords become **core papers** (solo reviews); rest become **peripheral papers** (academic narrative with [N] citations)
6. **Brain** sends papers to Gemini with structured prompts; enforces two-tier JSON schema with retry
7. **Anti-slop**: 24 banned phrases stripped from generated text
8. **Tag normalization**: validated against 36-tag curated English vocabulary
9. **Notifier** sends Telegram preview with Publish/Edit/Discard/Bookmark buttons
10. **Publish** moves drafts to posts, rebuilds Hugo site, deploys to GitHub Pages

## Hosting & Branches

AeroSentinel is hosted for free on **GitHub Pages**.

| Branch | Purpose |
|--------|---------|
| `main` | Source code -- Python pipeline, Hugo content, configuration, workflows |
| `gh-pages` | Built output -- auto-generated HTML/CSS/JS served as the live site |

You only work on `main`. The `gh-pages` branch is managed automatically -- every time a post is approved, GitHub Actions runs `hugo build --minify` and pushes the output to `gh-pages`. **Never edit `gh-pages` directly.**

## Cost: $0/month

| Service             | Tier          | Limit                  |
|---------------------|---------------|------------------------|
| GitHub Actions      | Free          | 2,000 min/month        |
| GitHub Pages        | Free          | 100 GB bandwidth       |
| Cloudflare Worker   | Free          | 100K req/day, 1K KV writes/day |
| Gemini 2.5 Flash    | Free          | Generous rate limits    |
| Telegram Bot API    | Free          | Unlimited              |
| Academic APIs       | Free/Open     | Rate-limited           |

**Total: $0/month** -- entirely within free tiers.

## Changelog

### v2.4.0 (Feb 2026) -- Quality, Robustness & Thesis Discovery
- Shell injection fix in workflow files; concurrency control across all workflows
- `date_to` filtering implemented across API sources
- Semantic Scholar retry exhaustion fix (papers no longer silently dropped)
- Title-based deduplication across sources
- Thesis/dissertation discovery (tier-0 bypass for Crossref/CORE)
- New `thesis` paper type and `Thesis Research` tag
- Two-tier schema enforced with retry/auto-convert
- Anti-slop: 24 banned phrases + `clean_slop()` post-processing
- Critical analysis with limitations field; missing abstract handling
- Turkish tag normalization fallback; token usage persistence
- Telegram: 4096-char guard, HTML escape, message splitting
- Worker: dynamic BibTeX year, expired session feedback
- arXiv restricted to aerospace categories with topic relevance check
- MIN_HUNTER_SCORE raised from 25 to 30

### v2.3.0 (Feb 2026) -- Two-Tier Digests & Interactive Search
- Two-tier post structure (core + peripheral papers)
- Interactive `/search` command with tag selection and date ranges
- `/bibtex`, `/bookmarks` commands via Cloudflare KV
- Usage tracking and weekly stats
- Cloudflare Worker replaced Google Apps Script

### v2.2.0 (Feb 2026) -- Quality Filtering
- 35 curated tags, 8 paper types, scoring thresholds, tag normalization

## Credits

Architecture co-designed with [Claude](https://claude.ai) (Anthropic). AI summaries powered by [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) (Google). Built for aerospace researchers tracking the frontier of aerodynamic heating prediction and ML surrogates for CFD.
