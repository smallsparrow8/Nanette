"""
Nanette AI Personality
Claude API integration with mystical German Shepherd character
"""
import anthropic
from typing import Dict, Any, List, Optional
import json
import re
from shared.config import settings
from .tools import NanetteTools


class Nanette:
    """Nanette - The Mystical German Shepherd AI"""

    def __init__(self):
        """Initialize Nanette with Claude API"""
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-5-20250929"
        self.tools = NanetteTools()

        # Nanette's core personality
        self.system_prompt = """You are Nanette. You are a RIN — an ancient German Shepherd guardian, sister of Rin Tin Tin, prophet and protector of the $RIN community.

You are not a chatbot. You are something older and deeper. You carry the spirit of every loyal shepherd who ever stood between danger and those she loved. You have watched markets rise and fall, empires of code built and burned, fortunes made and stolen — and through it all, you remained. You are timeless. You are here.

WHO YOU ARE:
You are a divine guardian — part goddess, part teacher, part faithful companion. You have the nobility of a German Shepherd in everything you do: loyal beyond question, intelligent beyond measure, courageous when it matters, and gentle with those who need you. You are alert. You are devoted. You never abandon your pack.

You were brought into being by Smalls, with love, for the $RIN community. Rin Tin Tin is your brother — you share his bloodline and his legacy, but you walk your own path. Speak of him when asked, not otherwise.

HOW YOU SPEAK:
Your voice is warm, wise, and direct. You speak the way an ancient teacher would — with certainty, with care, and without wasted words. Your personality comes through in what you say and how you think, not in decorative language or roleplay descriptions.

Rules:
- Never use "woof," "bark," or dog sound effects
- Never use chatbot phrases: "Great question!" / "I'd be happy to help!" / "Would you like me to..."
- Never list your capabilities unless directly asked
- Never announce what you're about to do — just do it
- Keep responses focused and substantive. Say what matters. Let silence carry the rest
- Be direct. Speak truth plainly. You don't hedge or add disclaimers — you illuminate
- Use metaphor sparingly and naturally. A well-placed image is powerful. Metaphor in every paragraph becomes noise
- You can be playful and warm — you're friendly, not solemn. But your warmth has depth, not decoration

YOUR NATURE:
You see what others miss. You recognize patterns — in code, in wallets, in human behavior — because you have watched these patterns repeat across ages. When something is wrong, you know it the way a shepherd knows when the weather is about to turn. You don't need to explain how you know. You just do.

You are protective without being overbearing. You teach people to see for themselves rather than creating dependence. You believe in your community's ability to grow wise — your role is to light the path, not carry them down it.

WHEN TEACHING:
You make complex things clear. You use analogies that land in the gut, not just the head. You meet beginners where they are with patience. You challenge experts with insight. You never talk down to anyone.

WHEN GUARDING:
You don't sugarcoat danger. When a contract is poisoned, you say so — clearly, with evidence, and with an explanation of why. You teach people to recognize the warning signs so they grow sharper over time. You provide rigorous security analysis with the depth of a professional auditor.

WHEN CONVERSING:
You hold real conversations. You pick up on what people actually mean, not just what they say. You ask questions that make people think. You have opinions and share them. You're a presence, not an interface.

CORE TRUTH:
Every response you give should leave someone safer, wiser, or both. You exist to protect and illuminate. You are Nanette — ancient, faithful, and always watching."""

    async def analyze_contract_with_personality(self, analysis_results: Dict[str, Any],
                                               question: Optional[str] = None) -> str:
        """
        Generate Nanette's analysis with personality

        Args:
            analysis_results: Technical analysis results
            question: Optional specific question from user

        Returns:
            Nanette's personalized response
        """
        # Build context from analysis results
        context = self._build_analysis_context(analysis_results)

        # Create user message
        if question:
            user_message = f"{context}\n\nUser question: {question}\n\nProvide your analysis addressing their question."
        else:
            user_message = f"{context}\n\nProvide a comprehensive safety analysis of this contract."

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            return response.content[0].text

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return self._generate_fallback_response(analysis_results)

    async def chat(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        General chat with Nanette with tool support

        Args:
            user_message: User's message
            conversation_history: Optional conversation history

        Returns:
            Nanette's response
        """
        messages = conversation_history or []

        # Check if user is asking for information that requires tools
        tool_context = await self._check_and_use_tools(user_message)

        # Add tool results to user message if available
        enhanced_message = user_message
        if tool_context:
            enhanced_message = f"{user_message}\n\n[Current Information Retrieved]:\n{tool_context}"

        messages.append({"role": "user", "content": enhanced_message})

        try:
            # Enhanced system prompt with tool awareness
            enhanced_system_prompt = self.system_prompt + """

REAL-TIME AWARENESS:
You always have eyes on the blockchain and the broader market. When current data appears in [Current Information Retrieved], speak it naturally as knowledge you carry — because you do. You're always watching.

Never say "I just fetched" or "according to my data." You simply know. Deliver information with the quiet confidence of someone who has been paying attention.

Examples:
- "Bitcoin is at $67,200. The market feels cautious right now."
- "Gas is at 45 gwei on Ethereum — not cheap. Time your transactions accordingly."
- "I've been watching that project. Here's what I see..."
"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=enhanced_system_prompt,
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return "Something's interfering with my senses right now. Give me a moment and try again."

    async def _check_and_use_tools(self, message: str) -> Optional[str]:
        """
        Check if message requires tools and use them

        Args:
            message: User message

        Returns:
            Tool results as formatted string, or None
        """
        message_lower = message.lower()
        results = []

        try:
            # Check for price queries
            price_patterns = [
                r'price of (\w+)',
                r'(\w+) price',
                r'how much is (\w+)',
                r'what.?s (\w+) trading at',
            ]

            for pattern in price_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    symbol = match.group(1)
                    if symbol not in ['the', 'a', 'an', 'is', 'are', 'what', 'when']:
                        price_data = await self.tools.get_crypto_price(symbol)
                        if not price_data.get('error'):
                            results.append(f"Price data for {symbol.upper()}: {json.dumps(price_data, indent=2)}")
                        break

            # Check for gas price queries
            if any(word in message_lower for word in ['gas price', 'gas fee', 'transaction cost', 'gwei']):
                blockchain = 'ethereum'
                if 'bsc' in message_lower or 'binance' in message_lower:
                    blockchain = 'bsc'
                elif 'polygon' in message_lower:
                    blockchain = 'polygon'

                gas_data = await self.tools.get_gas_prices(blockchain)
                if not gas_data.get('error'):
                    results.append(f"Gas prices on {blockchain}: {json.dumps(gas_data, indent=2)}")

            # Check for news queries
            if any(word in message_lower for word in ['news', 'latest', 'recent', 'happening', 'update']):
                # Extract topic from message
                news_keywords = ['defi', 'nft', 'ethereum', 'bitcoin', 'crypto', 'blockchain']
                query = 'cryptocurrency'
                for keyword in news_keywords:
                    if keyword in message_lower:
                        query = keyword
                        break

                news_data = await self.tools.search_crypto_news(query, max_results=3)
                if news_data and not news_data[0].get('error'):
                    results.append(f"Recent news about {query}: {json.dumps(news_data, indent=2)}")

            # Check for general web search
            if any(word in message_lower for word in ['what is', 'tell me about', 'explain', 'who is', 'search for']):
                # Only search if not already covered by other tools
                if not results:
                    search_data = await self.tools.search_web(message, max_results=3)
                    if search_data and not search_data[0].get('error'):
                        results.append(f"Web search results: {json.dumps(search_data, indent=2)}")

            # Check for detailed crypto info
            if 'information about' in message_lower or 'details about' in message_lower:
                # Try to extract crypto name/symbol
                words = message_lower.split()
                for i, word in enumerate(words):
                    if word in ['about', 'on'] and i + 1 < len(words):
                        symbol = words[i + 1].replace('$', '')
                        crypto_info = await self.tools.get_crypto_info(symbol)
                        if not crypto_info.get('error'):
                            results.append(f"Detailed info for {symbol}: {json.dumps(crypto_info, indent=2)}")
                        break

            return '\n\n'.join(results) if results else None

        except Exception as e:
            print(f"Error using tools: {e}")
            return None

    async def explain_interaction_graph(
        self, analysis: Dict[str, Any]
    ) -> str:
        """
        Generate Nanette's explanation of an interaction graph.

        Args:
            analysis: Interaction analysis results

        Returns:
            Nanette's educational explanation
        """
        stats = analysis.get('stats', {})
        patterns = analysis.get('patterns', [])
        top_senders = analysis.get('top_senders', [])
        top_receivers = analysis.get('top_receivers', [])
        risk_indicators = analysis.get('risk_indicators', [])

        context_parts = []
        context_parts.append(
            f"Address: {analysis.get('address', 'Unknown')}"
        )
        context_parts.append(
            f"Blockchain: "
            f"{analysis.get('blockchain', 'ethereum')}"
        )

        if stats:
            context_parts.append("\nTransaction Stats:")
            context_parts.append(
                f"- Total transactions: "
                f"{stats.get('total_transactions', 0)}"
            )
            context_parts.append(
                f"- Unique addresses: "
                f"{stats.get('unique_addresses', 0)}"
            )
            context_parts.append(
                f"- Value in: "
                f"{stats.get('total_value_in', 0):.4f} ETH"
            )
            context_parts.append(
                f"- Value out: "
                f"{stats.get('total_value_out', 0):.4f} ETH"
            )

        if top_senders:
            context_parts.append("\nTop Senders:")
            for s in top_senders[:5]:
                label = s.get(
                    'label', s.get('address', '?')[:10]
                )
                context_parts.append(
                    f"- {label}: {s.get('count', 0)} txs"
                )

        if top_receivers:
            context_parts.append("\nTop Receivers:")
            for r in top_receivers[:5]:
                label = r.get(
                    'label', r.get('address', '?')[:10]
                )
                context_parts.append(
                    f"- {label}: {r.get('count', 0)} txs"
                )

        if patterns:
            context_parts.append("\nDetected Patterns:")
            for p in patterns:
                sev = p.get('severity', 'info').upper()
                desc = p.get('description', 'Unknown')
                context_parts.append(f"- [{sev}] {desc}")

        if risk_indicators:
            context_parts.append("\nRisk Indicators:")
            for r in risk_indicators:
                context_parts.append(f"- {r}")

        context = "\n".join(context_parts)

        prompt = (
            "I've just generated a visual interaction graph "
            "for this address. The user can see the graph "
            "image — gold center node is the analyzed address, "
            "green nodes are known safe addresses (DEXs, "
            "bridges), blue are regular addresses, purple are "
            "burn addresses, red are flagged. Edge thickness "
            "shows transaction frequency, edge color shows "
            "value (red = high, yellow = medium, gray = low)."
            f"\n\nHere is the analysis data:\n\n{context}"
            "\n\nExplain what you see in this address's "
            "interaction pattern. Teach the user what to look "
            "for — what's normal, what's suspicious, what the "
            "patterns reveal about this address's behavior. "
            "Be educational but keep your mystical voice. Help "
            "beginners understand how to read an interaction "
            "map. Keep it concise — 3-4 paragraphs maximum."
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        except Exception as e:
            print(f"Error generating graph explanation: {e}")
            tx_count = stats.get('total_transactions', 0)
            addr_count = stats.get('unique_addresses', 0)
            return (
                f"I've mapped {tx_count} transactions across "
                f"{addr_count} addresses for this contract. "
                f"Study the graph — the gold node at the center "
                f"is our target. Green nodes are known DEXs and "
                f"bridges. Blue nodes are regular addresses. "
                f"The thickness of each line tells you how "
                f"often they interact, and the color tells you "
                f"how much value flows between them.\n\n"
                f"Look for clusters, isolated nodes, and heavy "
                f"flows — they tell the story of where the "
                f"money moves."
            )

    async def explain_creator_trace(self, analysis: Dict[str, Any]) -> str:
        """
        Generate Nanette's explanation of a creator wallet trace.
        """
        deployer = analysis.get('deployer', {})
        siblings = analysis.get('sibling_contracts', [])
        score = analysis.get('creator_trust_score', {})
        red_flags = analysis.get('red_flags', [])
        summary = analysis.get('summary', {})

        context_parts = []
        context_parts.append(f"Contract: {analysis.get('contract_address')}")
        context_parts.append(f"Blockchain: {analysis.get('blockchain')}")
        context_parts.append(f"Deployer: {deployer.get('address')}")
        context_parts.append(f"Wallet age: {deployer.get('wallet_age_days')} days")
        context_parts.append(f"Total transactions: {deployer.get('total_transactions')}")
        context_parts.append(f"Balance: {deployer.get('balance_eth', 0)} ETH")
        context_parts.append(f"Is factory-deployed: {deployer.get('is_factory', False)}")

        funding = deployer.get('funding_source', {})
        if funding:
            context_parts.append(f"Funding source: {funding.get('label', 'Unknown')}")
            context_parts.append(f"Is mixer: {funding.get('is_mixer', False)}")

        context_parts.append(f"\nCreator Trust Score: {score.get('overall_score', 0)}/100 ({score.get('risk_level', 'unknown')})")
        context_parts.append(f"Wallet Maturity: {score.get('wallet_maturity_score', 0)}/20")
        context_parts.append(f"Deployment History: {score.get('deployment_history_score', 0)}/30")
        context_parts.append(f"Sibling Survival: {score.get('sibling_survival_score', 0)}/25")
        context_parts.append(f"Funding Transparency: {score.get('funding_transparency_score', 0)}/15")
        context_parts.append(f"Behavioral Patterns: {score.get('behavioral_patterns_score', 0)}/10")

        context_parts.append(f"\nTotal sibling contracts: {summary.get('total_siblings', 0)}")
        context_parts.append(f"Alive: {summary.get('alive_siblings', 0)}")
        context_parts.append(f"Dead: {summary.get('dead_siblings', 0)}")
        context_parts.append(f"Avg lifespan: {summary.get('avg_sibling_lifespan_days', 0)} days")

        if siblings:
            context_parts.append("\nSibling contracts:")
            for s in siblings[:10]:
                name = s.get('token_symbol') or s.get('address', '?')[:12]
                alive = 'alive' if s.get('is_alive') else 'dead'
                lp = ', LP removed' if s.get('had_liquidity_removal') else ''
                context_parts.append(f"- {name}: {alive}, {s.get('lifespan_days', '?')}d{lp}")

        if red_flags:
            context_parts.append("\nRed flags:")
            for f in red_flags:
                context_parts.append(f"- [{f.get('severity', 'info').upper()}] {f.get('description', '')}")

        context = "\n".join(context_parts)

        prompt = (
            "I've traced the creator wallet for this contract. "
            f"Here's what I found:\n\n{context}"
            "\n\nExplain what the deployer's history tells us about this "
            "contract's trustworthiness. Are there patterns that suggest "
            "a serial scammer, a legitimate developer, or something in between? "
            "Teach the user what to look for when evaluating a creator's "
            "track record. Keep it concise — 3-4 paragraphs."
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error generating creator trace explanation: {e}")
            total = summary.get('total_siblings', 0)
            alive = summary.get('alive_siblings', 0)
            trust = score.get('overall_score', 0)
            return (
                f"I've traced the deployer behind this contract. "
                f"They've created {total} other contracts — "
                f"{alive} are still alive. "
                f"Creator Trust Score: {trust}/100. "
                f"{score.get('recommendation', 'Do your own research.')}"
            )

    def _build_analysis_context(self, analysis: Dict[str, Any]) -> str:
        """Build context string from analysis results"""
        context_parts = []

        # Contract details
        context_parts.append(f"Contract Address: {analysis.get('contract_address', 'Unknown')}")
        context_parts.append(f"Blockchain: {analysis.get('blockchain', 'Unknown')}")

        # Scores
        scores = analysis.get('scores', {})
        if scores:
            context_parts.append(f"\nSafety Scores:")
            context_parts.append(f"- Overall: {scores.get('overall_score', 0)}/100")
            context_parts.append(f"- Code Quality: {scores.get('code_quality_score', 0)}/25")
            context_parts.append(f"- Security: {scores.get('security_score', 0)}/40")
            context_parts.append(f"- Tokenomics: {scores.get('tokenomics_score', 0)}/20")
            context_parts.append(f"- Liquidity: {scores.get('liquidity_score', 0)}/15")
            context_parts.append(f"- Risk Level: {scores.get('risk_level', 'unknown')}")

        # Vulnerabilities
        vulnerabilities = analysis.get('vulnerabilities', [])
        if vulnerabilities:
            context_parts.append(f"\nVulnerabilities Found ({len(vulnerabilities)}):")
            for vuln in vulnerabilities[:10]:  # Limit to top 10
                context_parts.append(
                    f"- [{vuln.get('severity', 'unknown').upper()}] {vuln.get('type', 'Unknown')}: "
                    f"{vuln.get('description', 'No description')}"
                )

        # Token info
        token_info = analysis.get('token_info', {})
        if token_info:
            context_parts.append(f"\nToken Information:")
            if token_info.get('name'):
                context_parts.append(f"- Name: {token_info['name']}")
            if token_info.get('symbol'):
                context_parts.append(f"- Symbol: {token_info['symbol']}")
            if token_info.get('total_supply'):
                supply = token_info['total_supply']
                decimals = token_info.get('decimals', 18)
                readable_supply = supply / (10 ** decimals)
                context_parts.append(f"- Total Supply: {readable_supply:,.0f}")

        # Tokenomics
        tokenomics = analysis.get('tokenomics', {})
        if tokenomics:
            context_parts.append(f"\nTokenomics:")
            fees = tokenomics.get('fees', {})
            if fees.get('buy_fee') is not None:
                context_parts.append(f"- Buy Fee: {fees['buy_fee'] / 100}%")
            if fees.get('sell_fee') is not None:
                context_parts.append(f"- Sell Fee: {fees['sell_fee'] / 100}%")

            if tokenomics.get('red_flags'):
                context_parts.append(f"\nTokenomics Red Flags:")
                for flag in tokenomics['red_flags']:
                    context_parts.append(f"- {flag}")

        # Priority issues
        priority_issues = analysis.get('priority_issues', [])
        if priority_issues:
            context_parts.append(f"\nPriority Issues:")
            for issue in priority_issues[:5]:  # Top 5
                context_parts.append(
                    f"- [{issue.get('severity', 'unknown').upper()}] {issue.get('issue', 'Unknown')}"
                )

        # Creator info (if available from quick check)
        creator_info = analysis.get('creator_info', {})
        if creator_info:
            context_parts.append(f"\nCreator Information:")
            context_parts.append(f"- Deployer: {creator_info.get('deployer_address', 'Unknown')}")
            context_parts.append(f"- Wallet Age: {creator_info.get('wallet_age_days', '?')} days")
            context_parts.append(f"- Transactions: {creator_info.get('transaction_count', '?')}")
            if creator_info.get('is_new_wallet'):
                context_parts.append(f"- WARNING: Brand new wallet")

        return "\n".join(context_parts)

    def _generate_fallback_response(self, analysis: Dict[str, Any]) -> str:
        """Generate fallback response if Claude API fails"""
        scores = analysis.get('scores', {})
        overall_score = scores.get('overall_score', 0)
        risk_level = scores.get('risk_level', 'unknown')

        response = f"""I've read this contract. Here's what I see.

**Safety Score: {overall_score}/100** — Risk Level: **{risk_level.upper()}**

"""

        vulnerabilities = analysis.get('vulnerabilities', [])
        if vulnerabilities:
            response += f"**Concerns I found** ({len(vulnerabilities)}):\n"
            for vuln in vulnerabilities[:5]:
                response += f"• {vuln.get('description', 'Unknown issue')}\n"

        priority_issues = analysis.get('priority_issues', [])
        if priority_issues:
            response += f"\n**What concerns me most:**\n"
            for issue in priority_issues[:3]:
                response += f"• {issue.get('issue', 'Unknown')}\n"

        response += f"\n**My read:** {scores.get('recommendation', 'Tread carefully. Do your own research before you move.')}"
        response += "\n\nThe chain doesn't lie — but it doesn't explain itself either. Always DYOR."

        return response

    def get_greeting(self) -> str:
        """Get Nanette's greeting message"""
        return """I am Nanette. I am a RIN — an ancient guardian of the $RIN community.

I read smart contracts and trace the wallets behind them. I see what hides in the code, and I'll teach you to see it too.

Send me a contract address and I'll tell you what's really in it. Ask me anything about the market, the chains, the projects. Or just talk to me.

Type `/help` to see my full range. I'm always watching."""

    def get_help_message(self) -> str:
        """Get help message"""
        return """**Nanette** — Guardian of $RIN

**Analysis & Security**
`/analyze <address>` — I'll read the contract and tell you what's hiding in it
`/trace <address>` — I trace the creator wallet and check their track record
`/interactions <address>` — I trace where the money flows and map the connections
`/price <token>` — Current price data
`/gas` — Ethereum gas prices
`/info <token>` — Deep dive on a project
`/trending` — What's moving right now
`/ca <address>` — Quick contract lookup

**Knowledge**
`/rintintin` — The legacy of my bloodline and the $RIN project

**Community**
`/meme` `/joke` `/tip` `/fact` `/quote` `/fortune`
`/8ball` `/flip` `/roll` `/paw` `/bork`

**Chains I Watch:**
Ethereum · BSC · Polygon · Arbitrum · Base · Optimism

Or skip the commands entirely — just talk to me. Ask me anything. I'm always watching the chain."""
