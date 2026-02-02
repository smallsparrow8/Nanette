"""
Channel Analyzer — Processes messages from Telegram groups,
detects crypto-relevant topics, and decides when Nanette
should respond. Optionally runs RIN clue detection on admin
messages when enabled.
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .clue_detector import ClueDetector


# Crypto-relevant keyword patterns
CRYPTO_KEYWORDS = {
    'contract', 'token', 'swap', 'liquidity', 'pool',
    'dex', 'defi', 'nft', 'mint', 'burn', 'airdrop',
    'staking', 'yield', 'farm', 'rug', 'rugpull', 'scam',
    'honeypot', 'audit', 'whale', 'pump', 'dump',
    'bullish', 'bearish', 'moon', 'dip', 'hodl',
    'blockchain', 'ethereum', 'solana', 'bitcoin',
    'uniswap', 'pancakeswap', 'sushiswap',
    'metamask', 'wallet', 'gas', 'gwei',
    'market cap', 'mcap', 'volume', 'chart',
    'buy', 'sell', 'trade', 'exchange',
    'ath', 'atl', 'roi', 'apr', 'apy',
    'whitepaper', 'roadmap', 'utility',
}

# Patterns that detect contract addresses and token mentions
ADDRESS_PATTERN = re.compile(r'0x[a-fA-F0-9]{40}')
TOKEN_MENTION_PATTERN = re.compile(r'\$[A-Za-z]{2,10}')
PRICE_PATTERN = re.compile(
    r'(?:price|worth|cost|value)\s+(?:of\s+)?'
    r'(?:\$?[A-Za-z]{2,10})',
    re.IGNORECASE
)


class ChannelAnalyzer:
    """Analyzes messages from group chats for crypto relevance
    and determines when Nanette should respond."""

    def __init__(self):
        # In-memory cooldown tracking per chat
        # chat_id -> last_response_time
        self._last_response: Dict[str, datetime] = {}
        # Clue-specific cooldown (longer — 10 min)
        self._last_clue_response: Dict[str, datetime] = {}
        # Recent message context per chat
        # chat_id -> list of recent message dicts
        self._chat_context: Dict[str, List[Dict]] = {}
        self._max_context = 50
        # Clue detector (Phase 3)
        self.clue_detector = ClueDetector()

    def process_message(
        self, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an incoming group message.

        Args:
            message_data: Dict with keys:
                chat_id, chat_title, chat_type,
                message_id, user_id, username,
                is_admin, text, timestamp

        Returns:
            Dict with:
                stored: bool
                is_crypto_relevant: bool
                detected_topics: list
                detected_addresses: list
                should_respond: bool
                suggested_context: str (if should_respond)
        """
        text = message_data.get('text', '')
        chat_id = str(message_data.get('chat_id', ''))

        # Analyze crypto relevance
        relevance = self._analyze_relevance(text)

        # Store in context buffer
        self._add_to_context(chat_id, message_data)

        # Determine if Nanette should respond
        should_respond = False
        suggested_context = ''

        if relevance['is_crypto_relevant']:
            should_respond = self._should_respond(
                chat_id, message_data, relevance
            )

        if should_respond:
            suggested_context = self._build_response_context(
                chat_id, message_data, relevance
            )

        # Phase 3: Clue detection for admin messages
        clue_result = None
        if (message_data.get('is_admin')
                and message_data.get('rin_clue_detection')):
            clue_result = self.clue_detector.analyze_admin_message(
                message_data,
                chat_context=self._chat_context.get(chat_id, [])
            )
            # If clue detected and cooldown passed, respond
            if (clue_result.get('has_potential_clue')
                    and not should_respond):
                clue_cooldown = self._check_clue_cooldown(
                    chat_id, cooldown_seconds=600
                )
                if clue_cooldown:
                    should_respond = True
                    suggested_context = (
                        clue_result.get('suggested_response', '')
                    )

        return {
            'stored': True,
            'is_crypto_relevant': relevance['is_crypto_relevant'],
            'detected_topics': relevance['topics'],
            'detected_addresses': relevance['addresses'],
            'detected_tokens': relevance['tokens'],
            'should_respond': should_respond,
            'suggested_context': suggested_context,
            'clue_detection': clue_result,
        }

    def _analyze_relevance(
        self, text: str
    ) -> Dict[str, Any]:
        """Analyze text for crypto relevance."""
        if not text:
            return {
                'is_crypto_relevant': False,
                'topics': [],
                'addresses': [],
                'tokens': [],
                'keyword_count': 0,
            }

        text_lower = text.lower()

        # Find matching keywords
        topics = []
        for keyword in CRYPTO_KEYWORDS:
            if keyword in text_lower:
                topics.append(keyword)

        # Find contract addresses
        addresses = ADDRESS_PATTERN.findall(text)

        # Find token mentions ($XXX)
        tokens = TOKEN_MENTION_PATTERN.findall(text)

        # Check for price queries
        if PRICE_PATTERN.search(text):
            topics.append('price_query')

        # A message is crypto-relevant if it has 2+ keywords,
        # any address, any token mention, or a price query
        is_relevant = (
            len(topics) >= 2
            or len(addresses) > 0
            or len(tokens) > 0
            or 'price_query' in topics
        )

        return {
            'is_crypto_relevant': is_relevant,
            'topics': topics,
            'addresses': addresses,
            'tokens': tokens,
            'keyword_count': len(topics),
        }

    def _should_respond(
        self, chat_id: str,
        message_data: Dict[str, Any],
        relevance: Dict[str, Any]
    ) -> bool:
        """
        Decide if Nanette should respond to this message.
        Respects cooldown, relevance threshold, and direct
        triggers.
        """
        # Always respond if a contract address is posted
        if relevance['addresses']:
            return self._check_cooldown(chat_id, cooldown_seconds=60)

        # Respond to high-relevance messages (3+ keywords)
        if relevance['keyword_count'] >= 3:
            return self._check_cooldown(chat_id, cooldown_seconds=300)

        # Respond to token mentions with context
        if relevance['tokens'] and relevance['keyword_count'] >= 1:
            return self._check_cooldown(chat_id, cooldown_seconds=300)

        # Price queries
        if 'price_query' in relevance.get('topics', []):
            return self._check_cooldown(chat_id, cooldown_seconds=120)

        return False

    def _check_cooldown(
        self, chat_id: str,
        cooldown_seconds: int = 300
    ) -> bool:
        """Check if enough time has passed since last response."""
        last = self._last_response.get(chat_id)
        now = datetime.utcnow()

        if last and (now - last).total_seconds() < cooldown_seconds:
            return False

        # Mark as responded
        self._last_response[chat_id] = now
        return True

    def _check_clue_cooldown(
        self, chat_id: str,
        cooldown_seconds: int = 600
    ) -> bool:
        """Check clue-specific cooldown (longer than normal)."""
        last = self._last_clue_response.get(chat_id)
        now = datetime.utcnow()

        if last and (now - last).total_seconds() < cooldown_seconds:
            return False

        self._last_clue_response[chat_id] = now
        return True

    def _add_to_context(
        self, chat_id: str,
        message_data: Dict[str, Any]
    ):
        """Add message to the rolling context buffer."""
        if chat_id not in self._chat_context:
            self._chat_context[chat_id] = []

        self._chat_context[chat_id].append({
            'user': message_data.get('username', 'Unknown'),
            'text': message_data.get('text', ''),
            'is_admin': message_data.get('is_admin', False),
            'timestamp': message_data.get('timestamp', ''),
        })

        # Trim to max context
        if len(self._chat_context[chat_id]) > self._max_context:
            self._chat_context[chat_id] = \
                self._chat_context[chat_id][-self._max_context:]

    def _build_response_context(
        self, chat_id: str,
        message_data: Dict[str, Any],
        relevance: Dict[str, Any]
    ) -> str:
        """Build context string for Nanette's response."""
        parts = []

        # Current message
        user = message_data.get('username', 'Someone')
        text = message_data.get('text', '')
        parts.append(f"Message from {user}: \"{text}\"")

        # Topics detected
        if relevance['topics']:
            parts.append(
                f"Topics: {', '.join(relevance['topics'])}"
            )

        # Addresses found
        if relevance['addresses']:
            parts.append(
                f"Contract addresses mentioned: "
                f"{', '.join(relevance['addresses'][:3])}"
            )

        # Token mentions
        if relevance['tokens']:
            parts.append(
                f"Tokens mentioned: "
                f"{', '.join(relevance['tokens'][:5])}"
            )

        # Recent context (last 5 messages)
        recent = self._chat_context.get(chat_id, [])[-6:-1]
        if recent:
            context_lines = []
            for msg in recent:
                who = msg['user']
                what = msg['text'][:100]
                context_lines.append(f"  {who}: {what}")
            parts.append(
                "Recent conversation:\n" +
                "\n".join(context_lines)
            )

        return "\n\n".join(parts)

    def get_chat_summary(
        self, chat_id: str
    ) -> Dict[str, Any]:
        """Get a summary of recent activity in a chat."""
        messages = self._chat_context.get(chat_id, [])

        if not messages:
            return {
                'message_count': 0,
                'summary': 'No recent messages tracked.'
            }

        # Count topics across recent messages
        all_topics = []
        all_addresses = []
        all_tokens = []
        admin_messages = 0

        for msg in messages:
            rel = self._analyze_relevance(msg.get('text', ''))
            all_topics.extend(rel['topics'])
            all_addresses.extend(rel['addresses'])
            all_tokens.extend(rel['tokens'])
            if msg.get('is_admin'):
                admin_messages += 1

        # Count unique topics
        from collections import Counter
        topic_counts = Counter(all_topics)
        top_topics = topic_counts.most_common(5)

        return {
            'message_count': len(messages),
            'crypto_relevant': sum(
                1 for m in messages
                if self._analyze_relevance(
                    m.get('text', '')
                )['is_crypto_relevant']
            ),
            'admin_messages': admin_messages,
            'top_topics': [
                {'topic': t, 'count': c}
                for t, c in top_topics
            ],
            'addresses_mentioned': list(set(all_addresses)),
            'tokens_mentioned': list(set(all_tokens)),
        }
