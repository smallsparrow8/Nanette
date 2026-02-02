# Nanette's Conversational Features

## Overview

Nanette can now hold natural conversations with users about cryptocurrency, blockchain, and current events. She has access to real-time information from the web and blockchain networks.

## Features

### 1. Natural Conversation
- Chat naturally with Nanette beyond slash commands
- Mention @Nanette in any channel or DM her directly
- She maintains conversation context and remembers previous messages
- German Shepherd personality shines through in every interaction

### 2. Real-Time Information Access

Nanette can fetch and provide current information about:

#### Cryptocurrency Prices
```
User: "What's the price of Ethereum?"
Nanette: "Let me check the current price for you! According to the latest data I just fetched, Ethereum (ETH) is currently trading at $..."
```

#### Gas Prices
```
User: "How much are gas fees on Ethereum right now?"
Nanette: "I just checked the current gas prices on Ethereum. Safe: 20 Gwei, Standard: 25 Gwei, Fast: 30 Gwei..."
```

#### Crypto News
```
User: "What's the latest news about DeFi?"
Nanette: "Let me fetch the latest news for you! Here's what's happening in the DeFi space..."
```

#### Crypto Project Information
```
User: "Tell me about Bitcoin"
Nanette: "I just looked up detailed information about Bitcoin. Bitcoin (BTC) is the first and largest cryptocurrency by market cap..."
```

#### Web Search
```
User: "What is Ethereum 2.0?"
Nanette: "Let me search for that information! Ethereum 2.0, also known as 'The Merge', refers to..."
```

### 3. Context-Aware Responses

Nanette understands context and can:
- Remember previous messages in the conversation
- Reference earlier topics
- Build on previous explanations
- Maintain thread continuity

### 4. Educational Conversations

Beyond analysis, Nanette can:
- Explain blockchain concepts
- Answer questions about cryptocurrency
- Teach about smart contracts
- Discuss security best practices
- Share implementation patterns

## How to Use

### In Discord

#### Slash Commands (Structured Analysis)
```
/analyze 0x... - Analyze a smart contract
/help - Get command help
/about - Learn about Nanette
/rintintin - Learn about Rin Tin Tin and $RIN
/greet - Get a friendly greeting
```

#### Natural Conversation
```
# Mention Nanette in a channel
@Nanette what's the current price of Bitcoin?

# Direct message (no mention needed)
Tell me about the latest Ethereum updates
```

### Query Types Nanette Understands

#### Price Queries
- "What's the price of [crypto]?"
- "How much is [crypto] worth?"
- "What's [crypto] trading at?"
- "[crypto] price"

#### Gas/Fee Queries
- "What are gas prices on Ethereum?"
- "How much are transaction fees?"
- "Current gas fees"
- "Gwei prices"

#### News Queries
- "What's the latest news about [topic]?"
- "Recent updates on [crypto]"
- "Tell me what's happening with [project]"

#### Information Queries
- "What is [concept]?"
- "Tell me about [project]"
- "Explain [technology]"
- "How does [feature] work?"

#### Comparison Queries
- "What's the difference between [A] and [B]?"
- "Compare [crypto1] and [crypto2]"
- "Which is better, [A] or [B]?"

## Available Tools

Nanette has access to these tools to provide current information:

### 1. Web Search
- **Purpose**: Search the web for current information
- **Use Cases**: General information, explanations, concepts
- **Data Source**: DuckDuckGo API

### 2. Crypto Price Lookup
- **Purpose**: Get current cryptocurrency prices
- **Use Cases**: Price queries, market data
- **Data Source**: CoinGecko API
- **Includes**: Price, 24h change, market cap, volume

### 3. Crypto Information
- **Purpose**: Detailed project information
- **Use Cases**: Learning about projects, finding links
- **Data Source**: CoinGecko API
- **Includes**: Description, links, social media, scores

### 4. Gas Price Tracker
- **Purpose**: Current blockchain gas prices
- **Use Cases**: Transaction cost planning
- **Data Source**: Etherscan API
- **Blockchains**: Ethereum (others coming soon)

### 5. Crypto News Search
- **Purpose**: Latest cryptocurrency news
- **Use Cases**: Staying informed, research
- **Data Source**: Web search focused on crypto news

## Technical Implementation

### Architecture

```
Discord Message → Discord Bot (chat.ts)
                     ↓
              FastAPI Backend (/chat endpoint)
                     ↓
           Orchestrator (orchestrator.py)
                     ↓
         Nanette AI Core (personality.py)
                     ↓
              ┌──────┴──────┐
              ↓             ↓
        Claude API    Nanette Tools
              ↓             ↓
         AI Response   Real-time Data
              └──────┬──────┘
                     ↓
             Combined Response
```

### Tool Integration Flow

1. **User sends message** → Discord bot receives it
2. **Message analysis** → Nanette checks if tools are needed
3. **Tool execution** → Fetches current data if required
4. **Context enhancement** → Adds tool results to conversation
5. **AI processing** → Claude generates response with current data
6. **Response delivery** → User receives informed answer

### Conversation History

- Stored per channel (or per user in DMs)
- Limited to last 20 messages to manage token usage
- Cleared automatically when conversation becomes stale
- In production: Use Redis or database for persistence

## Examples

