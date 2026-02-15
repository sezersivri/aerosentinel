/**
 * AeroSentinel v2.5 — Cloudflare Worker Webhook Bridge
 * Replaces Google Apps Script. No 302 redirect issues.
 * Free tier: 100K requests/day.
 *
 * Uses Telegram webhook-reply method: returns the API call in the HTTP
 * response body instead of making a separate outbound fetch to api.telegram.org.
 */

const CURATED_TAGS = {
  "Research Domains": [
    "Aerothermodynamics", "Hypersonic Aerodynamics", "Supersonic Aerodynamics",
    "Thermal Protection Systems", "Flight Vehicle Design", "Reentry Physics",
    "Scramjet Propulsion"
  ],
  "Methodologies": [
    "Gaussian Process Surrogates", "Neural Network Surrogates", "Deep Learning",
    "Multi-Fidelity Modeling", "Design Optimization", "Reduced-Order Modeling",
    "Data-Driven Methods", "Analytical Methods"
  ],
  "Physical Phenomena": [
    "Stagnation Point Heating", "Shock-Boundary Layer Interaction", "Real Gas Effects",
    "Turbulent Heating", "Radiative Heating", "Ablation Modeling",
    "Laminar Heating", "Entropy Layer Effects"
  ],
  "Flow Regimes": [
    "Hypersonic Flow", "High Enthalpy Flow", "Rarefied Flow"
  ],
  "Applications": [
    "Missile Aerothermodynamics", "Reentry Vehicles", "Launch Vehicles",
    "Planetary Entry"
  ],
  "Cross-Cutting": [
    "Heat Flux Prediction", "Surrogate Modeling", "High-Performance Computing",
    "Review Paper"
  ]
};

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("AeroSentinel Bot Active", { status: 200 });
    }

    try {
      const data = await request.json();
      const config = {
        TELEGRAM_TOKEN: env.TELEGRAM_TOKEN,
        GITHUB_TOKEN: env.GITHUB_TOKEN,
        GITHUB_REPO: env.GITHUB_REPO,
        AUTHORIZED_CHAT_ID: parseInt(env.AUTHORIZED_CHAT_ID),
      };

      // Handle text messages (commands)
      if (data.message && data.message.text) {
        const chatId = data.message.chat.id;
        const text = data.message.text.trim();

        if (chatId !== config.AUTHORIZED_CHAT_ID) {
          return new Response("UNAUTHORIZED", { status: 200 });
        }

        // Check for active search session
        if (env.SEARCH_SESSIONS) {
          const sessionData = await env.SEARCH_SESSIONS.get(`search:${chatId}`, "json");
          if (sessionData && !text.startsWith("/")) {
            const reply = await handleSearchSession(config, env, chatId, text, sessionData);
            if (reply) {
              return webhookReply("sendMessage", {
                chat_id: chatId,
                text: reply,
                parse_mode: "HTML",
              });
            }
          }
        }

        const replyText = await buildCommandReply(config, env, chatId, text);
        if (replyText) {
          return webhookReply("sendMessage", {
            chat_id: chatId,
            text: replyText,
            parse_mode: "HTML",
          });
        }

        // Non-command text with no active session — likely expired search
        if (!text.startsWith("/")) {
          return webhookReply("sendMessage", {
            chat_id: chatId,
            text: "⏰ No active session. Send /search to start a new search, or /help for available commands.",
            parse_mode: "HTML",
          });
        }
        return new Response("OK", { status: 200 });
      }

      // Handle callback queries (button clicks)
      if (data.callback_query) {
        const payload = data.callback_query.data;
        const chatId = data.callback_query.message.chat.id;
        const messageId = data.callback_query.message.message_id;

        if (chatId !== config.AUTHORIZED_CHAT_ID) {
          return new Response("UNAUTHORIZED", { status: 200 });
        }

        // PUBLISH
        if (payload.startsWith("PUB_")) {
          const filenameBase = sanitizeFilename(payload.substring(4));
          triggerGitHubAction(config, "publish", filenameBase).catch(e => console.error("Publish trigger error:", e));
          // Use sendMessage via outbound fetch for multi-step callbacks
          // (webhook-reply can only return ONE method call)
          await sendMessage(config, chatId,
            "✅ Publishing both EN + TR versions! Site will update in ~2 minutes.");
          const owner = config.GITHUB_REPO.split("/")[0];
          await sendMessage(config, chatId,
            "🔗 EN: https://" + owner + ".github.io/aerosentinel/\n" +
            "🔗 TR: https://" + owner + ".github.io/aerosentinel/tr/");
          return webhookReply("answerCallbackQuery", {
            callback_query_id: data.callback_query.id,
          });
        }

        // EDIT
        else if (payload.startsWith("EDT_")) {
          const filenameBase = sanitizeFilename(payload.substring(4));
          const editUrl = "https://github.com/" + config.GITHUB_REPO + "/tree/main/content/drafts/";
          await sendMessage(config, chatId,
            "✏️ Edit the drafts on GitHub:\n" + editUrl +
            "\n\nBoth EN and TR versions are available. After editing, commit and click Publish.");

          const shortName = filenameBase.substring(0, 50);
          const keyboard = {
            inline_keyboard: [[
              { text: "✅ Publish (after edit)", callback_data: "PUB_" + shortName },
              { text: "🗑️ Discard", callback_data: "DEL_" + shortName }
            ]]
          };
          await sendMessageWithKeyboard(config, chatId, "Ready to publish the edited version?", keyboard);
          return webhookReply("answerCallbackQuery", {
            callback_query_id: data.callback_query.id,
          });
        }

        // DISCARD
        else if (payload.startsWith("DEL_")) {
          const filenameBase = sanitizeFilename(payload.substring(4));
          triggerGitHubAction(config, "discard", filenameBase).catch(e => console.error("Discard trigger error:", e));
          await editMessage(config, chatId, messageId, "🗑️ Both EN + TR drafts discarded.");
          return webhookReply("answerCallbackQuery", {
            callback_query_id: data.callback_query.id,
          });
        }

        // BOOKMARK
        else if (payload.startsWith("BKM_")) {
          const filenameBase = sanitizeFilename(payload.substring(4));
          if (env.SEARCH_SESSIONS) {
            const bookmarks = await env.SEARCH_SESSIONS.get(`bookmarks:${chatId}`, "json") || [];
            if (!bookmarks.includes(filenameBase)) {
              bookmarks.push(filenameBase);
              await env.SEARCH_SESSIONS.put(`bookmarks:${chatId}`, JSON.stringify(bookmarks));
            }
            await sendMessage(config, chatId, "⭐ Bookmarked: " + filenameBase);
          }
          return webhookReply("answerCallbackQuery", {
            callback_query_id: data.callback_query.id,
          });
        }

        return webhookReply("answerCallbackQuery", {
          callback_query_id: data.callback_query.id,
        });
      }

      return new Response("OK", { status: 200 });
    } catch (e) {
      console.error("Error:", e);
      return new Response("ERROR: " + e.message, { status: 200 });
    }
  }
};

