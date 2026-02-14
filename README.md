# AeroSentinel

[![Hugo](https://img.shields.io/badge/Hugo-PaperMod-blue?logo=hugo)](https://gohugo.io/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/sezersivri/aerosentinel/actions)
[![Bilingual](https://img.shields.io/badge/lang-EN%20%7C%20TR-brightgreen)](#)
[![Cost](https://img.shields.io/badge/cost-%240%2Fmonth-success)](#cost-0month)

**Automated Research Feed for Aerospace & Hypersonic Aerothermodynamics**

AeroSentinel scans 7 academic databases on a weekly schedule, filters and ranks papers
using a priority keyword system, generates bilingual (EN/TR) AI summaries via Gemini 2.5 Flash,
and publishes approved posts to a Hugo static site -- all through a Telegram-driven approval
workflow. Total cost: **$0/month**.

---

## Architecture

```
GitHub Actions (cron: weekly Saturday 08:00 UTC)
  |
  |  scout.yml
  v
+-----------------------------------------------------+
|                 SCOUT PIPELINE (Python)              |
|                                                      |
|  HUNTER ─────────────────> BRAIN ────────> NOTIFIER  |
|  7 sources:                Gemini 2.5      Telegram  |
|   - OpenAlex               Flash            preview  |
|   - Crossref              (bilingual        with     |
|   - CORE                   EN/TR            approve/ |
|   - Semantic Scholar        summaries)      edit/    |
|   - arXiv                                   discard  |
|   - NASA NTRS                               buttons  |
|   - IEEE Xplore                                      |
+-----------------------------------------------------+
                                   |
                     User taps button in Telegram
                                   |
                                   v
                      +------------------------+
                      | Cloudflare Worker      |
                      | (webhook bridge)       |
                      | /scout /search /bibtex |
                      | /bookmarks /status     |
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

## Features

- **7 Academic Sources** -- OpenAlex, Crossref, CORE, Semantic Scholar, arXiv, NASA NTRS, IEEE Xplore
- **Two-Tier Digests** -- Core papers (aerodynamic heating & AI/ML) get full solo reviews; peripheral papers are synthesized into a flowing academic narrative with in-text citations
- **AI Summaries** -- Gemini 2.5 Flash generates structured, bilingual research digests with model attribution
- **Interactive Search** -- `/search` command: pick tags, set date range, trigger a custom paper hunt from Telegram
- **BibTeX Export** -- `/bibtex` command returns citation entries for the latest digest
- **Bookmarks** -- Star button on Telegram previews to save papers for later; `/bookmarks` to list them
- **Usage Tracking** -- Pipeline stats (papers found/selected, API calls, duration) after each run
- **Weekly Stats** -- Automated digest of pipeline activity over the past 4 weeks
- **Bilingual** -- Every post published in both English and Turkish
- **Telegram Approval** -- Preview drafts with one-tap Approve / Edit / Discard / Bookmark buttons
- **Cloudflare Worker** -- Webhook bridge with KV-backed search sessions; handles 6 commands
- **Full-Text Search** -- Client-side Fuse.js search via PaperMod JSON index
- **RSS Feed** -- Full-text RSS for feed readers
- **Privacy First** -- No analytics, no tracking, no cookies

## File Structure

```
aerosentinel/
├── .github/workflows/
│   ├── scout.yml                 # Weekly paper hunt + summarize + notify
│   ├── publish.yml               # Telegram approval -> Hugo build -> deploy
│   └── search.yml                # Custom /search from Telegram -> parameterized hunt
├── content/
│   ├── drafts/                   # AI-generated drafts awaiting approval
│   ├── posts/                    # Published posts
│   └── ...                       # About, archives, search pages (EN + TR)
├── src/
│   ├── __init__.py               # Package init with version
│   ├── config.py                 # Settings, keyword tiers, curated tags, core focus
│   ├── hunter.py                 # Paper discovery (7 sources, parameterized search)
│   ├── brain.py                  # Gemini analysis (two-tier: core + peripheral)
│   ├── notifier.py               # Telegram notifications + bookmark button
│   └── pipeline.py               # Orchestrator + custom search + usage tracking
├── worker/
│   ├── index.js                  # Cloudflare Worker (/search, /bibtex, /bookmarks, KV)
│   └── wrangler.toml             # Wrangler config + KV namespace binding
├── themes/
│   └── PaperMod/                 # Hugo theme (git submodule)
├── hugo.yaml                     # Hugo site config (bilingual, PaperMod)
├── seen_papers.json              # Deduplication history
├── usage_stats.json              # Pipeline usage/quota tracking
├── requirements.txt              # Python dependencies
├── VERSION                       # Semantic version (2.3.0)
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

npx wrangler secret put TELEGRAM_BOT_TOKEN
npx wrangler secret put GITHUB_TOKEN
npx wrangler secret put GITHUB_REPO     # e.g. sezersivri/aerosentinel
npx wrangler secret put AUTHORIZED_CHAT_ID  # your Telegram chat ID
npx wrangler deploy
```

Then set the Telegram webhook to your Worker URL:

```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<worker>.workers.dev/webhook
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

### Telegram Commands

| Command | Description |
|---------|-------------|
| `/scout` | Trigger a paper hunt now |
| `/search` | Interactive search: pick tags, set date range |
| `/bibtex` | Export latest digest as BibTeX |
| `/bookmarks` | View your bookmarked digests |
| `/status` | Check latest workflow status |
| `/help` | Show available commands |

## Hosting & Branches

AeroSentinel is hosted for free on **GitHub Pages** — GitHub's built-in static site hosting service.

- **What is GitHub Pages?** A free hosting service from GitHub that serves static websites directly from a repository. You get a free subdomain at `yourusername.github.io/reponame` with optional custom domain support. Limits: 1 GB storage, 100 GB bandwidth/month — more than enough for a research blog.

- **Why two branches?**

  | Branch | Purpose |
  |--------|---------|
  | `main` | Source code — Python pipeline, Hugo content, configuration, workflows |
  | `gh-pages` | Built output — auto-generated HTML/CSS/JS that GitHub Pages serves as the live site |

  You only work on `main`. The `gh-pages` branch is managed automatically by the deploy workflow — every time a post is approved, GitHub Actions runs `hugo build --minify` and pushes the output to `gh-pages`. **Never edit `gh-pages` directly.**

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

## Credits

Architecture co-designed with Claude (Anthropic). AI summaries powered by Gemini (Google).
Built for aerospace engineers who want to stay on the cutting edge.
