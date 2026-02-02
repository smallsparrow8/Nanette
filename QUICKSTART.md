# Nanette Quick Start Guide

Get Nanette up and running in minutes!

## Prerequisites

- Python 3.11+ installed
- Node.js 20+ installed
- A Claude API key from Anthropic
- A Discord bot token (or Telegram bot token)

## Step 1: Get API Keys

### Claude API (Required)
1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Create an API key
4. Copy the key

### Discord Bot (Recommended for Quick Start)
1. Visit https://discord.com/developers/applications
2. Click "New Application"
3. Give it a name (e.g., "Nanette")
4. Go to "Bot" section → Click "Add Bot"
5. Copy the token
6. Under OAuth2 → URL Generator:
   - Select `bot` and `applications.commands`
   - Select permissions: Send Messages, Embed Links, Use Slash Commands
   - Copy the URL and invite the bot to your test server

### Blockchain RPC (Optional - Free Tier)
For better reliability, get a free Alchemy key:
1. Visit https://www.alchemy.com/
2. Sign up and create a new app
3. Select Ethereum (or other chains)
4. Copy the API key

## Step 2: Configure Environment

```bash
cd nanette
cp .env
```

Edit `.env` and add your keys:
```env
# Required
ANTHROPIC_API_KEY=your_claude_api_key_here
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here

# Optional but recommended
ALCHEMY_API_KEY=your_alchemy_key_here
ETHERSCAN_API_KEY=your_etherscan_key_here
```

## Step 3: Install Dependencies

### Python Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Discord Bot Dependencies
```bash
cd bots/discord-bot
npm install
cd ../..
```

## Step 4: Initialize Database

```bash
python -c "from shared.database import Database; db = Database(); db.create_tables(); print('Database initialized!')"
```

## Step 5: Start Services

### Option A: Start Everything Separately (Recommended for First Run)

**Terminal 1 - Start API:**
```bash
# Make sure venv is activated
cd nanette
python api/main.py
```

You should see:
```
Starting Nanette API...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Start Discord Bot:**
```bash
cd nanette/bots/discord-bot
npm run dev
```

You should see:
```
Nanette is online! Logged in as YourBot#1234
```

### Option B: Using Docker (After Testing)

```bash
cd nanette
docker-compose up --build
```

## Step 6: Test Nanette!

1. Go to your Discord server where you invited Nanette
2. Type: `/analyze address:0x6B175474E89094C44Da98b954EedeAC495271d0F`
   (This is DAI stablecoin contract - safe to test with)
3. Wait for Nanette's analysis!

## Troubleshooting

### "Module not found" errors in Python
```bash
# Make sure you're in the nanette directory and venv is activated
cd nanette
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Re-install
pip install -r requirements.txt
```

### Discord bot not responding
1. Check the bot is online in your server (green dot)
2. Make sure you ran the bot from `bots/discord-bot/` directory
3. Check the bot has permissions in your server
4. Verify DISCORD_BOT_TOKEN is correct in .env

### API connection errors
1. Make sure the API is running on port 8000
2. Check for any error messages in the API terminal
3. Verify ANTHROPIC_API_KEY is set correctly

### "Contract not verified" warnings
This is normal - many contracts aren't verified on block explorers. Nanette will still analyze what she can from the bytecode.

## Next Steps

Once everything is working:

1. **Get Explorer API Keys** (Free):
   - Etherscan: https://etherscan.io/apis
   - BscScan: https://bscscan.com/apis
   - Add to `.env` for verified contract analysis

2. **Try Different Blockchains**:
   ```
   /analyze address:0x... blockchain:bsc
   /analyze address:0x... blockchain:polygon
   ```

3. **Customize Nanette**:
   - Edit personality in `core/nanette/personality.py`
   - Adjust scoring in `analyzers/contract_analyzer/safety_scorer.py`

4. **Add Telegram Bot** (Optional):
   - Get bot token from @BotFather
   - Configure in `.env`
   - Run: `cd bots/telegram-bot && npm run dev`

## Need Help?

- Check the full README.md for detailed documentation
- Review error logs in the terminal
- Make sure all API keys are valid
- Verify Python 3.11+ and Node 20+ are installed

---

**Congratulations! Nanette is now protecting your crypto community!** 🐕

Remember: Nanette provides analysis and education, not financial advice. Always DYOR!
