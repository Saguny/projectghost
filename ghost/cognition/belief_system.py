"""
Belief System: Knowledge Graph for Facts

Architecture:
    Stores beliefs as (entity, relation, value) triplets
    Enables fact verification and contradiction detection
    
Examples:
    (user, name, "Sagun")
    (user, lives_in, "Berlin")
    (agent, is_ai, True)
    (agent, has_body, False)
    
Purpose:
    - Prevent hallucinations
    - Enforce consistency
    - Enable fact-based reasoning
    
Storage:
    SQLite for simplicity and persistence
    Could scale to Neo4j for complex graphs
"""

import logging
import sqlite3
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class BeliefSystem:
    """
    Knowledge graph for agent beliefs and facts.
    
    Schema:
        (entity, relation, value, timestamp, confidence, source)
    
    Operations:
        - store(entity, relation, value)
        - query(entity, relation) → value
        - verify(entity, relation, value) → bool
        - get_all(entity) → {relation: value}
    """
    
    def __init__(self, db_path: str = "data/beliefs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        self._load_core_beliefs()
        
        logger.info(f"Belief system initialized: {self.db_path}")
    
    def _init_database(self):
        """Create database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS beliefs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    value TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source TEXT,
                    UNIQUE(entity, relation)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity 
                ON beliefs(entity)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relation 
                ON beliefs(relation)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _load_core_beliefs(self):
        """Initialize core identity beliefs (immutable)"""
        core_beliefs = [
            # Agent identity (immutable)
            ('agent', 'is_ai', 'true', 1.0, 'core'),
            ('agent', 'has_body', 'false', 1.0, 'core'),
            ('agent', 'has_location', 'false', 1.0, 'core'),
            ('agent', 'exists_physically', 'false', 1.0, 'core'),
            ('agent', 'can_physical_action', 'false', 1.0, 'core'),
            ('agent', 'name', 'Korone', 1.0, 'core'),
            ('agent', 'type', 'autonomous_ai', 1.0, 'core'),
            
            # Capabilities (immutable)
            ('agent', 'can_think', 'true', 1.0, 'core'),
            ('agent', 'can_remember', 'true', 1.0, 'core'),
            ('agent', 'can_reason', 'true', 1.0, 'core'),
            ('agent', 'can_converse', 'true', 1.0, 'core'),
        ]
        
        for entity, relation, value, confidence, source in core_beliefs:
            self.store(entity, relation, value, confidence, source)
    
    async def store(
        self,
        entity: str,
        relation: str,
        value: str,
        confidence: float = 1.0,
        source: str = 'inference'
    ) -> bool:
        """
        Store or update a belief.
        
        Args:
            entity: Subject (e.g., "user", "agent")
            relation: Predicate (e.g., "name", "likes")
            value: Object (e.g., "Sagun", "cats")
            confidence: Certainty (0-1)
            source: Where fact came from
            
        Returns:
            Success boolean
        """
        
        # Validate core beliefs (immutable)
        if source == 'core':
            # Allow initial creation of core beliefs
            pass
        else:
            # Check if trying to modify core belief
            existing = await self.query(entity, relation)
            if existing:
                existing_source = await self._get_source(entity, relation)
                if existing_source == 'core':
                    logger.warning(
                        f"Attempted to modify core belief: "
                        f"({entity}, {relation}, {value})"
                    )
                    return False
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO beliefs 
                    (entity, relation, value, timestamp, confidence, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (entity, relation, value, timestamp, confidence, source))
                conn.commit()
            
            logger.debug(f"Stored: ({entity}, {relation}, {value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store belief: {e}")
            return False
    
    async def query(
        self,
        entity: str,
        relation: str
    ) -> Optional[str]:
        """
        Query a specific fact.
        
        Args:
            entity: Subject
            relation: Predicate
            
        Returns:
            Value or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT value FROM beliefs
                    WHERE entity = ? AND relation = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (entity, relation))
                
                row = cursor.fetchone()
                return row['value'] if row else None
                
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return None
    
    async def verify(
        self,
        entity: str,
        relation: str,
        value: str
    ) -> bool:
        """
        Verify if a belief matches stored fact.
        
        Returns:
            True if matches, False if contradicts or unknown
        """
        stored_value = await self.query(entity, relation)
        
        if stored_value is None:
            return True  # Unknown, not contradicted
        
        return stored_value.lower() == value.lower()
    
    async def get_all(
        self,
        entity: str
    ) -> Dict[str, str]:
        """
        Get all beliefs about an entity.
        
        Returns:
            {relation: value} dictionary
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT relation, value FROM beliefs
                    WHERE entity = ?
                    ORDER BY timestamp DESC
                """, (entity,))
                
                return {row['relation']: row['value'] for row in cursor}
                
        except Exception as e:
            logger.error(f"Get all failed: {e}")
            return {}
    
    async def search(
        self,
        entity: Optional[str] = None,
        relation: Optional[str] = None,
        limit: int = 10
    ) -> List[Tuple[str, str, str]]:
        """
        Search beliefs by entity or relation.
        
        Returns:
            List of (entity, relation, value) tuples
        """
        try:
            with self._get_connection() as conn:
                if entity and relation:
                    cursor = conn.execute("""
                        SELECT entity, relation, value FROM beliefs
                        WHERE entity = ? AND relation = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (entity, relation, limit))
                elif entity:
                    cursor = conn.execute("""
                        SELECT entity, relation, value FROM beliefs
                        WHERE entity = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (entity, limit))
                elif relation:
                    cursor = conn.execute("""
                        SELECT entity, relation, value FROM beliefs
                        WHERE relation = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (relation, limit))
                else:
                    cursor = conn.execute("""
                        SELECT entity, relation, value FROM beliefs
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                return [
                    (row['entity'], row['relation'], row['value']) 
                    for row in cursor
                ]
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def _get_source(
        self,
        entity: str,
        relation: str
    ) -> Optional[str]:
        """Get source of a belief"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT source FROM beliefs
                    WHERE entity = ? AND relation = ?
                """, (entity, relation))
                
                row = cursor.fetchone()
                return row['source'] if row else None
                
        except Exception as e:
            logger.error(f"Get source failed: {e}")
            return None
    
    async def get_summary(self) -> str:
        """Get human-readable summary of beliefs"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) as count FROM beliefs
                """)
                total = cursor.fetchone()['count']
                
                # Get recent beliefs
                cursor = conn.execute("""
                    SELECT entity, relation, value FROM beliefs
                    ORDER BY timestamp DESC
                    LIMIT 10
                """)
                
                recent = [
                    f"  ({row['entity']}, {row['relation']}, {row['value']})"
                    for row in cursor
                ]
                
                return f"""
Belief System Status:
- Total beliefs: {total}
- Recent:
{chr(10).join(recent)}
"""
        except Exception as e:
            return f"Error getting summary: {e}"
    
    async def export_graph(self, output_path: str):
        """Export beliefs as JSON for visualization"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT entity, relation, value, confidence, source, timestamp
                    FROM beliefs
                    ORDER BY entity, relation
                """)
                
                beliefs = [
                    {
                        'entity': row['entity'],
                        'relation': row['relation'],
                        'value': row['value'],
                        'confidence': row['confidence'],
                        'source': row['source'],
                        'timestamp': row['timestamp']
                    }
                    for row in cursor
                ]
            
            with open(output_path, 'w') as f:
                json.dump(beliefs, f, indent=2)
            
            logger.info(f"Exported {len(beliefs)} beliefs to {output_path}")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")