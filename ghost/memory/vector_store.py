"""Vector database for semantic memory storage."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False

from ghost.core.interfaces import Message

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages semantic memory using ChromaDB."""
    
    def __init__(self, persist_directory: str, embedding_model: str):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        if not VECTOR_DB_AVAILABLE:
            logger.warning("ChromaDB not available, using fallback memory")
            self._fallback_mode = True
            self._fallback_store: List[Message] = []
            return
        
        self._fallback_mode = False
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="ghost_memories",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embedding model
        self.embedder = SentenceTransformer(embedding_model)
        logger.info(f"Vector store initialized with {embedding_model}")
    
    async def add_message(self, message: Message) -> None:
        """Add message to vector store."""
        if self._fallback_mode:
            self._fallback_store.append(message)
            return
        
        try:
            # Generate embedding
            embedding = self.embedder.encode(message.content).tolist()
            
            # Prepare metadata
            metadata = {
                "role": message.role,
                **message.metadata
            }
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[message.content],
                metadatas=[metadata],
                ids=[str(uuid.uuid4())]
            )
        except Exception as e:
            logger.error(f"Failed to add to vector store: {e}", exc_info=True)
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        rerank: bool = True,
        time_weight: float = 0.3
    ) -> List[Message]:
        """Search with reranking and recency weighting."""
        if self._fallback_mode:
            results = [
                msg for msg in self._fallback_store
                if query.lower() in msg.content.lower()
            ]
            return results[:limit]
        
        try:
            query_embedding = self.embedder.encode(query).tolist()
            
            # Retrieve 3x more candidates for reranking
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit * 3
            )
            
            if not results['documents']:
                return []
            
            scored_messages = []
            for doc, metadata, distance in zip(
                results['documents'][0], 
                results['metadatas'][0],
                results['distances'][0]
            ):
                role = metadata.pop('role', 'unknown')
                
                # Calculate recency score
                timestamp = metadata.get('timestamp', '')
                recency_score = self._calculate_recency_score(timestamp)
                
                # Combined score: semantic similarity + recency
                relevance = 1 - distance  # Convert distance to similarity
                final_score = (1 - time_weight) * relevance + time_weight * recency_score
                
                scored_messages.append((
                    final_score,
                    Message(role=role, content=doc, metadata=metadata)
                ))
            
            # Sort by score and return top results
            scored_messages.sort(reverse=True, key=lambda x: x[0])
            return [msg for _, msg in scored_messages[:limit]]
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}", exc_info=True)
            return []

    def _calculate_recency_score(self, timestamp: str) -> float:
        """Calculate recency score (1.0 = now, 0.0 = very old)."""
        try:
            msg_time = datetime.fromisoformat(timestamp)
            age = (datetime.utcnow() - msg_time).total_seconds()
            
            # Exponential decay: half-life of 7 days
            half_life = 7 * 24 * 3600
            return 0.5 ** (age / half_life)
        except:
            return 0.5
    
    async def clear(self) -> None:
        """Clear all stored memories."""
        if self._fallback_mode:
            self._fallback_store.clear()
            return
        
        try:
            self.client.delete_collection("ghost_memories")
            self.collection = self.client.get_or_create_collection("ghost_memories")
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}", exc_info=True)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        if self._fallback_mode:
            return {"total_memories": len(self._fallback_store), "fallback_mode": True}
        
        try:
            count = self.collection.count()
            return {
                "total_memories": count,
                "fallback_mode": False,
                "collection_name": self.collection.name
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}", exc_info=True)
            return {"error": str(e)}