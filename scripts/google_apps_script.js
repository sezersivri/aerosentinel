/**
 * AeroSentinel — Google Apps Script Webhook Bridge
 * 
 * This script runs FREE on Google's servers 24/7.
 * It listens for Telegram button clicks and triggers GitHub Actions.
 * 
 * SETUP:
 * 1. Go to https://script.google.com → New Project
 * 2. Paste this code
 * 3. Go to Project Settings → Script Properties → Add:
 *    - TELEGRAM_TOKEN: your bot token from @BotFather
 *    - GITHUB_TOKEN: your GitHub PAT (repo scope)
 *    - GITHUB_REPO: "username/aerosentinel"
 *    - AUTHORIZED_CHAT_ID: your Telegram chat ID (number)
 * 4. Deploy → Web App → Execute as: Me → Access: Anyone
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

// ─── MAIN WEBHOOK HANDLER ───
function doPost(e) {
  var config = getConfig();
  var data = JSON.parse(e.postData.contents);
  
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
      var filename = payload.substring(4); // Remove "PUB_" prefix
      
      triggerGitHubAction(config, "publish", filename);
      editMessage(config, chatId, messageId, 
        "✅ Publishing initiated! Site will update in ~2 minutes.");
      
      // Send follow-up with site link after a delay
      Utilities.sleep(3000);
      sendMessage(config, chatId, 
        "🔗 Check: https://" + config.GITHUB_REPO.split("/")[0] + ".github.io/aerosentinel/");
    }
    
    // ── EDIT ──
    else if (payload.startsWith("EDT_")) {
      var filename = payload.substring(4); // Remove "EDT_" prefix
      var editUrl = "https://github.com/" + config.GITHUB_REPO + 
                    "/edit/main/content/drafts/" + filename;
      
      sendMessage(config, chatId, 
        "✏️ Edit the draft directly on GitHub:\n" + editUrl + 
        "\n\nAfter editing, commit the changes. Then come back here and click Publish.");
      
      // Re-send publish button
      var shortName = filename.substring(0, 50);
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
      var filename = payload.substring(4);
      
      triggerGitHubAction(config, "discard", filename);
      editMessage(config, chatId, messageId, "🗑️ Draft discarded.");
    }
    
    // Acknowledge callback to remove loading spinner
    answerCallbackQuery(config, data.callback_query.id);
  }
  
  return ContentService.createTextOutput("OK");
}

// ─── GITHUB ACTIONS TRIGGER ───
function triggerGitHubAction(config, command, filename) {
  var url = "https://api.github.com/repos/" + config.GITHUB_REPO + "/dispatches";
  
  var options = {
    "method": "post",
    "headers": {
      "Authorization": "token " + config.GITHUB_TOKEN,
      "Accept": "application/vnd.github.v3+json",
      "Content-Type": "application/json"
    },
    "payload": JSON.stringify({
      "event_type": "telegram_command",
      "client_payload": {
        "command": command,
        "filename": filename
      }
    }),
    "muteHttpExceptions": true
  };
  
  var response = UrlFetchApp.fetch(url, options);
  Logger.log("GitHub dispatch: " + response.getResponseCode());
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
