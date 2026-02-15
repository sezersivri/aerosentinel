/**
 * ⚠️ DEPRECATED — This Google Apps Script bridge has been replaced by
 * worker/index.js (Cloudflare Worker). It only supports /scout, /status,
 * /help and lacks v2.3 features (search, bibtex, bookmarks, two-tier posts).
 * Kept for reference only. See worker/index.js for the active implementation.
 *
 * AeroSentinel v2 — Google Apps Script Webhook Bridge (LEGACY)
 *
 * This script runs FREE on Google's servers 24/7.
 * It listens for Telegram button clicks AND text commands,
 * then triggers GitHub Actions accordingly.
 *
 * SETUP:
 * 1. Go to https://script.google.com -> New Project
 * 2. Paste this code
 * 3. Go to Project Settings -> Script Properties -> Add:
 *    - TELEGRAM_TOKEN: your bot token from @BotFather
 *    - GITHUB_TOKEN: your GitHub PAT (repo scope)
 *    - GITHUB_REPO: "username/aerosentinel"
 *    - AUTHORIZED_CHAT_ID: your Telegram chat ID (number)
 * 4. Deploy -> Web App -> Execute as: Me -> Access: Anyone
 * 5. Copy the Web App URL
 * 6. Set Telegram webhook:
 *    https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WEB_APP_URL>
 */

// ─── SECURE TOKEN ACCESS ───
function getConfig() {
  var props = PropertiesService.getScriptProperties();
  return {
    TELEGRAM_TOKEN: props.getProperty('TELEGRAM_TOKEN'),
    GITHUB_TOKEN: props.getProperty('GITHUB_TOKEN'),
    GITHUB_REPO: props.getProperty('GITHUB_REPO'),
    AUTHORIZED_CHAT_ID: parseInt(props.getProperty('AUTHORIZED_CHAT_ID'))
  };
}

// ─── FILENAME SANITIZATION (security fix) ───
function sanitizeFilename(filename) {
  // Remove any characters that aren't alphanumeric, hyphens, dots, or underscores
  return filename.replace(/[^a-zA-Z0-9\-_.]/g, '');
}

// ─── MAIN WEBHOOK HANDLER ───
function doPost(e) {
  var config = getConfig();
  var data = JSON.parse(e.postData.contents);

  // Handle text messages (commands)
  if (data.message && data.message.text) {
    var chatId = data.message.chat.id;
    var text = data.message.text.trim();

    // Security: Only respond to authorized user
    if (chatId !== config.AUTHORIZED_CHAT_ID) {
      Logger.log("Unauthorized text message from chat ID: " + chatId);
      return ContentService.createTextOutput("UNAUTHORIZED");
    }

    handleTextCommand(config, chatId, text);
    return ContentService.createTextOutput("OK");
  }

  // Handle callback queries (button clicks)
  if (data.callback_query) {
    var payload = data.callback_query.data;
    var chatId = data.callback_query.message.chat.id;
    var messageId = data.callback_query.message.message_id;

    // ── SECURITY: Only respond to authorized user ──
    if (chatId !== config.AUTHORIZED_CHAT_ID) {
      Logger.log("Unauthorized access attempt from chat ID: " + chatId);
      return ContentService.createTextOutput("UNAUTHORIZED");
    }

    // ── PUBLISH ──
    if (payload.startsWith("PUB_")) {
      var filenameBase = sanitizeFilename(payload.substring(4));

      triggerGitHubAction(config, "publish", filenameBase);
      editMessage(config, chatId, messageId,
        "✅ Publishing both EN + TR versions! Site will update in ~2 minutes.");

      // Send follow-up with site link after a delay
      Utilities.sleep(3000);
      sendMessage(config, chatId,
        "🔗 EN: https://" + config.GITHUB_REPO.split("/")[0] + ".github.io/aerosentinel/\n" +
        "🔗 TR: https://" + config.GITHUB_REPO.split("/")[0] + ".github.io/aerosentinel/tr/");
    }

    // ── EDIT ──
    else if (payload.startsWith("EDT_")) {
      var filenameBase = sanitizeFilename(payload.substring(4));
      var editUrl = "https://github.com/" + config.GITHUB_REPO +
                    "/tree/main/content/drafts/";

      sendMessage(config, chatId,
        "✏️ Edit the drafts on GitHub:\n" + editUrl +
        "\n\nBoth EN and TR versions are available. After editing, commit the changes and click Publish.");

      // Re-send publish button
      var shortName = filenameBase.substring(0, 50);
      var keyboard = {
        "inline_keyboard": [
          [
            {"text": "✅ Publish (after edit)", "callback_data": "PUB_" + shortName},
            {"text": "🗑️ Discard", "callback_data": "DEL_" + shortName}
          ]
        ]
      };
      sendMessageWithKeyboard(config, chatId, "Ready to publish the edited version?", keyboard);
    }

    // ── DISCARD ──
    else if (payload.startsWith("DEL_")) {
      var filenameBase = sanitizeFilename(payload.substring(4));

      triggerGitHubAction(config, "discard", filenameBase);
      editMessage(config, chatId, messageId, "🗑️ Both EN + TR drafts discarded.");
    }

    // Acknowledge callback to remove loading spinner
    answerCallbackQuery(config, data.callback_query.id);
  }

  return ContentService.createTextOutput("OK");
}

