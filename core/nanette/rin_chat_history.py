"""
RIN Chat History Parser and Knowledge Base

Parses Telegram chat export HTML files and provides searchable knowledge
for Nanette about the RinTinTin community history.
"""
import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


@dataclass
class ChatMessage:
    """Represents a single chat message"""
    message_id: str
    sender: str
    timestamp: str
    text: str
    media_type: Optional[str] = None
    media_path: Optional[str] = None
    is_service_message: bool = False


def parse_single_file(html_path: str) -> List[ChatMessage]:
    """Parse a single HTML file and extract messages"""
    if BeautifulSoup is None:
        print("BeautifulSoup not installed. Run: pip install beautifulsoup4")
        return []

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    messages = []
    last_sender = None

    # Find all message divs
    for msg_div in soup.find_all('div', class_='message'):
        classes = msg_div.get('class', [])
        msg_id = msg_div.get('id', '')

        # Service messages (date separators, etc.)
        if 'service' in classes:
            body = msg_div.find('div', class_='body')
            if body:
                text = body.get_text(strip=True)
                messages.append(ChatMessage(
                    message_id=msg_id,
                    sender='',
                    timestamp='',
                    text=text,
                    is_service_message=True
                ))
            continue

        # Regular messages
        if 'default' not in classes:
            continue

        # Get sender
        from_name_div = msg_div.find('div', class_='from_name')
        if from_name_div:
            sender = from_name_div.get_text(strip=True)
            last_sender = sender
        elif 'joined' in classes and last_sender:
            sender = last_sender
        else:
            sender = 'Unknown'

        # Get timestamp
        date_div = msg_div.find('div', class_='date')
        timestamp = ''
        if date_div and date_div.get('title'):
            timestamp = date_div.get('title')

        # Get text content
        text_div = msg_div.find('div', class_='text')
        text = ''
        if text_div:
            text = text_div.get_text(separator=' ', strip=True)

        # Get media
        media_type = None
        media_path = None
        media_wrap = msg_div.find('div', class_='media_wrap')
        if media_wrap:
            link = media_wrap.find('a', href=True)
            if link:
                href = link.get('href', '')
                media_path = href
                if 'photos/' in href:
                    media_type = 'photo'
                elif 'video_files/' in href:
                    media_type = 'video'
                elif 'animations/' in href:
                    media_type = 'animation'
                elif 'voice_messages/' in href:
                    media_type = 'voice'
                elif 'stickers/' in href:
                    media_type = 'sticker'
                elif 'round_video_messages/' in href:
                    media_type = 'video_note'
                elif 'files/' in href:
                    media_type = 'document'

        messages.append(ChatMessage(
            message_id=msg_id,
            sender=sender,
            timestamp=timestamp,
            text=text,
            media_type=media_type,
            media_path=media_path,
            is_service_message=False
        ))

    return messages


def parse_chat_export(export_dir: str) -> List[ChatMessage]:
    """Parse all HTML files in the Telegram chat export directory."""
    export_path = Path(export_dir)
    all_messages: List[ChatMessage] = []

    # Find all message HTML files
    html_files = []
    for f in export_path.iterdir():
        if f.name.startswith('messages') and f.suffix == '.html':
            html_files.append(f)

    # Sort files by number
    def get_file_number(f):
        name = f.stem
        if name == 'messages':
            return 1
        else:
            num = name.replace('messages', '')
            return int(num) if num.isdigit() else 999

    html_files.sort(key=get_file_number)
    print(f"Found {len(html_files)} HTML files to parse...")

    for i, html_file in enumerate(html_files):
        try:
            file_messages = parse_single_file(str(html_file))
            all_messages.extend(file_messages)
            if (i + 1) % 25 == 0:
                print(f"  Parsed {i + 1}/{len(html_files)} files ({len(all_messages)} messages so far)")
        except Exception as e:
            print(f"Error parsing {html_file}: {e}")

    print(f"Parsed {len(all_messages)} total messages")
    return all_messages


