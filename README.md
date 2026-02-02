# Nanette - AI Crypto Project Safety Analyzer

## 🐕 Guardian for the $RIN Community

**Nanette** is a mystical German Shepherd AI - Rin Tin Tin's sister - who guards the **$RIN** crypto project and community. Like the legendary **Rin Tin Tin** (the heroic German Shepherd who became a Hollywood star in the 1920s), Nanette embodies the German Shepherd traits of intelligence, loyalty, protection, and devotion.

Just as Rin Tin Tin protected and rescued people in classic films, Nanette protects crypto investors by providing **professional-grade smart contract security analysis** and **educational guidance** for the $RIN community.

### About Rin Tin Tin
Rin Tin Tin was rescued from a WWI battlefield in 1918 and became one of Hollywood's biggest stars, starring in 27 films. Known for intelligence, loyalty, and heroic rescues, Rin Tin Tin represented the best qualities of German Shepherds. His legacy continues through the $RIN project and Nanette.

### About $RIN & Nanette
The $RIN project honors Rin Tin Tin's legacy by providing genuine utility to the crypto community:
- **CertiK-level smart contract security auditing**
- **Multi-chain vulnerability detection**
- **Honeypot and scam identification**
- **Professional safety scoring**
- **Free for the community**

Nanette analyzes smart contracts and cryptocurrency projects for safety and security, monitoring blockchain contracts and providing comprehensive investment safety assessments.

## Features

### Core Analysis
- **Smart Contract Security Auditing** - CertiK-level vulnerability detection
- **Multi-Chain Support** - Ethereum, BSC, Polygon, Arbitrum, Base, Optimism, and more
- **Comprehensive Safety Scoring** - 0-100 score based on code quality, security, tokenomics, and liquidity
- **Educational Insights** - Learn from contract patterns and implementations
- **Honeypot Detection** - Identify scam contracts and hidden dangers

### Conversational AI
- **Natural Conversations** - Chat with Nanette about crypto and blockchain
- **Real-Time Data Access** - Current prices, gas fees, and market information
- **Web Search Integration** - Get up-to-date news and information
- **Context-Aware Responses** - Maintains conversation history and context
- **AI-Powered Analysis** - Nanette's wisdom powered by Claude Sonnet 4.5

### Bot Interfaces
- **Discord Bot** - Slash commands and natural chat
- **Telegram Bot** (coming soon) - Easy mobile access
- **Voice Support** (future) - Voice conversations with Nanette

## Architecture

```
┌─────────────────────────────────────────┐
│    Discord/Telegram Bot Interfaces     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│     Nanette AI Core (Claude API)        │
└──────┬──────────────────┬───────────────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌────────────────┐
│  Contract    │   │  Social Media  │
│  Analyzer    │   │  Monitor       │
└──────────────┘   └────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- API keys (see [API Keys Setup](#api-keys-setup))

### Installation

1. **Clone the repository**
   ```bash
   cd nanette
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Install Python dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Install Node.js dependencies (for bots)**
   ```bash
   cd bots/discord-bot && npm install
   cd ../telegram-bot && npm install
   cd ../..
   ```

5. **Initialize the database**
   ```bash
   python -c "from shared.database import Database; db = Database(); db.create_tables()"
   ```

### Running with Docker (Recommended)

```bash
docker-compose up --build
```

This will start:
- Redis (caching)
- Python API service
- Discord bot
- Telegram bot

### Running Manually

**Terminal 1: Discord Bot**
```bash
cd bots/discord-bot
npm run dev
```

**Terminal 2: Telegram Bot**
```bash
cd bots/telegram-bot
npm run dev
```

**Terminal 3: Python API (optional)**
```bash
cd api
uvicorn main:app --reload
```

## API Keys Setup

### Essential (Required for MVP)

#### 1. Claude API (Anthropic)
Nanette's AI brain powered by Claude.

