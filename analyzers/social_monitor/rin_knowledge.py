"""
RIN Knowledge Base — Dynamic lore repository for clue detection.
Seeds from data/rin_lore.json and learns from community discoveries.
Never fabricates. Only shares what it knows with confidence.
"""
import json
import os
from typing import Dict, Any, List, Optional


# Resolve path to seed data relative to project root
_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)
    ))),
    'data'
)
_SEED_FILE = os.path.join(_DATA_DIR, 'rin_lore.json')


class RINKnowledgeBase:
    """
    Dynamic knowledge base for RIN lore and clue detection.

    Loads seed data on init. Can absorb confirmed discoveries
    from the community over time. Never invents facts.
    """

    def __init__(self):
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[str, List[str]] = {}
        self._thematic_keywords: Dict[str, List[str]] = {}
        self._load_seed_data()

    def _load_seed_data(self):
        """Load initial knowledge from rin_lore.json."""
        if not os.path.exists(_SEED_FILE):
            print(f"Warning: Seed file not found at {_SEED_FILE}")
            return

        with open(_SEED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Load thematic keywords
        self._thematic_keywords = data.get(
            'thematic_keywords', {}
        )

        # Load categorized entries
        categories = data.get('categories', {})
        for cat_name, cat_data in categories.items():
            self._categories[cat_name] = []
            for entry in cat_data.get('entries', []):
                entry_id = entry['id']
                self._entries[entry_id] = {
                    'text': entry['text'],
                    'source': entry.get('source', 'unknown'),
                    'category': cat_name,
                    'can_share': entry.get('can_share', True),
                    'is_spoiler': entry.get('is_spoiler', False),
                }
                self._categories[cat_name].append(entry_id)

        print(
            f"RIN Knowledge Base loaded: "
            f"{len(self._entries)} entries across "
            f"{len(self._categories)} categories"
        )

    def query(self, text: str) -> List[Dict[str, Any]]:
        """
        Find knowledge entries relevant to the given text.

        Args:
            text: Text to search against

        Returns:
            List of matching entries sorted by relevance
        """
        if not text:
            return []

        text_lower = text.lower()
        matches = []

        for entry_id, entry in self._entries.items():
            # Score based on keyword overlap
            entry_words = set(entry['text'].lower().split())
            text_words = set(text_lower.split())
            overlap = entry_words & text_words

            # Check thematic keyword matches
            theme_score = 0
            matched_themes = []
            for theme, keywords in self._thematic_keywords.items():
                for kw in keywords:
                    if kw in text_lower:
                        theme_score += 1
                        if theme not in matched_themes:
                            matched_themes.append(theme)

            total_score = len(overlap) + theme_score
            if total_score > 0:
                matches.append({
                    'id': entry_id,
                    'text': entry['text'],
                    'category': entry['category'],
                    'source': entry['source'],
                    'can_share': entry['can_share'],
                    'is_spoiler': entry['is_spoiler'],
                    'relevance_score': total_score,
                    'matched_themes': matched_themes,
                })

        matches.sort(key=lambda m: m['relevance_score'], reverse=True)
        return matches

    def get_thematic_matches(
        self, text: str
    ) -> Dict[str, List[str]]:
        """
        Identify which RIN themes are present in the text.

        Returns:
            Dict of theme_name -> list of matched keywords
        """
        if not text:
            return {}

        text_lower = text.lower()
        results = {}

        for theme, keywords in self._thematic_keywords.items():
            matched = [kw for kw in keywords if kw in text_lower]
            if matched:
                results[theme] = matched

        return results

    def get_by_category(
        self, category: str, shareable_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all entries in a category."""
        entry_ids = self._categories.get(category, [])
        results = []
        for eid in entry_ids:
            entry = self._entries.get(eid)
            if entry:
                if shareable_only and not entry['can_share']:
                    continue
                results.append({
                    'id': eid,
                    **entry
                })
        return results

    def is_safe_to_share(self, entry_id: str) -> bool:
        """Check if an entry is safe to share without spoiling."""
        entry = self._entries.get(entry_id)
        if not entry:
            return False
        return entry['can_share'] and not entry['is_spoiler']

    def learn_from_discovery(
        self, text: str, context: str,
        category: str = 'discovered_clues',
        source: str = 'community_discovery'
    ) -> str:
        """
        Absorb a confirmed discovery into the knowledge base.

        Args:
            text: The discovered fact/clue
            context: Where/how it was discovered
            category: Category to file it under
            source: Source attribution

        Returns:
            The entry ID of the new knowledge
        """
        # Generate ID
        existing_count = len([
            eid for eid in self._entries
            if eid.startswith(f'{category}_')
        ])
        entry_id = f"{category}_{existing_count + 1:03d}"

        self._entries[entry_id] = {
            'text': text,
            'source': source,
            'category': category,
            'can_share': True,
            'is_spoiler': False,
            'context': context,
        }

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(entry_id)

        return entry_id

    def get_all_themes(self) -> List[str]:
        """Get list of all known theme names."""
        return list(self._thematic_keywords.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            'total_entries': len(self._entries),
            'categories': {
                cat: len(ids)
                for cat, ids in self._categories.items()
            },
            'themes': list(self._thematic_keywords.keys()),
            'shareable_entries': sum(
                1 for e in self._entries.values()
                if e['can_share']
            ),
        }
