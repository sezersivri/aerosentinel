# 🛰️ AeroSentinel

**Automated Research Intelligence for Aerospace & Hypersonic Aerothermodynamics**

Every 2 days, AeroSentinel scans top academic databases, filters for high-quality papers,
generates AI summaries via Gemini 2.5 Pro, and publishes to your blog — all for $0/month.

## Architecture

```
GitHub Actions (cron every 2 days)
  │
  ├── HUNTER: OpenAlex + Semantic Scholar + arXiv + NASA NTRS
  ├── BRAIN: Gemini 2.5 Pro → narrative synthesis
  └── NOTIFIER: Telegram preview → [✅ Publish] [✏️ Edit] [🗑️ Discard]
                    │
                    ▼
              Google Apps Script (free webhook bridge)
                    │
                    ▼
              GitHub Actions → Hugo build → GitHub Pages (LIVE)
```

## Cost: $0/month (all free tiers)

## File Structure

```
aerosentinel/
├── .github/workflows/
│   ├── scout.yml              # Scheduled hunt + summarize + notify
│   └── publish.yml            # Triggered by Telegram approval
├── content/
│   ├── drafts/                # AI-generated drafts awaiting approval
│   ├── posts/                 # Published posts
│   ├── about.md
│   └── archives.md
├── scripts/
│   └── google_apps_script.js  # Telegram ↔ GitHub webhook bridge
├── src/
│   ├── config.py              # All configuration
│   ├── hunter.py              # Paper discovery engine
│   ├── brain.py               # Gemini 2.5 Pro summarization
│   ├── notifier.py            # Telegram notifications
│   └── pipeline.py            # Main orchestrator
├── hugo.yaml                  # Hugo site config (PaperMod theme)
├── seen_papers.json           # Deduplication history
├── CLAUDE_CODE_PLAN.md        # Deployment instructions for Claude Code
└── README.md
```

## Setup

See `CLAUDE_CODE_PLAN.md` for full deployment instructions.

### Quick Start
1. Set GitHub Secrets: `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
2. Install Hugo theme: `git submodule add https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod`
3. Deploy Google Apps Script (see `scripts/google_apps_script.js`)
4. Push to GitHub → Go to Actions → Run "Scout" manually
5. Check Telegram for your first draft preview

## Credits

Architecture co-designed by Claude (Anthropic) and Gemini (Google).
Built for aerospace engineers who want to stay on the cutting edge.