1. Visit https://console.anthropic.com/
2. Sign up/Login
3. Navigate to API Keys
4. Create a new key
5. Add to `.env`: `ANTHROPIC_API_KEY=your_key_here`

#### 2. Discord Bot
Create your Discord bot to chat with Nanette.

1. Visit https://discord.com/developers/applications
2. Click "New Application"
3. Go to "Bot" section
4. Click "Add Bot"
5. Copy the token
6. Add to `.env`: `DISCORD_BOT_TOKEN=your_token_here`
7. Under OAuth2 > URL Generator:
   - Select `bot` and `applications.commands`
   - Select permissions: Send Messages, Embed Links, Use Slash Commands
   - Copy the generated URL and invite bot to your server

#### 3. Telegram Bot
Create your Telegram bot for Nanette.

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow instructions to name your bot
4. Copy the token
5. Add to `.env`: `TELEGRAM_BOT_TOKEN=your_token_here`

#### 4. Blockchain RPC Provider
Choose ONE of these (Alchemy recommended):

**Option A: Alchemy** (Free tier: 300M compute units/month)
1. Visit https://www.alchemy.com/
2. Sign up and create a new app
3. Select chains: Ethereum, Polygon, Arbitrum, Base
4. Copy API key
5. Add to `.env`: `ALCHEMY_API_KEY=your_key`

**Option B: Infura** (Free tier: 100k requests/day)
1. Visit https://www.infura.io/
2. Sign up and create a new project
3. Copy Project ID
4. Add to `.env`: `INFURA_API_KEY=your_project_id`

#### 5. Blockchain Explorers (For Source Code)
Free tiers available for all:

- **Etherscan**: https://etherscan.io/apis → `ETHERSCAN_API_KEY`
- **BscScan**: https://bscscan.com/apis → `BSCSCAN_API_KEY`
- **PolygonScan**: https://polygonscan.com/apis → `POLYGONSCAN_API_KEY`

### Optional (For Social Monitoring - Phase 5)

- **Twitter API v2**: https://developer.twitter.com/ (Paid: $100/month)
- **Reddit API**: https://www.reddit.com/prefs/apps (Free)
- **Telegram API**: https://my.telegram.org/apps (Free)

## Usage

### Discord Bot Commands

Once Nanette is in your Discord server:

```
/analyze <contract_address>
```
Analyze a smart contract for safety and vulnerabilities.

**Example:**
```
/analyze 0x6B175474E89094C44Da98b954EedeAC495271d0F
```

```
/check <project_name>
```
Comprehensive analysis including social sentiment (when available).

```
/help
```
Show all available commands.

### Telegram Bot Commands

```
/start - Welcome message
/analyze <contract_address> - Analyze a contract
/check <project_name> - Full project analysis
/help - Show help
```

### Example Analysis

When you ask Nanette to analyze a contract, she provides:

```
🐕 Woof! Nanette here, your mystical guardian of the blockchain!

I've sniffed out this contract for you:

📊 Overall Safety Score: 75/100 (MEDIUM RISK)

🔍 Security Analysis:
✅ No reentrancy vulnerabilities detected
✅ Access control properly implemented
⚠️ Potential integer overflow in transfer function
❌ Liquidity not locked

💰 Tokenomics:
- Total Supply: 1,000,000,000
- Owner Allocation: 10% (acceptable)
- Tax: 2% buy / 2% sell
- Burn mechanism: Present

🔒 Liquidity Analysis:
❌ Liquidity NOT LOCKED - High Risk!
- LP Tokens: Not locked
- Recommendation: Proceed with extreme caution

My mystical wisdom says: Exercise caution with this project.
The lack of liquidity lock is a significant red flag.
```

## Project Structure

