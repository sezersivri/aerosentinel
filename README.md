# AeroSentinel

[![Hugo](https://img.shields.io/badge/Hugo-PaperMod-blue?logo=hugo)](https://gohugo.io/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/sezersivri/aerosentinel/actions)
[![Bilingual](https://img.shields.io/badge/lang-EN%20%7C%20TR-brightgreen)](#)
[![Cost](https://img.shields.io/badge/cost-%240%2Fmonth-success)](#cost-0month)

**Automated Research Intelligence for Aerospace & Hypersonic Aerothermodynamics**

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
                      | /scout /status /help   |
                      | + callback buttons     |
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
- **AI Summaries** -- Gemini 2.5 Flash generates structured, narrative research digests
- **Bilingual** -- Every post published in both English and Turkish
- **Telegram Approval** -- Preview drafts with one-tap Approve / Edit / Discard buttons
- **Cloudflare Worker** -- Zero-redirect webhook bridge; handles `/scout`, `/status`, `/help` commands
- **Full-Text Search** -- Client-side Fuse.js search via PaperMod JSON index
- **Share Buttons** -- Telegram, LinkedIn, Reddit, X
- **Edit on GitHub** -- "Suggest Edit" link on every post
- **Table of Contents** -- Auto-generated ToC on long posts
- **Collapsible Sections** -- `<details>` support for technical deep-dives
- **RSS Feed** -- Full-text RSS for feed readers
- **Privacy First** -- No analytics, no tracking, no cookies

## File Structure

```
aerosentinel/
├── .github/workflows/
│   ├── scout.yml                 # Weekly paper hunt + summarize + notify
│   └── publish.yml               # Telegram approval -> Hugo build -> deploy
├── content/
│   ├── drafts/                   # AI-generated drafts awaiting approval
│   ├── posts/                    # Published posts
│   ├── about.en.md               # About page (English)
│   ├── about.tr.md               # About page (Turkish)
│   ├── archives.en.md            # Archive page (English)
│   ├── archives.tr.md            # Archive page (Turkish)
│   ├── search.en.md              # Search page (English)
│   └── search.tr.md              # Search page (Turkish)
├── src/
│   ├── __init__.py               # Package init with version
│   ├── config.py                 # All configuration & keyword tiers
│   ├── hunter.py                 # Paper discovery engine (7 sources)
│   ├── brain.py                  # Gemini 2.5 Flash summarization
│   ├── notifier.py               # Telegram notifications
│   └── pipeline.py               # Main orchestrator
├── static/
│   └── favicon.svg               # Site favicon
├── worker/
│   ├── index.js                  # Cloudflare Worker webhook bridge
│   └── wrangler.toml             # Wrangler deployment config
├── themes/
│   └── PaperMod/                 # Hugo theme (git submodule)
├── hugo.yaml                     # Hugo site config (bilingual, PaperMod)
├── seen_papers.json              # Deduplication history
├── requirements.txt              # Python dependencies
├── VERSION                       # Semantic version
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
npx wrangler secret put TELEGRAM_BOT_TOKEN
npx wrangler secret put GITHUB_TOKEN
npx wrangler secret put GITHUB_REPO     # e.g. sezersivri/aerosentinel
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

## Cost: $0/month

| Service             | Tier          | Limit                  |
|---------------------|---------------|------------------------|
| GitHub Actions      | Free          | 2,000 min/month        |
| GitHub Pages        | Free          | 100 GB bandwidth       |
| Cloudflare Worker   | Free          | 100,000 requests/day   |
| Gemini 2.5 Flash    | Free          | Generous rate limits    |
| Telegram Bot API    | Free          | Unlimited              |
| Academic APIs       | Free/Open     | Rate-limited           |

**Total: $0/month** -- entirely within free tiers.

## Credits

Architecture co-designed with Claude (Anthropic). AI summaries powered by Gemini (Google).
Built for aerospace engineers who want to stay on the cutting edge.
