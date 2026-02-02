"""
Clue Detector — Analyzes admin messages for potential RIN clues.
Never fabricates. Expresses curiosity, not certainty.
Only triggers at confidence > 0.7.
"""
import re
from typing import Dict, Any, List, Optional

from .rin_knowledge import RINKnowledgeBase


# Riddle/puzzle structural patterns
RIDDLE_PATTERNS = [
    # Questions that feel deliberate
    re.compile(
        r'(?:what|where|who|when|why|how)\s+.{10,}\?',
        re.IGNORECASE
    ),
    # Ellipsis usage (trailing thought)
    re.compile(r'\.{3}'),
    # Cryptic phrasing
    re.compile(
        r'(?:listen|look|watch|remember|seek|find|follow)'
        r'\s+(?:closely|carefully|deeper|within|beneath)',
        re.IGNORECASE
    ),
    # Encoded/number patterns
    re.compile(r'\b\d{2,}\s+\d{2,}\s+\d{2,}\b'),
    # Binary strings
    re.compile(r'[01]{8,}'),
    # Deliberate capitalization patterns (3+ consecutive caps words)
    re.compile(r'(?:[A-Z]{2,}\s+){2,}[A-Z]{2,}'),
    # Counting/sequence language
    re.compile(
        r'(?:first|second|third|fourth|fifth|next|then|finally)',
        re.IGNORECASE
    ),
]

# Poetic/mystical language indicators
MYSTICAL_PHRASES = [
    'the trail', 'the path', 'the way',
    'something stirs', 'awakens', 'the spirit',
    'between the lines', 'hidden', 'beneath',
    'the moon', 'the howl', 'the hunt',
    'the pack gathers', 'the den', 'the blood',
    'runs deep', 'old as', 'ancient',
    'the veil', 'beyond', 'the shadow',
    'nine tails', 'kitsune', 'fox',
    'the key', 'the door', 'the gate',
    'silence speaks', 'whisper',
]