// ─── TEXT COMMAND HANDLER ───
function handleTextCommand(config, chatId, text) {
  var command = text.toLowerCase().split(' ')[0];

  switch (command) {
    case '/scout':
      sendMessage(config, chatId, "🛰️ Triggering AeroSentinel scout pipeline...");
      triggerGitHubAction(config, "scout", "manual");
      Utilities.sleep(2000);
      sendMessage(config, chatId, "✅ Scout workflow triggered! Papers will be hunted and analyzed. You'll receive a preview when ready.");
      break;

    case '/status':
      var statusText = getLatestWorkflowStatus(config);
      sendMessage(config, chatId, statusText);
      break;

    case '/help':
      sendMessage(config, chatId,
        "🛰️ <b>AeroSentinel v2 Commands</b>\n\n" +
        "/scout — Trigger a paper hunt now\n" +
        "/status — Check latest workflow status\n" +
        "/help — Show this help message\n\n" +
        "You can also use the inline buttons on draft previews to Publish, Edit, or Discard.");
      break;

    default:
      // Ignore unrecognized commands
      break;
  }
}

// ─── GITHUB WORKFLOW STATUS ───
function getLatestWorkflowStatus(config) {
  var url = "https://api.github.com/repos/" + config.GITHUB_REPO + "/actions/runs?per_page=3";

  var options = {
    "method": "get",
    "headers": {
      "Authorization": "token " + config.GITHUB_TOKEN,
      "Accept": "application/vnd.github.v3+json"
    },
    "muteHttpExceptions": true
  };

  try {
    var response = UrlFetchApp.fetch(url, options);
    var data = JSON.parse(response.getContentText());
    var runs = data.workflow_runs || [];

    if (runs.length === 0) {
      return "📊 No recent workflow runs found.";
    }

    var statusText = "📊 <b>Latest Workflow Runs</b>\n\n";
    for (var i = 0; i < Math.min(runs.length, 3); i++) {
      var run = runs[i];
      var icon = run.conclusion === "success" ? "✅" :
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
function triggerGitHubAction(config, command, filename) {
  var url = "https://api.github.com/repos/" + config.GITHUB_REPO + "/dispatches";

  var eventType = (command === "scout") ? "telegram_scout" : "telegram_command";

  var options = {
    "method": "post",
    "headers": {
      "Authorization": "token " + config.GITHUB_TOKEN,
      "Accept": "application/vnd.github.v3+json",
      "Content-Type": "application/json"
    },
    "payload": JSON.stringify({
      "event_type": eventType,
      "client_payload": {
        "command": command,
        "filename": filename
      }
    }),
    "muteHttpExceptions": true
  };

  var response = UrlFetchApp.fetch(url, options);
  Logger.log("GitHub dispatch (" + eventType + "): " + response.getResponseCode());
}

// ─── TELEGRAM HELPERS ───
function sendMessage(config, chatId, text) {
  var url = "https://api.telegram.org/bot" + config.TELEGRAM_TOKEN + "/sendMessage";
  UrlFetchApp.fetch(url, {
    "method": "post",
    "payload": {
      "chat_id": String(chatId),
      "text": text,
      "parse_mode": "HTML"
    },
    "muteHttpExceptions": true
  });
}

function sendMessageWithKeyboard(config, chatId, text, keyboard) {
  var url = "https://api.telegram.org/bot" + config.TELEGRAM_TOKEN + "/sendMessage";
  UrlFetchApp.fetch(url, {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify({
      "chat_id": chatId,
      "text": text,
      "parse_mode": "HTML",
      "reply_markup": keyboard
    }),
    "muteHttpExceptions": true
  });
}

function editMessage(config, chatId, messageId, text) {
  var url = "https://api.telegram.org/bot" + config.TELEGRAM_TOKEN + "/editMessageText";
  UrlFetchApp.fetch(url, {
    "method": "post",
    "payload": {
      "chat_id": String(chatId),
      "message_id": String(messageId),
      "text": text,
      "parse_mode": "HTML"
    },
    "muteHttpExceptions": true
  });
}

function answerCallbackQuery(config, callbackQueryId) {
  var url = "https://api.telegram.org/bot" + config.TELEGRAM_TOKEN + "/answerCallbackQuery";
  UrlFetchApp.fetch(url, {
    "method": "post",
    "payload": {
      "callback_query_id": callbackQueryId
    },
    "muteHttpExceptions": true
  });
}

// ─── SETUP HELPER ───
// Run this once manually to set the Telegram webhook
function setWebhook() {
  var config = getConfig();
  var webAppUrl = ScriptApp.getService().getUrl();
  var url = "https://api.telegram.org/bot" + config.TELEGRAM_TOKEN +
            "/setWebhook?url=" + webAppUrl;
  var response = UrlFetchApp.fetch(url);
  Logger.log("Webhook set: " + response.getContentText());
}
