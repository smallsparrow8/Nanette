# Telegram Bot Quick Test Guide

Fast guide to get Nanette running on Telegram in 5 minutes! 🐕

## Step 1: Get Your Bot Token (2 minutes)

1. Open Telegram
2. Search for `@BotFather`
3. Send: `/newbot`
4. Name your bot: `Nanette Guardian` (or any name)
5. Username: `nanette_test_bot` (or any name ending in `_bot`)
6. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Add Token to .env (30 seconds)

Open `nanette/.env` and add:
```env
TELEGRAM_BOT_TOKEN=your_token_here
```

## Step 3: Install Dependencies (1 minute)

```bash
cd nanette/bots/telegram-bot
npm install
```

## Step 4: Start the API (30 seconds)

In one terminal:
```bash
cd nanette
python -m api.main
```

Wait for: `Application startup complete`

## Step 5: Start the Bot (30 seconds)

In another terminal:
```bash
cd nanette/bots/telegram-bot
npm run dev
```

Wait for: `✅ Nanette Telegram bot is online!`

## Step 6: Test! (30 seconds)

1. Open Telegram
2. Search for your bot username (e.g., `@nanette_test_bot`)
3. Send: `/start`

You should get a welcome message from Nanette! 🐕

## Quick Tests

### Test Commands
```
/start          → Welcome message
/help           → See all features
/greet          → Friendly greeting
/about          → Learn about Nanette
/rintintin      → Rin Tin Tin story
```

### Test Conversation
```
Hello Nanette!
→ She'll respond with her German Shepherd personality

What's the price of Bitcoin?
→ She'll fetch current BTC price

How much are gas fees?
→ Current Ethereum gas prices

Explain what DeFi is
→ Educational explanation
```

### Test Analysis (Takes ~30 seconds)
```
/analyze 0x6B175474E89094C44Da98b954EedeAC495271d0F

→ Full security analysis of DAI stablecoin
```

## What to Expect

✅ **Working Correctly:**
- Bot responds to commands
- Conversational messages work
- Price queries return data
- Analysis completes successfully

❌ **Common Issues:**

**Bot doesn't respond:**
- Check token is correct in `.env`
- Make sure bot is running (check terminal)

**"Service offline" error:**
- Python API not running
- Start with: `python -m api.main`

**Analysis times out:**
- First analysis takes longer (loading libraries)
- Try again, should be faster

## Features to Try

### Real-Time Data
```
What's Ethereum trading at?
How much are gas fees on Ethereum?
Tell me the latest crypto news
```

### Educational Questions
```
What is a smart contract?
Explain ERC20 tokens
How does blockchain work?
What's the difference between Layer 1 and Layer 2?
```

### Security Analysis
```
/analyze 0x... ethereum        → Ethereum contracts
/analyze 0x... bsc             → Binance Smart Chain
/analyze 0x... polygon         → Polygon
```

### Natural Conversation
```
Hi Nanette, how are you?
Can you help me understand rug pulls?
What should I look for in a safe contract?
```

## Stopping the Bot

Press `Ctrl+C` in both terminals (API and Bot)

## Next Steps

Once testing is successful:
1. See [README.md](bots/telegram-bot/README.md) for full features
2. Check [CONVERSATIONAL_FEATURES.md](CONVERSATIONAL_FEATURES.md) for conversation examples
3. Review [NANETTE_POSITIONING.md](NANETTE_POSITIONING.md) for personality guide

## Production Setup

For production deployment:
```bash
# Build
cd nanette/bots/telegram-bot
npm run build

# Run with PM2
pm2 start dist/index.js --name nanette-telegram
```

## Troubleshooting

### Can't Find Bot
- Make sure you used the exact username BotFather gave you
- Try searching with the full username including @

### Commands Not Working
- Make sure you include the `/` before commands
- Commands are case-sensitive

### Slow Responses
- First message takes longer (initializing)
- Analysis takes 10-60 seconds (normal)
- Conversation should be quick (2-5 seconds)

### API Connection Failed
Check:
1. API is running: `http://localhost:8000`
2. Test API: Open browser, go to `http://localhost:8000`
3. Should see: `{"name":"Nanette API","version":"1.0.0",...}`

## Success Checklist

- [ ] Got bot token from BotFather
- [ ] Added token to `.env`
- [ ] Installed npm dependencies
- [ ] Started Python API successfully
- [ ] Started Telegram bot successfully
- [ ] Bot responds to `/start`
- [ ] Bot responds to regular messages
- [ ] Price queries work
- [ ] Contract analysis works

If all checked ✅ - You're ready to go! 🐕

---

**Happy testing! Woof!** 🐕

_Created with love by Smalls for the Rin Community_
