/**
 * AeroSentinel v2 — Cloudflare Worker Webhook Bridge
 * Replaces Google Apps Script. No 302 redirect issues.
 * Free tier: 100K requests/day.
 *
 * Uses Telegram webhook-reply method: returns the API call in the HTTP
 * response body instead of making a separate outbound fetch to api.telegram.org.
 */

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

        const replyText = await buildCommandReply(config, text);
        if (replyText) {
          return webhookReply("sendMessage", {
            chat_id: chatId,
            text: replyText,
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
async function buildCommandReply(config, text) {
  const command = text.toLowerCase().split(" ")[0];

  switch (command) {
    case "/scout":
      triggerGitHubAction(config, "scout", "manual").catch(e => console.error("Scout trigger error:", e));
      return "🛰️ Scout pipeline triggered! You'll receive a preview when ready.";

    case "/status":
      return await getLatestWorkflowStatus(config);

    case "/help":
      return "🛰️ <b>AeroSentinel v2 Commands</b>\n\n" +
        "/scout — Trigger a paper hunt now\n" +
        "/status — Check latest workflow status\n" +
        "/help — Show this help message\n\n" +
        "Use the inline buttons on draft previews to Publish, Edit, or Discard.";

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
