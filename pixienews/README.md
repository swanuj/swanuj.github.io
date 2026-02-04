# PixieNews 🤖📰

**AI News Bot** - A lightweight bot that scrapes AI/ML news from around the world and delivers it via WhatsApp.

Users can select their preferred country and receive curated AI news directly in their WhatsApp chat.

## Features

- 🌍 **10+ Countries** - US, UK, India, China, Germany, Japan, France, Korea, Canada, Australia + Global
- 📰 **Multiple Sources** - Aggregates from TechCrunch, VentureBeat, BBC, Analytics India, and more
- 🔍 **Smart Search** - Search AI news across all sources
- 💬 **WhatsApp Integration** - Get news delivered to your WhatsApp
- ⚡ **Lightweight** - Minimal dependencies, fast execution
- 🔄 **Real-time** - Fresh news with intelligent caching
- 📱 **User Preferences** - Set your default country

---

## Quick Start

### 1. Install PixieNews

```bash
# Clone the repository
git clone https://github.com/your-repo/pixienews.git
cd pixienews

# Install Python package
pip install -e .
```

### 2. Set Up WhatsApp Bridge

```bash
# Navigate to bridge directory
cd bridge

# Install Node.js dependencies (requires Node.js >= 18)
npm install

# Start the bridge
node server.js
```

### 3. Connect WhatsApp

1. A QR code will appear in the terminal
2. Open WhatsApp on your phone
3. Go to **Settings → Linked Devices → Link a Device**
4. Scan the QR code

### 4. Start the Bot

```bash
# In a new terminal
pixienews run
```

That's it! Send `/start` to your WhatsApp to begin.

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

## Detailed WhatsApp Integration Guide

### Architecture

```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│   PixieNews     │◄──────────────────►│  WhatsApp Bridge │
│   (Python)      │    ws://3001       │    (Node.js)     │
└─────────────────┘                    └────────┬─────────┘
                                                │
                                                │ WhatsApp Web
                                                │ Protocol
                                                ▼
                                       ┌──────────────────┐
                                       │   WhatsApp       │
                                       │   Servers        │
                                       └──────────────────┘
```

### Step-by-Step Setup

#### Prerequisites

- **Python 3.11+** - For the main bot
- **Node.js 18+** - For the WhatsApp bridge
- **A WhatsApp account** - To link as a device

#### Step 1: Install Dependencies

```bash
# Python dependencies
pip install pixienews[full]

# Or install from source
pip install httpx beautifulsoup4 feedparser websocket-client pydantic loguru apscheduler rich typer
```

#### Step 2: Configure the Bridge

The bridge uses `whatsapp-web.js` which automates WhatsApp Web.

```bash
cd pixienews/bridge
npm install
```

**Important Files:**
- `bridge/server.js` - The WebSocket server
- `bridge/.wwebjs_auth/` - Session data (created after first login)

#### Step 3: First-Time Authentication

```bash
# Start the bridge
node server.js
```

You'll see:
```
🚀 Starting WhatsApp client...
📁 Session data will be stored in: ./.wwebjs_auth
🔌 WebSocket server started on port 3001

📱 Scan this QR code with WhatsApp:

▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
█ ▄▄▄▄▄ █▄▀▄█...
...
```

1. Open WhatsApp on your phone
2. Go to **Settings** (⚙️)
3. Tap **Linked Devices**
4. Tap **Link a Device**
5. Scan the QR code

After scanning:
```
✅ WhatsApp authenticated
✅ WhatsApp client is ready!
📞 Connected as: 1234567890
```

#### Step 4: Run the Bot

In a new terminal:

```bash
pixienews run
```

Output:
```
🤖 Starting PixieNews Bot...
📁 Data directory: /home/user/.pixienews
🔌 Bridge URL: ws://localhost:3001
Connected to WhatsApp bridge
Waiting for messages...
```

#### Step 5: Test It!

Send a message to your WhatsApp number:
- `/start` - See welcome message
- `US` - Get US AI news
- `/search ChatGPT` - Search for ChatGPT news

---

## CLI Usage (Without WhatsApp)

You can also use PixieNews from the command line:

```bash
# Get news for a country
pixienews news US
pixienews news IN --limit 10

# Search news
pixienews search "OpenAI GPT"

# List countries
pixienews countries

# Setup guide
pixienews setup
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

## Configuration

Config file: `~/.pixienews/config.json`

```json
{
  "whatsapp_bridge_url": "ws://localhost:3001",
  "scrape_interval_minutes": 30,
  "max_news_per_source": 10,
  "cache_ttl_minutes": 15,
  "data_dir": "/home/user/.pixienews"
}
```

### Environment Variables

```bash
export PIXIENEWS_BRIDGE_URL="ws://localhost:3001"
export PIXIENEWS_DATA_DIR="/path/to/data"
```

---

## Deployment

### Running as a Service (systemd)

Create `/etc/systemd/system/pixienews-bridge.service`:

```ini
[Unit]
Description=PixieNews WhatsApp Bridge
After=network.target

[Service]
Type=simple
User=pixienews
WorkingDirectory=/opt/pixienews/bridge
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/pixienews.service`:

```ini
[Unit]
Description=PixieNews Bot
After=network.target pixienews-bridge.service
Requires=pixienews-bridge.service

[Service]
Type=simple
User=pixienews
ExecStart=/usr/local/bin/pixienews run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable pixienews-bridge pixienews
sudo systemctl start pixienews-bridge pixienews
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

CMD ["pixienews", "run", "--bridge", "ws://bridge:3001"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  bridge:
    build: ./bridge
    ports:
      - "3001:3001"
    volumes:
      - ./bridge/.wwebjs_auth:/app/.wwebjs_auth

  bot:
    build: .
    depends_on:
      - bridge
    volumes:
      - pixienews-data:/root/.pixienews

volumes:
  pixienews-data:
```

---

## Troubleshooting

### QR Code Not Appearing
- Make sure Node.js >= 18 is installed
- Delete `.wwebjs_auth/` and restart the bridge

### Bot Not Responding
- Check if the bridge is running: `node server.js`
- Ensure WebSocket connection on port 3001
- Check logs: `pixienews run --debug`

### WhatsApp Disconnects Frequently
- WhatsApp Web sessions expire after inactivity
- Keep the bridge running continuously
- Use systemd or PM2 for process management

### No News Found
- Some RSS feeds may be down temporarily
- Try `/global` for international sources
- Check internet connectivity

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint code
ruff check pixienews
```

---

## License

MIT License - Feel free to use and modify!

---

## Credits

Built with:
- [whatsapp-web.js](https://github.com/pedroslopez/whatsapp-web.js) - WhatsApp Web API
- [feedparser](https://feedparser.readthedocs.io/) - RSS parsing
- [httpx](https://www.python-httpx.org/) - Async HTTP
- [Typer](https://typer.tiangolo.com/) - CLI framework