### Example 1: Price and Analysis
```
User: @Nanette What's the current price of Ethereum and is it a good time to buy?

Nanette: Woof! Let me check the current price for you!

According to the latest data I just fetched, Ethereum (ETH) is currently trading at $2,345 USD, up 3.2% in the last 24 hours.

As for whether it's a good time to buy - I'm a guardian, not a financial advisor! But I can tell you what to consider:

🔍 Current Market Indicators:
- Price trend: Upward momentum (24h)
- Market cap: $280B (2nd largest)
- Volume: Strong trading activity

⚠️ Important Considerations:
- Market is volatile - never invest more than you can lose
- Research upcoming events (upgrades, regulations)
- Check technical analysis and support levels
- Diversify your portfolio

Remember: Always DYOR (Do Your Own Research)! I can analyze contracts and provide data, but investment decisions are yours to make! 🐕
```

### Example 2: Educational Conversation
```
User: @Nanette What's the difference between ERC20 and ERC721?

Nanette: Woof! Great question! Let me explain these two important token standards:

**ERC20 (Fungible Tokens):**
Think of these like dollars - every token is identical and interchangeable.
- Every token has the same value
- Used for: Cryptocurrencies, utility tokens
- Example: USDT, LINK, $RIN
- Analogy: Like identical coins in your pocket

**ERC721 (Non-Fungible Tokens - NFTs):**
Think of these like unique trading cards - each token is one-of-a-kind.
- Each token has unique properties
- Used for: NFTs, collectibles, digital art
- Example: CryptoPunks, Bored Apes
- Analogy: Like numbered limited edition items

**Key Differences:**
1. **Divisibility**: ERC20 can be divided (0.5 tokens), ERC721 cannot
2. **Uniqueness**: ERC20 tokens are identical, ERC721 are unique
3. **Use Case**: ERC20 for currency, ERC721 for ownership

**For Developers:**
```solidity
// ERC20: fungible
function transfer(address to, uint256 amount)

// ERC721: non-fungible
function transferFrom(address from, address to, uint256 tokenId)
```

Want to learn more about implementing these? I can analyze contracts that use them! 🐕
```

### Example 3: Contract Analysis + Current Data
```
User: @Nanette Analyze 0x6B175474E89094C44Da98b954EedeAC495271d0F and tell me its current price

Nanette: Woof! I'll analyze that contract and fetch the current price!

[Analyzes contract...]

**Contract Analysis:** DAI Stablecoin
Overall Safety Score: 95/100 (VERY LOW RISK)

This is the official DAI stablecoin contract - one of the most trusted in DeFi!

✅ Security Highlights:
- Battle-tested OpenZeppelin libraries
- Multi-signature governance
- Extensive audits by multiple firms
- Years of safe operation

**Current Market Data** (just fetched):
- Price: $1.00 USD (stable)
- 24h Change: +0.01%
- Market Cap: $5.2B
- Volume: $180M (24h)

💡 Why DAI is Special:
It's a decentralized stablecoin - maintains $1 value through smart contract mechanisms rather than bank reserves. This is real utility in action!

Always DYOR! 🐕
```

## Features in Development

### Coming Soon
- [ ] Telegram bot conversation support
- [ ] Multi-chain real-time data
- [ ] NFT floor price tracking
- [ ] DeFi protocol TVL data
- [ ] Social sentiment analysis
- [ ] Developer activity metrics
- [ ] Wallet address analysis
- [ ] Token holder distribution

### Future Enhancements
- Voice conversation support
- Multi-language conversations
- Advanced analytics
- Custom alerts
- Community voting integration

## Privacy & Data

### What Nanette Remembers
- Conversation context (last 20 messages)
- User preferences (in future versions)
- Analysis history (for learning)

### What Nanette NEVER Stores
- Private keys or seed phrases
- Personal financial information
- Wallet balances (unless you share them)

### Data Sources
All data is fetched from public APIs:
- CoinGecko (crypto prices & info)
- Etherscan (gas prices & blockchain data)
- DuckDuckGo (web search)

No personal data is sent to these services - only search queries.

## Best Practices

### For Users

1. **Be Specific**: "What's ETH price?" is better than "What's the price?"
2. **Ask Follow-ups**: Nanette remembers context - build on previous answers
3. **Request Analysis**: For detailed contract analysis, use `/analyze` command
4. **Stay Safe**: Never share private keys or seed phrases, even with Nanette

### For Developers

1. **Conversation Limits**: Keep history to 20 messages max
2. **Error Handling**: Always handle API timeouts gracefully
3. **Rate Limiting**: Respect API rate limits (CoinGecko: 50 calls/min)
4. **Caching**: Consider caching price data for 1-5 minutes

## Troubleshooting

### "I'm having trouble connecting"
- API service may be down
- Check network connectivity
- Try again in a moment

### "No results found"
- Check spelling of crypto symbols
- Try full name instead of symbol
- Some newer tokens may not be in CoinGecko

### Slow Responses
- Fetching real-time data takes a few seconds
- Multiple tool calls compound wait time
- This is normal for data-rich responses

## Credits

Built with:
- **Claude API** (Anthropic) - AI personality
- **CoinGecko API** - Crypto data
- **Etherscan API** - Blockchain data
- **DuckDuckGo API** - Web search
- **Discord.js** - Discord integration
- **FastAPI** - Backend API

---

**Remember**: Nanette is a guardian and educator, providing information and analysis. She's not a financial advisor. Always do your own research before making investment decisions! 🐕

**Created with love by Smalls for the Rin Community** ❤️