// ─── WEBHOOK REPLY HELPER ───
function webhookReply(method, params) {
  return new Response(JSON.stringify({ method, ...params }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

// ─── FILENAME SANITIZATION ───
function sanitizeFilename(filename) {
  return filename.replace(/[^a-zA-Z0-9\-_.]/g, "");
}

// ─── BUILD COMMAND REPLY ───
async function buildCommandReply(config, env, chatId, text) {
  const command = text.toLowerCase().split(" ")[0];

  switch (command) {
    case "/scout":
      triggerGitHubAction(config, "scout", "manual").catch(e => console.error("Scout trigger error:", e));
      return "🛰️ Scout pipeline triggered! You'll receive a preview when ready.";

    case "/search":
      if (env.SEARCH_SESSIONS) {
        const { text: tagListText } = formatTagList();
        await env.SEARCH_SESSIONS.put(`search:${chatId}`, JSON.stringify({
          step: 1,
          created_at: new Date().toISOString()
        }), { expirationTtl: 600 });
        return "🔍 <b>Custom Paper Search</b>\n\n" + tagListText +
          "\nSend tag numbers (comma-separated) or custom keywords.\nExample: <code>1, 8, deep learning heating</code>";
      }
      return "⚠️ Search sessions not configured. KV namespace needed.";

    case "/bibtex":
      return await getBibtexExport(config);

    case "/bookmarks":
      if (env.SEARCH_SESSIONS) {
        const bookmarks = await env.SEARCH_SESSIONS.get(`bookmarks:${chatId}`, "json") || [];
        if (bookmarks.length === 0) return "⭐ No bookmarks yet. Use the ⭐ Bookmark button on draft previews.";
        let bmText = "⭐ <b>Your Bookmarks</b>\n\n";
        for (let i = 0; i < bookmarks.length; i++) {
          bmText += `${i + 1}. ${bookmarks[i]}\n`;
        }
        return bmText;
      }
      return "⚠️ Bookmarks not configured. KV namespace needed.";

    case "/status":
      return await getLatestWorkflowStatus(config);

    case "/help":
      return "🛰️ <b>AeroSentinel v2.5 Commands</b>\n\n" +
        "/scout — Trigger a paper hunt now\n" +
        "/search — Custom search with tags & date range\n" +
        "/bibtex — Export latest digest as BibTeX\n" +
        "/bookmarks — View your bookmarked digests\n" +
        "/status — Check latest workflow status\n" +
        "/help — Show this help message\n\n" +
        "Use the inline buttons on draft previews to Publish, Edit, Discard, or Bookmark.";

    case "/start":
      return "🛰️ <b>AeroSentinel Bot Active</b>\n\nType /help to see available commands.";

    default:
      return null;
  }
}

// ─── GITHUB WORKFLOW STATUS ───
async function getLatestWorkflowStatus(config) {
  const url = "https://api.github.com/repos/" + config.GITHUB_REPO + "/actions/runs?per_page=3";
  try {
    const resp = await fetch(url, {
      headers: {
        Authorization: "token " + config.GITHUB_TOKEN,
        Accept: "application/vnd.github.v3+json",
        "User-Agent": "AeroSentinel-Bot",
      },
    });
    const data = await resp.json();
    const runs = data.workflow_runs || [];

    if (runs.length === 0) return "📊 No recent workflow runs found.";

    let statusText = "📊 <b>Latest Workflow Runs</b>\n\n";
    for (let i = 0; i < Math.min(runs.length, 3); i++) {
      const run = runs[i];
      const icon = run.conclusion === "success" ? "✅" :
                   run.conclusion === "failure" ? "❌" :
                   run.status === "in_progress" ? "🔄" : "⏳";
      statusText += icon + " " + run.name + "\n";
      statusText += "   Status: " + (run.conclusion || run.status) + "\n";
      statusText += "   " + run.created_at.substring(0, 16).replace("T", " ") + "\n\n";
    }
    return statusText;
  } catch (e) {
    return "⚠️ Could not fetch workflow status: " + e.message;
  }
}

// ─── GITHUB ACTIONS TRIGGER ───
async function triggerGitHubAction(config, command, filename) {
  const url = "https://api.github.com/repos/" + config.GITHUB_REPO + "/dispatches";
  const eventType = command === "scout" ? "telegram_scout" : "telegram_command";

  await fetch(url, {
    method: "POST",
    headers: {
      Authorization: "token " + config.GITHUB_TOKEN,
      Accept: "application/vnd.github.v3+json",
      "Content-Type": "application/json",
      "User-Agent": "AeroSentinel-Bot",
    },
    body: JSON.stringify({
      event_type: eventType,
      client_payload: { command, filename },
    }),
  });
}

// ─── TAG HELPERS ───
function formatTagList() {
  let text = "📋 <b>Available Tags:</b>\n\n";
  let num = 1;
  const tagMap = {};
  for (const [category, tags] of Object.entries(CURATED_TAGS)) {
    text += `<b>${category}:</b>\n`;
    for (const tag of tags) {
      text += `  ${num}. ${tag}\n`;
      tagMap[num] = tag;
      num++;
    }
    text += "\n";
  }
  return { text, tagMap };
}

function resolveTagSelection(input) {
  const { tagMap } = formatTagList();
  const allTags = Object.values(CURATED_TAGS).flat();
  const parts = input.split(",").map(s => s.trim()).filter(Boolean);
  const resolved = [];
  for (const part of parts) {
    const num = parseInt(part);
    if (!isNaN(num) && tagMap[num]) {
      resolved.push(tagMap[num]);
    } else {
      // Check if it's a tag name (case-insensitive)
      const match = allTags.find(t => t.toLowerCase() === part.toLowerCase());
      if (match) resolved.push(match);
      else resolved.push(part); // Custom keyword
    }
  }
  return resolved;
}

// ─── SEARCH SESSION HANDLER ───
async function handleSearchSession(config, env, chatId, text, session) {
  if (session.step === 1) {
    // Parse tag selection
    const tags = resolveTagSelection(text);
    if (tags.length === 0) return "❌ No valid tags found. Try again or send /search to restart.";

    // Store tags and advance to step 2
    await env.SEARCH_SESSIONS.put(`search:${chatId}`, JSON.stringify({
      step: 2,
      tags: tags,
      created_at: session.created_at
    }), { expirationTtl: 600 });

    return "✅ <b>Tags selected:</b> " + tags.join(", ") +
      "\n\n📅 Now enter the date range:\nFormat: <code>YYYY/MM-YYYY/MM</code> or <code>YYYY/MM-now</code>\nExample: <code>2022/01-now</code>";
  }

  if (session.step === 2) {
    // Parse date range
    const dateMatch = text.match(/^(\d{4}\/\d{2})\s*-\s*(\d{4}\/\d{2}|now)$/i);
    if (!dateMatch) {
      return "❌ Invalid format. Use: <code>YYYY/MM-YYYY/MM</code> or <code>YYYY/MM-now</code>";
    }

    const dateFrom = dateMatch[1].replace("/", "-");
    const dateTo = dateMatch[2] === "now" ? "now" : dateMatch[2].replace("/", "-");

    // Clean up session
    await env.SEARCH_SESSIONS.delete(`search:${chatId}`);

    // Trigger search
    await triggerSearchAction(config, session.tags, dateFrom, dateTo);

    return "🔍 <b>Search triggered!</b>\n\n" +
      "🏷️ Tags: " + session.tags.join(", ") + "\n" +
      "📅 Range: " + dateMatch[1] + " to " + dateMatch[2] + "\n\n" +
      "Results will arrive in ~3 minutes.";
  }

  return null;
}

// ─── SEARCH ACTION TRIGGER ───
async function triggerSearchAction(config, tags, dateFrom, dateTo) {
  const url = "https://api.github.com/repos/" + config.GITHUB_REPO + "/dispatches";
  const searchJson = JSON.stringify({ tags, date_from: dateFrom, date_to: dateTo });

  await fetch(url, {
    method: "POST",
    headers: {
      Authorization: "token " + config.GITHUB_TOKEN,
      Accept: "application/vnd.github.v3+json",
      "Content-Type": "application/json",
      "User-Agent": "AeroSentinel-Bot",
    },
    body: JSON.stringify({
      event_type: "telegram_search",
      client_payload: { search_json: searchJson },
    }),
  });
}

// ─── BIBTEX EXPORT ───
async function getBibtexExport(config) {
  try {
    // Try drafts first, then posts
    for (const dir of ["content/drafts", "content/posts"]) {
      const url = `https://api.github.com/repos/${config.GITHUB_REPO}/contents/${dir}`;
      const resp = await fetch(url, {
        headers: {
          Authorization: "token " + config.GITHUB_TOKEN,
          Accept: "application/vnd.github.v3+json",
          "User-Agent": "AeroSentinel-Bot",
        },
      });
      if (resp.status !== 200) continue;

      const files = await resp.json();
      const metaFiles = files.filter(f => f.name.endsWith(".meta.json")).sort((a, b) => b.name.localeCompare(a.name));

      if (metaFiles.length === 0) continue;

      // Fetch the latest meta.json
      const metaResp = await fetch(metaFiles[0].download_url, {
        headers: { "User-Agent": "AeroSentinel-Bot" },
      });
      const meta = await metaResp.json();

      // Build BibTeX from EN gemini output (supports old and new schema)
      const gemini = meta.gemini_output_en || {};
      let bibtex = "";
      const currentYear = new Date().getFullYear().toString();

      // New v2.5 single-paper schema: fields at top level
      if (gemini.paper_title && !gemini.core_papers) {
        const p = gemini;
        const key = p.paper_title.split(" ").slice(0, 3).join("").replace(/[^a-zA-Z]/g, "") + currentYear;
        bibtex = `@article{${key},\n`;
        bibtex += `  title = {${p.paper_title}},\n`;
        bibtex += `  author = {${p.authors || "Unknown"}},\n`;
        bibtex += `  year = {${currentYear}}\n`;
        bibtex += `}\n`;
      } else {
        // Old v2.4 batch schema: arrays of papers
        const papers = [
          ...(gemini.core_papers || []),
          ...(gemini.peripheral_papers || []),
          ...(gemini.papers || []),
        ];
        if (papers.length === 0) continue;

        for (let i = 0; i < papers.length; i++) {
          const p = papers[i];
          const key = p.title.split(" ").slice(0, 3).join("").replace(/[^a-zA-Z]/g, "") + currentYear;
          bibtex += `@article{${key},\n`;
          bibtex += `  title = {${p.title}},\n`;
          bibtex += `  author = {${p.authors || "Unknown"}},\n`;
          bibtex += `  year = {${currentYear}}\n`;
          bibtex += `}\n\n`;
        }
      }

      return "📚 <b>BibTeX Export</b>\n\n<pre>" + bibtex.trim() + "</pre>";
    }
    return "📚 No recent digests found for BibTeX export.";
  } catch (e) {
    return "⚠️ BibTeX export failed: " + e.message;
  }
}

// ─── TELEGRAM HELPERS (outbound fetch, used for multi-step callbacks) ───
async function sendMessage(config, chatId, text) {
  const resp = await fetch("https://api.telegram.org/bot" + config.TELEGRAM_TOKEN + "/sendMessage", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text: text, parse_mode: "HTML" }),
  });
  const result = await resp.json();
  if (!result.ok) {
    console.error("sendMessage failed:", JSON.stringify(result));
  }
  return result;
}

async function sendMessageWithKeyboard(config, chatId, text, keyboard) {
  const resp = await fetch("https://api.telegram.org/bot" + config.TELEGRAM_TOKEN + "/sendMessage", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text: text, parse_mode: "HTML", reply_markup: keyboard }),
  });
  const result = await resp.json();
  if (!result.ok) {
    console.error("sendMessageWithKeyboard failed:", JSON.stringify(result));
  }
  return result;
}

async function editMessage(config, chatId, messageId, text) {
  const resp = await fetch("https://api.telegram.org/bot" + config.TELEGRAM_TOKEN + "/editMessageText", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, message_id: messageId, text: text, parse_mode: "HTML" }),
  });
  const result = await resp.json();
  if (!result.ok) {
    console.error("editMessage failed:", JSON.stringify(result));
  }
  return result;
}
