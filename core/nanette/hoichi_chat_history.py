"""
HOICHI Chat History Knowledge Base

Provides searchable knowledge for Nanette about the HOICHI project community history.
Uses the same structure as rin_chat_history.py for consistency.
"""
import os
import json
from typing import List, Dict, Optional, Any


class HOICHIHistorySearch:
    """Searchable interface to HOICHI chat history for Nanette."""

    def __init__(self, knowledge_base_path: Optional[str] = None):
        self.knowledge_base: Dict[str, Any] = {}
        self.messages: List[Dict] = []
        self.media: List[Dict] = []
        self.top_members: Dict[str, int] = {}
        self._loaded = False

        if knowledge_base_path and os.path.exists(knowledge_base_path):
            self.load(knowledge_base_path)

    def load(self, path: str):
        """Load knowledge base from file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
            self.messages = self.knowledge_base.get('messages', [])
            self.media = self.knowledge_base.get('media', [])
            self.top_members = self.knowledge_base.get('top_members', {})
            self._loaded = True
            print(f"Loaded HOICHI history: {len(self.messages)} messages, {len(self.media)} media items")
        except Exception as e:
            print(f"Error loading HOICHI history: {e}")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def search_messages(self, query: str, limit: int = 20) -> List[Dict]:
        """Search messages for keywords"""
        if not self._loaded:
            return []
        query_lower = query.lower()
        results = []
        for msg in self.messages:
            text = msg.get('text', '')
            if query_lower in text.lower():
                results.append(msg)
                if len(results) >= limit:
                    break
        return results

    def search_by_sender(self, sender: str, limit: int = 50) -> List[Dict]:
        """Get messages from a specific sender"""
        if not self._loaded:
            return []
        sender_lower = sender.lower()
        return [
            msg for msg in self.messages
            if sender_lower in msg.get('sender', '').lower()
        ][:limit]

    def get_media_by_type(self, media_type: str) -> List[Dict]:
        """Get all media of a specific type"""
        if not self._loaded:
            return []
        return [m for m in self.media if m.get('media_type') == media_type]

    def search_media(self, query: str, limit: int = 20) -> List[Dict]:
        """Search media by caption or filename"""
        if not self._loaded:
            return []
        query_lower = query.lower()
        results = []
        for m in self.media:
            caption = m.get('caption', '').lower()
            path = m.get('media_path', '').lower()
            if query_lower in caption or query_lower in path:
                results.append(m)
                if len(results) >= limit:
                    break
        return results

    def get_context_for_query(self, query: str, max_messages: int = 10) -> str:
        """Get relevant historical context for a query."""
        if not self._loaded:
            return ""

        results = self.search_messages(query, limit=max_messages)
        if not results:
            return ""

        context_parts = [f"[Historical HOICHI chat context for '{query}':]"]
        for msg in results:
            sender = msg.get('sender', 'Unknown')
            text = msg.get('text', '')[:200]
            timestamp = msg.get('timestamp', '')[:10]
            context_parts.append(f"- {sender} ({timestamp}): {text}")

        return "\n".join(context_parts)

    def get_member_history(self, username: str, limit: int = 10) -> str:
        """Get a member's message history for context"""
        if not self._loaded:
            return ""

        messages = self.search_by_sender(username, limit=limit)
        if not messages:
            return ""

        parts = [f"[{username}'s past messages in HOICHI chat:]"]
        for msg in messages:
            text = msg.get('text', '')[:150]
            parts.append(f"- {text}")

        return "\n".join(parts)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about the chat history"""
        if not self._loaded:
            return {}

        return {
            'total_messages': len(self.messages),
            'total_media': len(self.media),
            'top_10_members': list(self.top_members.items())[:10],
            'media_breakdown': {
                'photos': len([m for m in self.media if m.get('media_type') == 'photo']),
                'videos': len([m for m in self.media if m.get('media_type') == 'video']),
                'animations': len([m for m in self.media if m.get('media_type') == 'animation']),
                'stickers': len([m for m in self.media if m.get('media_type') == 'sticker']),
                'voice': len([m for m in self.media if m.get('media_type') == 'voice']),
                'documents': len([m for m in self.media if m.get('media_type') == 'document']),
            }
        }


# Global instance for use by Nanette
_history_instance: Optional[HOICHIHistorySearch] = None


def get_hoichi_history() -> Optional[HOICHIHistorySearch]:
    """Get the global HOICHI history instance"""
    global _history_instance
    return _history_instance


def initialize_hoichi_history(knowledge_base_path: str) -> bool:
    """Initialize the global HOICHI history instance"""
    global _history_instance
    if os.path.exists(knowledge_base_path):
        _history_instance = HOICHIHistorySearch(knowledge_base_path)
        return _history_instance.is_loaded
    return False