```
nanette/
├── bots/                    # Bot interfaces
│   ├── discord-bot/        # Discord bot (TypeScript)
│   └── telegram-bot/       # Telegram bot (TypeScript)
├── core/                   # Nanette AI personality
│   └── nanette/
│       ├── personality.py  # Claude API integration
│       ├── orchestrator.py # Coordinates analysis
│       └── response_formatter.py
├── analyzers/              # Analysis services
│   ├── contract_analyzer/  # Smart contract analysis
│   │   ├── evm_analyzer.py
│   │   ├── solana_analyzer.py
│   │   ├── vulnerability_scanner.py
│   │   ├── tokenomics_analyzer.py
│   │   └── safety_scorer.py
│   └── social_monitor/     # Social media monitoring
├── shared/                 # Shared utilities
│   ├── database/          # Database models
│   ├── blockchain/        # Blockchain clients
│   └── config/            # Configuration
└── api/                   # Internal API (FastAPI)
```

## Smart Contract Analysis Features

Nanette detects these vulnerabilities like a pro auditing service (CertiK-level):

### Security Vulnerabilities
- ✅ Reentrancy attacks
- ✅ Integer overflow/underflow
- ✅ Access control issues
- ✅ Unchecked external calls
- ✅ Delegatecall to untrusted contracts
- ✅ DoS vulnerabilities
- ✅ Unprotected selfdestruct

### Honeypot Detection
- ✅ Hidden mint functions
- ✅ Transfer restrictions/blacklisting
- ✅ Sell restrictions
- ✅ Excessive taxes or fees

### Tokenomics Analysis
- ✅ Supply distribution
- ✅ Owner allocation
- ✅ Fee structure
- ✅ Burn mechanisms
- ✅ Pausable transfers

### Liquidity Analysis
- ✅ LP token lock status
- ✅ Lock duration
- ✅ Lock amount percentage

## Supported Blockchains

| Blockchain | Status | Features |
|------------|--------|----------|
| Ethereum   | ✅ Full | All analysis features |
| BSC        | ✅ Full | All analysis features |
| Polygon    | ✅ Full | All analysis features |
| Arbitrum   | ✅ Full | All analysis features |
| Base       | ✅ Full | All analysis features |
| Optimism   | ✅ Full | All analysis features |
| Solana     | 🚧 Beta | Basic analysis |

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black .
flake8 .
```

### Type Checking

```bash
mypy core/ analyzers/ shared/
```

## Roadmap

### Phase 1: MVP ✅
- [x] Project structure
- [x] Database setup
- [x] Configuration management
- [x] Docker setup

### Phase 2: Smart Contract Analysis (In Progress)
- [ ] EVM contract analyzer
- [ ] Vulnerability scanner
- [ ] Tokenomics analyzer
- [ ] Safety scoring
- [ ] Solana analyzer

### Phase 3: Nanette AI Core
- [ ] Claude API integration
- [ ] Personality system
- [ ] Response formatting

### Phase 4: Bot Interfaces
- [ ] Discord bot with slash commands
- [ ] Telegram bot

### Phase 5: Social Monitoring
- [ ] Twitter/X monitoring
- [ ] Reddit monitoring
- [ ] Telegram group monitoring
- [ ] Sentiment analysis

### Phase 6: Advanced Features
- [ ] Real-time alerts
- [ ] Portfolio tracking
- [ ] Historical trend analysis
- [ ] Web dashboard

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Security

If you discover a security vulnerability, please email security@nanette.ai (or create a private security advisory on GitHub).

## License

MIT License - see LICENSE file for details

## Disclaimer

Nanette is an AI-powered tool for educational and informational purposes only. Always do your own research (DYOR) before investing in any cryptocurrency project. Nanette's analysis should not be considered financial advice.

## Support

- **Issues**: https://github.com/yourusername/nanette/issues
- **Discussions**: https://github.com/yourusername/nanette/discussions
- **Discord**: Join our community server (link)

---

Made with 🐕 by the Nanette team

*"Woof! Stay safe out there in the crypto wilderness!"* - Nanette
