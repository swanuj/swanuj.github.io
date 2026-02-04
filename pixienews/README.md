# PixieNews 🤖📰

**AI News Bot** - A lightweight bot that scrapes AI/ML news from around the world and delivers it via **Telegram** or **WhatsApp**.

Users can select their preferred country and receive curated AI news directly in their chat.

## Features

- 🌍 **10+ Countries** - US, UK, India, China, Germany, Japan, France, Korea, Canada, Australia + Global
- 📰 **Multiple Sources** - Aggregates from TechCrunch, VentureBeat, BBC, Analytics India, and more
- 🔍 **Smart Search** - Search AI news across all sources
- 📱 **Telegram Bot** - Easy setup in 2 minutes!
- 💬 **WhatsApp Integration** - Official Business API support
- ⚡ **Lightweight** - Minimal dependencies, fast execution
- 🔄 **Real-time** - Fresh news with intelligent caching

---

## 🎯 Choose Your Platform

| Platform | Setup Time | Difficulty | Cost |
|----------|-----------|------------|------|
| **Telegram** | 2 minutes | ⭐ Easy | Free |
| **WhatsApp Business** | 1-2 days | ⭐⭐⭐ Complex | Pay per message |
| **WhatsApp Web Bridge** | 10 minutes | ⭐⭐ Medium | Free (unofficial) |

---

# 📱 Telegram Bot (EASIEST - Recommended!)

Setup a fully working bot in **2 minutes**. Free forever!

## Quick Start

```bash
# 1. Install PixieNews with Telegram support
pip install pixienews[telegram]

# 2. Get your bot token from @BotFather on Telegram
#    - Open Telegram, search @BotFather
#    - Send /newbot
#    - Follow instructions, copy the token

# 3. Run your bot!
pixienews telegram --token YOUR_BOT_TOKEN
```

That's it! Open Telegram and send `/start` to your bot.

## Step-by-Step Guide

### Step 1: Create Bot with @BotFather
1. Open Telegram
2. Search for `@BotFather`
3. Send `/newbot`
4. Choose a name: `My AI News Bot`
5. Choose a username: `myainews_bot`
6. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Run PixieNews
```bash
# Install
pip install pixienews[telegram]

# Run with token
pixienews telegram --token "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

# Or use environment variable
export TELEGRAM_BOT_TOKEN="your_token"
pixienews telegram
```

### Step 3: Test Your Bot
1. Open Telegram
2. Search for your bot username
3. Send `/start`
4. Try: `US`, `/news`, `/search OpenAI`

---

# 💬 WhatsApp Business API

Official WhatsApp bot with its own phone number. Requires Meta Business account.

This creates a **real WhatsApp bot** that users can add and message.

## Step 1: Create Meta Business Account

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click **My Apps** → **Create App**
3. Select **Business** → **Next**
4. Fill in app name: `PixieNews Bot`
5. Create the app

## Step 2: Set Up WhatsApp Business

1. In your app dashboard, click **Add Product**
2. Find **WhatsApp** → Click **Set Up**
3. You'll get a **Test Phone Number** (free for testing)

## Step 3: Get Your Credentials

From the WhatsApp dashboard, note down:
- **Phone Number ID**: `1234567890123456`
- **Access Token**: `EAAxxxxxxx...`
- **Verify Token**: Create your own (e.g., `pixienews_secret_123`)

## Step 4: Install & Configure PixieNews

```bash
# Clone and install
git clone https://github.com/your-repo/pixienews.git
cd pixienews
pip install -e ".[full]"

# Set environment variables
export WHATSAPP_PHONE_NUMBER_ID="your_phone_number_id"
export WHATSAPP_ACCESS_TOKEN="your_access_token"
export WHATSAPP_VERIFY_TOKEN="pixienews_secret_123"
```

## Step 5: Start the Webhook Server

```bash
# Start the server (default port 8000)
pixienews webhook

# Or with custom port
pixienews webhook --port 8080
```

## Step 6: Expose Your Server (for Meta to reach you)

Use **ngrok** (easiest for testing):

```bash
# Install ngrok
brew install ngrok  # or download from ngrok.com

# Expose your server
ngrok http 8000
```

You'll get a URL like: `https://abc123.ngrok.io`

## Step 7: Configure Webhook in Meta Dashboard

1. Go to **WhatsApp** → **Configuration**
2. Click **Edit** under Webhooks
3. Enter:
   - **Callback URL**: `https://abc123.ngrok.io/webhook`
   - **Verify Token**: `pixienews_secret_123`
4. Click **Verify and Save**
5. Under **Webhook Fields**, subscribe to:
   - `messages`

## Step 8: Test Your Bot!

1. In Meta Dashboard, go to **WhatsApp** → **API Setup**
2. Add your phone number as a recipient
3. Send a message to the test number
4. Or use the **Send Message** button to send yourself a template first

### How Users Interact:

```
User sends: /start
Bot replies: 🤖 Welcome to PixieNews! ...

User sends: US
Bot replies: 🇺🇸 AI News from United States
             1. OpenAI announces GPT-5...
             2. Google DeepMind...

User sends: /search ChatGPT
Bot replies: 🔍 Search Results for: ChatGPT
             1. ChatGPT hits 200M users...
```

---

# 🔧 Method 2: WhatsApp Web Bridge (Personal Use)

This links YOUR WhatsApp account (like WhatsApp Web). The bot responds AS YOU.

⚠️ **Note**: This is NOT a separate bot. It's YOUR account automated.

## Setup

### 1. Install PixieNews

```bash
git clone https://github.com/your-repo/pixienews.git
cd pixienews
pip install -e .
```

