"""Redis-based fast cache for recent memories."""

import logging
import json
from typing import List, Optional
from ghost.core.interfaces import Message

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedisMemoryCache:
    """Fast Redis cache for recent conversations."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", ttl: int = 3600):
        self.ttl = ttl  # Time to live in seconds
        self.client = None
        
        if REDIS_AVAILABLE:
            try:
                self.client = redis.from_url(redis_url, decode_responses=True)
                logger.info("Redis memory cache initialized")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
        else:
            logger.warning("redis package not installed, cache disabled")
    
    async def get_recent_messages(self, user_id: str, limit: int = 20) -> List[Message]:
        """Get recent messages from cache."""
        if not self.client:
            return []
        
        try:
            key = f"messages:{user_id}"
            messages_json = await self.client.lrange(key, 0, limit - 1)
            
            messages = []
            for msg_json in messages_json:
                msg_data = json.loads(msg_json)
                messages.append(Message(**msg_data))
            
            return messages
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return []
    
    async def add_message(self, user_id: str, message: Message) -> None:
        """Add message to cache."""
        if not self.client:
            return
        
        try:
            key = f"messages:{user_id}"
            msg_json = json.dumps({
                "role": message.role,
                "content": message.content,
                "metadata": message.metadata
            })
            
            # Add to list (LPUSH adds to beginning)
            await self.client.lpush(key, msg_json)
            
            # Trim to keep only recent messages
            await self.client.ltrim(key, 0, 49)  # Keep 50 messages
            
            # Set expiration
            await self.client.expire(key, self.ttl)
            
        except Exception as e:
            logger.error(f"Redis add failed: {e}")