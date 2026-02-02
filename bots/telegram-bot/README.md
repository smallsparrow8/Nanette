# Nanette Telegram Bot

German Shepherd guardian for the $RIN community - now on Telegram! 🐕

## Features

### Commands
- `/start` - Welcome message
- `/analyze <address>` - Analyze a smart contract
- `/help` - Get help and see all commands
- `/about` - Learn about Nanette and her creator
- `/greet` - Get a friendly greeting
- `/rintintin` - Learn about Rin Tin Tin and $RIN

### Natural Conversation
Just send any message to Nanette and she'll respond! Ask about:
- Current crypto prices
- Gas fees
- Blockchain concepts
- Smart contract questions
- Crypto news

## Setup

### Prerequisites
- Node.js 20+
- Telegram bot token (get from [@BotFather](https://t.me/botfather))
- Nanette API running (see main README)

### Getting a Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts:
   - Choose a name (e.g., "Nanette Guardian")
   - Choose a username (must end in 'bot', e.g., "nanette_rin_bot")
4. BotFather will give you a token like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
5. Add this token to your `.env` file as `TELEGRAM_BOT_TOKEN`

### Installation

```bash
# Navigate to telegram bot directory
cd bots/telegram-bot

# Install dependencies
npm install

# Build TypeScript
npm run build
```

### Configuration

Add to your `.env` file in the project root:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# API URL (if different from default)
API_URL=http://localhost:8000
```

### Running

Development mode (with auto-reload):
```bash
npm run dev
```

Production mode:
```bash
npm run build
npm start
```

## Testing

### 1. Start the Backend API

First, make sure the Nanette API is running:

```bash
# From project root
cd nanette
python -m api.main
```

The API should start on `http://localhost:8000`

### 2. Start the Telegram Bot

In a new terminal:

```bash
cd bots/telegram-bot
npm run dev
```

You should see:
```
✅ Nanette Telegram bot is online!
🐕 Ready to protect the crypto community!
```

### 3. Test in Telegram

1. Open Telegram
2. Search for your bot username (e.g., @nanette_rin_bot)
3. Start a chat and send `/start`

### Test Commands

```
/start
→ Welcome message

/help
→ See all commands and features

/greet
→ Get a friendly greeting

/about
→ Learn about Nanette and her creator

/rintintin
→ Learn about Rin Tin Tin and $RIN

/analyze 0x6B175474E89094C44Da98b954EedeAC495271d0F
→ Analyze DAI stablecoin contract
```

### Test Conversation

```
What's the price of Ethereum?
→ Nanette fetches current ETH price

How much are gas fees?
→ Current gas prices on Ethereum

Tell me about Bitcoin
→ Information about Bitcoin

What is DeFi?
→ Explanation of DeFi
```

## Features

### Smart Contract Analysis
Send contract addresses with `/analyze` command:
```
/analyze 0x6B175474E89094C44Da98b954EedeAC495271d0F ethereum
```

Nanette will provide:
- Overall safety score (0-100)
- Risk level assessment
- Vulnerability detection
- Tokenomics analysis
- Token information
- Recommendations

### Conversational AI
Just send regular messages:
```
What's Bitcoin trading at?
→ Current BTC price

Explain what smart contracts are
→ Educational explanation

Is this contract safe? 0x...
→ Quick safety check
```

### Real-Time Data
Nanette can fetch:
- Cryptocurrency prices (via CoinGecko)
- Gas prices (via Etherscan)
- Crypto news and updates
- Web search results
- Project information

## Bot Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message | `/start` |
| `/analyze` | Analyze contract | `/analyze 0x... ethereum` |
| `/help` | Show help | `/help` |
| `/about` | About Nanette | `/about` |
| `/greet` | Friendly greeting | `/greet` |
| `/rintintin` | Rin Tin Tin info | `/rintintin` |

## Conversation Examples

### Price Query
```
User: What's the current price of Ethereum?

Nanette: Woof! Let me check the current price for you!

According to the latest data I just fetched, Ethereum (ETH) is currently trading at $2,345 USD, up 3.2% in the last 24 hours.

📊 Market Data:
• Price: $2,345
• 24h Change: +3.2%
• Market Cap: $280B
• Volume: $165M

Remember: Always DYOR! 🐕
```

### Educational Query
```
User: What's the difference between ERC20 and ERC721?

Nanette: Woof! Great question! Let me explain...

[Detailed explanation with examples and analogies]
```

### Contract Analysis
```
User: /analyze 0x6B175474E89094C44Da98b954EedeAC495271d0F

Nanette: 🔍 Sniffing out the code... This may take a moment! 🐕

[Complete security analysis with scores and recommendations]
```

## Troubleshooting

### Bot Not Responding
1. Check that the bot token is correct in `.env`
2. Make sure the API is running (`http://localhost:8000`)
3. Check console for errors

### "Service Offline" Error
- The Python API is not running
- Start it with: `python -m api.main` from project root

### Analysis Takes Too Long
- Some contracts are complex and take time to analyze
- Typical analysis: 10-60 seconds
- If it times out (2 min), the contract may be too large

### Conversation Not Working
- Make sure you're sending regular text (not commands)
- The `/chat` endpoint must be working in the API
- Check API logs for errors

## Production Deployment

### Environment Variables
Ensure these are set in production:
```env
TELEGRAM_BOT_TOKEN=your_production_token
API_URL=https://your-api-domain.com
NODE_ENV=production
```

### Process Management
Use PM2 for production:

```bash
npm install -g pm2

# Build
npm run build

# Start with PM2
pm2 start dist/index.js --name nanette-telegram

# Save PM2 config
pm2 save

# Setup auto-restart on reboot
pm2 startup
```

### Monitoring
```bash
# View logs
pm2 logs nanette-telegram

# Monitor performance
pm2 monit

# Restart
pm2 restart nanette-telegram
```

## Security Notes

### Bot Token Security
- **NEVER** commit your bot token to Git
- Store in `.env` file (gitignored)
- Rotate token if compromised (use BotFather)

### User Privacy
- Conversation history stored in memory (cleared periodically)
- No personal data is logged
- Contract addresses are public blockchain data

### Rate Limiting
- Telegram enforces rate limits (30 msgs/second per chat)
- Bot handles this automatically
- Long messages are split appropriately

## Architecture

```
Telegram User
     ↓
Telegram Bot (Telegraf)
     ↓
Command Handlers
     ↓
FastAPI Backend
     ↓
Nanette AI Core (Claude + Tools)
     ↓
Response to User
```

## Development

### Project Structure
```
telegram-bot/
├── src/
│   ├── index.ts           # Main bot file
│   └── commands/
│       ├── analyze.ts     # Contract analysis
│       ├── chat.ts        # Conversation handler
│       ├── help.ts        # Help command
│       ├── about.ts       # About command
│       ├── greet.ts       # Greeting
│       └── rintintin.ts   # Rin Tin Tin info
├── package.json
├── tsconfig.json
└── README.md
```

### Adding New Commands

1. Create command file in `src/commands/`
2. Export command handler function
3. Import in `src/index.ts`
4. Add bot command registration

Example:
```typescript
// src/commands/newcommand.ts
import { Context } from 'telegraf';

export async function newCommand(ctx: Context) {
  return ctx.reply('New command response!');
}

// src/index.ts
import { newCommand } from './commands/newcommand';
bot.command('newcommand', newCommand);
```

## Support

For issues or questions:
- Check main [README.md](../../README.md)
- See [CONVERSATIONAL_FEATURES.md](../../CONVERSATIONAL_FEATURES.md)
- Review Telegram [Bot API docs](https://core.telegram.org/bots/api)

---

**Created with love by Smalls for the Rin Community** 🐕❤️