### 2. Set Up WhatsApp Bridge

```bash
cd bridge
npm install
node server.js
```

### 3. Scan QR Code

1. A QR code appears in terminal
2. Open WhatsApp → **Settings** → **Linked Devices**
3. Tap **Link a Device**
4. Scan the QR code

### 4. Start the Bot

```bash
# In a new terminal
pixienews run
```

### 5. Test

Send a message FROM ANOTHER PHONE to your WhatsApp number.

---

## WhatsApp Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and quick start guide |
| `/help` | Show all available commands |
| `/countries` | List all available countries |
| `/set US` | Set your default country (US, UK, IN, etc.) |
| `/news` | Get latest AI news for your country |
| `/news UK` | Get news for a specific country |
| `/global` | Get global/international AI news |
| `/search GPT-5` | Search news by keyword |
| `/subscribe` | Subscribe to daily updates |
| `/unsubscribe` | Unsubscribe from updates |

**Quick Access:** Just type a country code (US, UK, IN, DE, etc.) to get news!

---

## Architecture

### Method 1: WhatsApp Business API
```
┌─────────────┐    HTTPS     ┌─────────────┐     API      ┌──────────────┐
│   Users     │◄────────────►│   Meta      │◄────────────►│  PixieNews   │
│  WhatsApp   │              │  Servers    │   Webhook    │   Server     │
└─────────────┘              └─────────────┘              └──────────────┘
                                                                │
                                                                ▼
                                                         ┌──────────────┐
                                                         │ News Scraper │
                                                         └──────────────┘
```

### Method 2: WhatsApp Web Bridge
```
┌─────────────┐    WA Web    ┌─────────────┐  WebSocket   ┌──────────────┐
│   Your      │◄────────────►│  WhatsApp   │◄────────────►│  PixieNews   │
│   Phone     │              │  Bridge     │              │    Bot       │
└─────────────┘              │  (Node.js)  │              └──────────────┘
                             └─────────────┘
```

---

## Available Countries

| Code | Country | Flag | Sources |
|------|---------|------|---------|
| US | United States | 🇺🇸 | TechCrunch, VentureBeat, MIT Tech Review, The Verge |
| UK | United Kingdom | 🇬🇧 | BBC Tech, The Guardian, Wired UK |
| IN | India | 🇮🇳 | Analytics India, Inc42, YourStory |
| CN | China | 🇨🇳 | Synced AI, Pandaily |
| DE | Germany | 🇩🇪 | Heise AI, Golem |
| JP | Japan | 🇯🇵 | AI Japan, TechCrunch Japan |
| FR | France | 🇫🇷 | L'Usine Digitale, ActuIA |
| KR | South Korea | 🇰🇷 | Korea AI Times, ZDNet Korea |
| CA | Canada | 🇨🇦 | BetaKit, IT World Canada |
| AU | Australia | 🇦🇺 | iTnews, ZDNet AU |
| GLOBAL | International | 🌍 | Google AI, OpenAI, Anthropic, Hugging Face, arXiv |

---

## CLI Usage (Without WhatsApp)

```bash
# Get news for a country
pixienews news US
pixienews news IN --limit 10

# Search news
pixienews search "OpenAI GPT"

# List countries
pixienews countries

# Run webhook server (Business API)
pixienews webhook --port 8000

# Run bridge bot (Web method)
pixienews run
```

---

## Deployment (Production)

### For WhatsApp Business API:

```bash
# Using Docker
docker build -t pixienews .
docker run -d \
  -e WHATSAPP_PHONE_NUMBER_ID=xxx \
  -e WHATSAPP_ACCESS_TOKEN=xxx \
  -e WHATSAPP_VERIFY_TOKEN=xxx \
  -p 8000:8000 \
  pixienews webhook

# Using systemd
sudo cp pixienews.service /etc/systemd/system/
sudo systemctl enable pixienews
sudo systemctl start pixienews
```

### Reverse Proxy (nginx):

```nginx
server {
    listen 443 ssl;
    server_name pixienews.yourdomain.com;

    ssl_certificate /etc/ssl/certs/your_cert.pem;
    ssl_certificate_key /etc/ssl/private/your_key.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `WHATSAPP_PHONE_NUMBER_ID` | Meta Phone Number ID | Yes (API) |
| `WHATSAPP_ACCESS_TOKEN` | Meta Access Token | Yes (API) |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verify token | Yes (API) |
| `WHATSAPP_WEBHOOK_SECRET` | Signature validation | Optional |
| `PIXIENEWS_DATA_DIR` | Data storage path | Optional |

---

## Troubleshooting

### Webhook Not Verified
- Check your `WHATSAPP_VERIFY_TOKEN` matches Meta dashboard
- Ensure your server is publicly accessible (use ngrok for testing)

### No Messages Received
- Subscribe to `messages` in webhook fields
- Check your server logs: `pixienews webhook --debug`

### QR Code Issues (Web method)
- Delete `bridge/.wwebjs_auth/` and restart
- Ensure Node.js >= 18

### Rate Limited
- WhatsApp has rate limits on messages
- Use template messages for first contact

---

## License

MIT License - Feel free to use and modify!

---

## Credits

Built with:
- [Meta Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api) - Official WhatsApp API
- [whatsapp-web.js](https://github.com/pedroslopez/whatsapp-web.js) - WhatsApp Web automation
- [FastAPI](https://fastapi.tiangolo.com/) - Webhook server
- [feedparser](https://feedparser.readthedocs.io/) - RSS parsing
- [httpx](https://www.python-httpx.org/) - Async HTTP
