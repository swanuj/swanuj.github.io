/**
 * PixieNews WhatsApp Bridge
 *
 * This bridge connects WhatsApp Web to the Python bot via WebSocket.
 * Uses whatsapp-web.js for WhatsApp Web automation.
 */

const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const WebSocket = require("ws");

// Configuration
const WS_PORT = process.env.WS_PORT || 3001;
const SESSION_PATH = process.env.SESSION_PATH || "./.wwebjs_auth";

// WebSocket server for Python bot connection
const wss = new WebSocket.Server({ port: WS_PORT });
let botConnection = null;

console.log(`🔌 WebSocket server started on port ${WS_PORT}`);

// WhatsApp client with persistent session
const whatsapp = new Client({
  authStrategy: new LocalAuth({
    dataPath: SESSION_PATH,
  }),
  puppeteer: {
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-accelerated-2d-canvas",
      "--no-first-run",
      "--no-zygote",
      "--disable-gpu",
    ],
  },
});

// Send message to connected bot
function sendToBot(type, data) {
  if (botConnection && botConnection.readyState === WebSocket.OPEN) {
    botConnection.send(JSON.stringify({ type, data }));
  }
}

// WebSocket connection handling
wss.on("connection", (ws) => {
  console.log("🤖 Bot connected to bridge");
  botConnection = ws;

  // Send ready status if WhatsApp is already connected
  if (whatsapp.info) {
    sendToBot("ready", { phone: whatsapp.info.wid.user });
  }

  ws.on("message", async (message) => {
    try {
      const { type, data } = JSON.parse(message);

      switch (type) {
        case "send_message":
          await handleSendMessage(data);
          break;

        case "send_image":
          await handleSendImage(data);
          break;

        case "send_buttons":
          await handleSendButtons(data);
          break;

        case "get_chats":
          await handleGetChats();
          break;

        default:
          console.log(`Unknown message type: ${type}`);
      }
    } catch (error) {
      console.error("Error processing message:", error);
    }
  });

  ws.on("close", () => {
    console.log("🤖 Bot disconnected from bridge");
    botConnection = null;
  });

  ws.on("error", (error) => {
    console.error("WebSocket error:", error);
  });
});

// Message handlers
async function handleSendMessage(data) {
  const { chatId, content } = data;
  try {
    await whatsapp.sendMessage(chatId, content);
    console.log(`📤 Sent message to ${chatId}`);
  } catch (error) {
    console.error(`Failed to send message to ${chatId}:`, error);
  }
}

async function handleSendImage(data) {
  const { chatId, imageUrl, caption } = data;
  try {
    const { MessageMedia } = require("whatsapp-web.js");
    const media = await MessageMedia.fromUrl(imageUrl);
    await whatsapp.sendMessage(chatId, media, { caption });
    console.log(`📤 Sent image to ${chatId}`);
  } catch (error) {
    console.error(`Failed to send image to ${chatId}:`, error);
  }
}

async function handleSendButtons(data) {
  const { chatId, content, buttons } = data;
  try {
    // Note: WhatsApp Web has limited button support
    // Fallback to text with numbered options
    let message = content + "\n\n";
    buttons.forEach((btn, i) => {
      message += `${i + 1}. ${btn.text}\n`;
    });
    await whatsapp.sendMessage(chatId, message);
    console.log(`📤 Sent buttons to ${chatId}`);
  } catch (error) {
    console.error(`Failed to send buttons to ${chatId}:`, error);
  }
}

async function handleGetChats() {
  try {
    const chats = await whatsapp.getChats();
    const chatList = chats.slice(0, 50).map((chat) => ({
      id: chat.id._serialized,
      name: chat.name,
      isGroup: chat.isGroup,
    }));
    sendToBot("chats", chatList);
  } catch (error) {
    console.error("Failed to get chats:", error);
  }
}

// WhatsApp event handlers
whatsapp.on("qr", (qr) => {
  console.log("\n📱 Scan this QR code with WhatsApp:\n");
  qrcode.generate(qr, { small: true });
  sendToBot("qr", { qr });
});

whatsapp.on("authenticated", () => {
  console.log("✅ WhatsApp authenticated");
});

whatsapp.on("auth_failure", (msg) => {
  console.error("❌ WhatsApp authentication failed:", msg);
  sendToBot("auth_failure", { message: msg });
});

whatsapp.on("ready", () => {
  console.log("✅ WhatsApp client is ready!");
  console.log(`📞 Connected as: ${whatsapp.info.wid.user}`);
  sendToBot("ready", { phone: whatsapp.info.wid.user });
});

whatsapp.on("disconnected", (reason) => {
  console.log("❌ WhatsApp disconnected:", reason);
  sendToBot("disconnected", { reason });
});

whatsapp.on("message", async (message) => {
  // Ignore status updates and media messages without text
  if (message.isStatus || message.from === "status@broadcast") {
    return;
  }

  const chat = await message.getChat();
  const contact = await message.getContact();

  const messageData = {
    chatId: message.from,
    sender: contact.pushname || contact.number || message.from,
    content: message.body,
    timestamp: message.timestamp,
    isGroup: chat.isGroup,
    groupName: chat.isGroup ? chat.name : null,
    messageId: message.id._serialized,
  };

  console.log(`📥 Message from ${messageData.sender}: ${message.body.slice(0, 50)}...`);
  sendToBot("message", messageData);
});

whatsapp.on("message_create", async (message) => {
  // Log outgoing messages
  if (message.fromMe) {
    console.log(`📤 Sent: ${message.body.slice(0, 50)}...`);
  }
});

// Error handling
whatsapp.on("error", (error) => {
  console.error("WhatsApp client error:", error);
});

process.on("uncaughtException", (error) => {
  console.error("Uncaught exception:", error);
});

process.on("unhandledRejection", (error) => {
  console.error("Unhandled rejection:", error);
});

// Graceful shutdown
process.on("SIGINT", async () => {
  console.log("\n🛑 Shutting down...");
  await whatsapp.destroy();
  wss.close();
  process.exit(0);
});

// Initialize WhatsApp client
console.log("🚀 Starting WhatsApp client...");
console.log("📁 Session data will be stored in:", SESSION_PATH);
whatsapp.initialize();