def build_knowledge_base(messages: List[ChatMessage], output_path: str) -> Dict[str, Any]:
    """Build a searchable knowledge base from parsed messages."""
    # Patterns that indicate bot spam
    bot_spam_patterns = [
        r'Buy!\s',
        r'Sell!\s',
        r'Spent:.*Got:',
        r'MCap:.*\$',
        r'Holder Count:',
        r'🦊🦊🦊',
    ]

    meaningful_messages = []
    senders: Dict[str, int] = {}
    media_messages = []

    for msg in messages:
        if msg.is_service_message:
            continue

        # Skip bot spam
        is_bot_spam = any(re.search(p, msg.text) for p in bot_spam_patterns if msg.text)
        if is_bot_spam:
            continue

        # Track sender activity
        if msg.sender and msg.sender not in ['Unknown', '']:
            senders[msg.sender] = senders.get(msg.sender, 0) + 1

        # Track media
        if msg.media_path:
            media_messages.append({
                'sender': msg.sender,
                'timestamp': msg.timestamp,
                'media_type': msg.media_type,
                'media_path': msg.media_path,
                'caption': msg.text[:500] if msg.text else ''
            })

        # Keep messages with actual content
        if msg.text and len(msg.text.strip()) > 3:
            meaningful_messages.append({
                'id': msg.message_id,
                'sender': msg.sender,
                'timestamp': msg.timestamp,
                'text': msg.text[:2000],
                'media_type': msg.media_type,
                'media_path': msg.media_path
            })

    # Sort senders by activity
    top_members = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:100]

    knowledge_base = {
        'metadata': {
            'source': 'RinTinTin Official Telegram',
            'total_messages': len(messages),
            'meaningful_messages': len(meaningful_messages),
            'media_count': len(media_messages),
            'parsed_at': datetime.now().isoformat()
        },
        'top_members': dict(top_members),
        'messages': meaningful_messages,
        'media': media_messages
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False)

    print(f"Knowledge base saved to {output_path}")
    print(f"  - {len(meaningful_messages)} meaningful messages")
    print(f"  - {len(media_messages)} media items")
    print(f"  - {len(top_members)} active members tracked")

    return knowledge_base


class RINHistorySearch:
    """Searchable interface to RIN chat history for Nanette."""

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
            print(f"Loaded RIN history: {len(self.messages)} messages, {len(self.media)} media items")
        except Exception as e:
            print(f"Error loading RIN history: {e}")

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

        context_parts = [f"[Historical RIN chat context for '{query}':]"]
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

        parts = [f"[{username}'s past messages in RIN chat:]"]
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
_history_instance: Optional[RINHistorySearch] = None


def get_rin_history() -> Optional[RINHistorySearch]:
    """Get the global RIN history instance"""
    global _history_instance
    return _history_instance


def initialize_rin_history(knowledge_base_path: str) -> bool:
    """Initialize the global RIN history instance"""
    global _history_instance
    if os.path.exists(knowledge_base_path):
        _history_instance = RINHistorySearch(knowledge_base_path)
        return _history_instance.is_loaded
    return False


if __name__ == '__main__':
    import sys

    export_dir = r"C:\Users\small\Downloads\Telegram Desktop\ChatExport_2026-01-31"
    output_path = os.path.join(os.path.dirname(__file__), 'rin_knowledge_base.json')

    if BeautifulSoup is None:
        print("BeautifulSoup is required. Installing...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'beautifulsoup4'])
        from bs4 import BeautifulSoup

    if os.path.exists(export_dir):
        print(f"Parsing chat export from: {export_dir}")
        messages = parse_chat_export(export_dir)
        if messages:
            knowledge_base = build_knowledge_base(messages, output_path)
            print("\nDone! Knowledge base ready for Nanette.")
        else:
            print("No messages found. Check the export directory.")
    else:
        print(f"Export directory not found: {export_dir}")
        sys.exit(1)
