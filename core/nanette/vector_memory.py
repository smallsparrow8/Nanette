"""
Vector Memory for Nanette
Uses Pinecone for semantic search over chat history.
Messages are embedded and stored in real-time as they arrive.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from shared.config import settings


class VectorMemory:
    """Pinecone-backed semantic memory for Nanette"""

    def __init__(self):
        self._pc = None
        self._index = None
        self._openai = None
        self._ready = False
        self._init_error = None

    def initialize(self) -> bool:
        """Initialize Pinecone connection. Returns True if ready."""
        if self._ready:
            return True

        if not settings.pinecone_api_key:
            self._init_error = "PINECONE_API_KEY not set"
            print(f"[VectorMemory] {self._init_error}")
            return False

        if not settings.openai_api_key:
            self._init_error = "OPENAI_API_KEY not set (needed for embeddings)"
            print(f"[VectorMemory] {self._init_error}")
            return False

        try:
            from pinecone import Pinecone
        except ImportError as e:
            self._init_error = f"Cannot import pinecone: {e}"
            print(f"[VectorMemory] {self._init_error}")
            return False

        try:
            from openai import OpenAI

            self._pc = Pinecone(api_key=settings.pinecone_api_key)
            self._openai = OpenAI(api_key=settings.openai_api_key)

            index_name = settings.pinecone_index_name

            # Check if index exists, create if not
            existing = [
                idx.name for idx in self._pc.list_indexes()
            ]
            if index_name not in existing:
                from pinecone import ServerlessSpec
                self._pc.create_index(
                    name=index_name,
                    dimension=1536,  # text-embedding-3-small
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=settings.pinecone_environment
                    )
                )
                print(
                    f"[VectorMemory] Created index: {index_name}"
                )

            self._index = self._pc.Index(index_name)
            self._ready = True
            stats = self._index.describe_index_stats()
            total = getattr(stats, 'total_vector_count', 0)
            print(
                f"[VectorMemory] Connected to Pinecone. "
                f"{total} vectors stored."
            )
            return True

        except Exception as e:
            self._init_error = str(e)
            print(f"[VectorMemory] Init error: {e}")
            return False

    @property
    def is_ready(self) -> bool:
        return self._ready

    def _embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI text-embedding-3-small"""
        response = self._openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        response = self._openai.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]

    def store_message(
        self, message_id: str, text: str,
        chat_id: str, user_id: Optional[str] = None,
        username: Optional[str] = None,
        chat_title: Optional[str] = None,
        is_group: bool = False,
        timestamp: Optional[str] = None,
        platform: str = 'telegram'
    ):
        """
        Embed and store a message in Pinecone.
        Called in real-time as messages flow through.
        """
        if not self._ready:
            return

        # Skip very short messages
        if not text or len(text.strip()) < 5:
            return

        try:
            embedding = self._embed(text)

            metadata = {
                'text': text[:1000],  # Pinecone metadata limit
                'chat_id': str(chat_id),
                'user_id': str(user_id) if user_id else '',
                'username': username or '',
                'chat_title': chat_title or '',
                'is_group': is_group,
                'platform': platform,
                'timestamp': timestamp or datetime.utcnow().isoformat(),
            }

            # Use a composite ID to avoid duplicates
            vec_id = f"{platform}_{chat_id}_{message_id}"

            self._index.upsert(
                vectors=[(vec_id, embedding, metadata)]
            )

        except Exception as e:
            print(f"[VectorMemory] Store error: {e}")

    def query(
        self, query_text: str, top_k: int = 5,
        chat_id: Optional[str] = None,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant messages.
        Returns list of matching messages with scores.
        """
        if not self._ready:
            return []

        try:
            embedding = self._embed(query_text)

            # Build filter
            filter_dict = {}
            if chat_id:
                filter_dict['chat_id'] = str(chat_id)

            results = self._index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )

            matches = []
            for match in getattr(results, 'matches', []):
                score = getattr(match, 'score', 0)
                if score >= min_score:
                    meta = getattr(match, 'metadata', {}) or {}
                    matches.append({
                        'text': meta.get('text', ''),
                        'username': meta.get('username', ''),
                        'chat_title': meta.get('chat_title', ''),
                        'timestamp': meta.get('timestamp', ''),
                        'score': score,
                        'is_group': meta.get('is_group', False),
                    })

            return matches

        except Exception as e:
            print(f"[VectorMemory] Query error: {e}")
            return []

    def get_context_for_query(
        self, query: str, top_k: int = 5,
        chat_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get formatted context string for Nanette's prompt.
        Searches across all stored history.
        """
        matches = self.query(
            query, top_k=top_k, chat_id=chat_id
        )

        if not matches:
            return None

        parts = []
        for m in matches:
            who = m.get('username', 'Someone')
            where = m.get('chat_title', '')
            text = m.get('text', '')
            ts = m.get('timestamp', '')[:10]  # Just date

            if where:
                parts.append(f"[{where}, {ts}] {who}: {text}")
            else:
                parts.append(f"[{ts}] {who}: {text}")

        return "\n".join(parts)

    def bulk_import(
        self, messages: List[Dict[str, Any]],
        batch_size: int = 100,
        source_label: str = "import"
    ) -> int:
        """
        Bulk import messages into Pinecone.
        Used for initial data loading.

        Each message dict should have:
        - id: unique identifier
        - text: message text
        - chat_id: chat identifier
        - username: sender name (optional)
        - timestamp: ISO timestamp (optional)
        """
        if not self._ready:
            print("[VectorMemory] Not ready for bulk import")
            return 0

        imported = 0
        embed_batch_size = 256  # OpenAI batch limit for embeddings

        # Process in chunks for batched embedding
        eligible = []
        for msg in messages:
            text = msg.get('text', '')
            if text and len(text.strip()) >= 5:
                eligible.append(msg)

        total = len(eligible)
        print(f"[VectorMemory] Starting import: {total} messages")

        for i in range(0, total, embed_batch_size):
            chunk = eligible[i:i + embed_batch_size]
            texts = [m['text'][:1000] for m in chunk]

            try:
                embeddings = self._embed_batch(texts)

                vectors = []
                for j, (msg, emb) in enumerate(zip(chunk, embeddings)):
                    vec_id = f"{source_label}_{msg.get('id', i + j)}"
                    metadata = {
                        'text': msg['text'][:1000],
                        'chat_id': str(msg.get('chat_id', '')),
                        'username': msg.get('username', ''),
                        'chat_title': msg.get('chat_title', ''),
                        'is_group': True,
                        'platform': 'telegram',
                        'timestamp': msg.get('timestamp', ''),
                    }
                    vectors.append((vec_id, emb, metadata))

                # Upsert in Pinecone batches
                for k in range(0, len(vectors), batch_size):
                    pine_batch = vectors[k:k + batch_size]
                    self._index.upsert(vectors=pine_batch)

                imported += len(vectors)
                print(
                    f"[VectorMemory] Imported {imported}/{total} "
                    f"messages..."
                )

            except Exception as e:
                print(f"[VectorMemory] Batch import error at {i}: {e}")
                continue

        print(f"[VectorMemory] Import complete: {imported} messages")
        return imported