class ClueDetector:
    """
    Detects potential RIN clues in admin messages.

    Design philosophy:
    - Never fabricates lore or clues
    - Expresses curiosity, not certainty
    - Only fires at confidence > 0.7
    - Nudges toward discovery without spoiling
    """

    def __init__(self):
        self.knowledge = RINKnowledgeBase()

    def analyze_admin_message(
        self,
        message_data: Dict[str, Any],
        chat_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Perform deep analysis of an admin message for clues.

        Args:
            message_data: Dict with text, username, etc.
            chat_context: Recent messages for context

        Returns:
            Dict with:
                has_potential_clue: bool
                clue_type: str (riddle/thematic/encoded/timeline)
                confidence: float (0-1.0)
                thematic_connections: list
                matched_themes: dict
                knowledge_matches: list
                suggested_response: str
        """
        text = message_data.get('text', '')
        if not text or len(text) < 10:
            return self._no_clue()

        # Score components
        riddle_score = self._assess_riddle_structure(text)
        thematic_score, matched_themes = (
            self._detect_thematic_patterns(text)
        )
        mystical_score = self._assess_mystical_language(text)
        encoding_score = self._detect_encoding_patterns(text)
        knowledge_matches = self.knowledge.query(text)

        # Knowledge relevance bonus
        knowledge_score = min(
            len(knowledge_matches) * 0.1, 0.3
        )

        # Combined confidence (weighted)
        confidence = (
            riddle_score * 0.25
            + thematic_score * 0.30
            + mystical_score * 0.20
            + encoding_score * 0.15
            + knowledge_score * 0.10
        )

        # Determine clue type
        clue_type = self._determine_clue_type(
            riddle_score, thematic_score,
            mystical_score, encoding_score
        )

        # Build thematic connections list
        thematic_connections = []
        for theme, keywords in matched_themes.items():
            thematic_connections.append({
                'theme': theme,
                'matched_keywords': keywords,
            })

        has_clue = confidence >= 0.7

        # Build suggested response only if confident
        suggested_response = ''
        if has_clue:
            suggested_response = self._build_clue_response(
                text, clue_type, thematic_connections,
                knowledge_matches
            )

        return {
            'has_potential_clue': has_clue,
            'clue_type': clue_type if has_clue else None,
            'confidence': round(confidence, 3),
            'thematic_connections': thematic_connections,
            'matched_themes': matched_themes,
            'knowledge_matches': [
                {
                    'text': m['text'],
                    'category': m['category'],
                    'relevance': m['relevance_score'],
                }
                for m in knowledge_matches[:3]
            ],
            'suggested_response': suggested_response,
            'scores': {
                'riddle': round(riddle_score, 3),
                'thematic': round(thematic_score, 3),
                'mystical': round(mystical_score, 3),
                'encoding': round(encoding_score, 3),
                'knowledge': round(knowledge_score, 3),
            }
        }

    def _assess_riddle_structure(self, text: str) -> float:
        """Score likelihood of riddle/puzzle structure (0-1)."""
        score = 0.0
        matches = 0

        for pattern in RIDDLE_PATTERNS:
            if pattern.search(text):
                matches += 1

        # Normalize: 1 match = 0.3, 2 = 0.6, 3+ = 0.9
        if matches >= 3:
            score = 0.9
        elif matches == 2:
            score = 0.6
        elif matches == 1:
            score = 0.3

        # Boost if message is medium-length (riddles are crafted)
        word_count = len(text.split())
        if 15 <= word_count <= 100:
            score = min(score + 0.1, 1.0)

        return score

    def _detect_thematic_patterns(
        self, text: str
    ) -> tuple:
        """
        Check for RIN thematic patterns.

        Returns:
            (score: float, matched_themes: dict)
        """
        matched_themes = self.knowledge.get_thematic_matches(
            text
        )

        if not matched_themes:
            return 0.0, {}

        # Score based on number of themes and depth
        total_matches = sum(
            len(kws) for kws in matched_themes.values()
        )
        unique_themes = len(matched_themes)

        # Multiple themes hitting = stronger signal
        if unique_themes >= 3:
            score = 0.9
        elif unique_themes == 2:
            score = 0.6 + min(total_matches * 0.05, 0.2)
        elif total_matches >= 3:
            score = 0.5
        elif total_matches >= 2:
            score = 0.3
        else:
            score = 0.15

        return min(score, 1.0), matched_themes

    def _assess_mystical_language(self, text: str) -> float:
        """Score presence of mystical/poetic language."""
        text_lower = text.lower()
        matches = 0

        for phrase in MYSTICAL_PHRASES:
            if phrase in text_lower:
                matches += 1

        if matches >= 4:
            return 0.9
        elif matches >= 3:
            return 0.7
        elif matches == 2:
            return 0.5
        elif matches == 1:
            return 0.2
        return 0.0

    def _detect_encoding_patterns(self, text: str) -> float:
        """Score presence of encoded/cipher-like content."""
        score = 0.0

        # Binary strings
        if re.search(r'[01]{8,}', text):
            score += 0.5

        # Hex-like strings (not contract addresses)
        hex_matches = re.findall(
            r'(?<!\w)[0-9a-f]{8,}(?!\w)', text, re.IGNORECASE
        )
        # Filter out likely contract addresses
        non_address_hex = [
            h for h in hex_matches if len(h) != 40
        ]
        if non_address_hex:
            score += 0.3

        # Number sequences
        if re.search(r'\b\d{2,}\s+\d{2,}\s+\d{2,}\b', text):
            score += 0.3

        # Base64-like strings
        if re.search(
            r'[A-Za-z0-9+/]{20,}={0,2}', text
        ):
            score += 0.2

        return min(score, 1.0)

    def _determine_clue_type(
        self, riddle: float, thematic: float,
        mystical: float, encoding: float
    ) -> str:
        """Determine the primary clue type."""
        scores = {
            'riddle': riddle,
            'thematic_reference': thematic,
            'encoded': encoding,
            'timeline_hint': mystical,
        }
        return max(scores, key=scores.get)

    def _build_clue_response(
        self,
        text: str,
        clue_type: str,
        thematic_connections: List[Dict],
        knowledge_matches: List[Dict]
    ) -> str:
        """
        Build Nanette's response to a potential clue.
        Curious, not certain. Nudges, doesn't spoil.
        """
        parts = []

        if clue_type == 'riddle':
            parts.append(
                "Something in those words feels deliberate... "
                "like a trail left for those paying attention."
            )
        elif clue_type == 'encoded':
            parts.append(
                "I sense patterns in there. Something encoded, "
                "maybe. The kind of thing that rewards a closer look."
            )
        elif clue_type == 'thematic_reference':
            themes = [tc['theme'] for tc in thematic_connections]
            theme_str = ', '.join(themes[:3])
            parts.append(
                f"The echoes of familiar themes... "
                f"{theme_str}. "
                f"This feels connected to something deeper."
            )
        elif clue_type == 'timeline_hint':
            parts.append(
                "There's a mystical weight to these words. "
                "Something stirs in the old stories."
            )

        # Add knowledge connection if relevant
        if knowledge_matches:
            best = knowledge_matches[0]
            if best.get('can_share', True):
                parts.append(
                    "The trail is warm here. What do you see?"
                )

        return ' '.join(parts)

    def _no_clue(self) -> Dict[str, Any]:
        """Return empty result for non-clue messages."""
        return {
            'has_potential_clue': False,
            'clue_type': None,
            'confidence': 0.0,
            'thematic_connections': [],
            'matched_themes': {},
            'knowledge_matches': [],
            'suggested_response': '',
            'scores': {
                'riddle': 0.0,
                'thematic': 0.0,
                'mystical': 0.0,
                'encoding': 0.0,
                'knowledge': 0.0,
            }
        }
