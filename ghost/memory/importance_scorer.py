"""Score message importance for selective memory storage."""

import logging
import re
from typing import List
from ghost.core.interfaces import Message

logger = logging.getLogger(__name__)


class ImportanceScorer:
    """
    Scores messages by importance to prioritize what gets stored long-term.
    
    High importance indicators:
    - User sharing personal information
    - User preferences
    - Future plans/commitments
    - Questions needing follow-up
    - Emotional moments
    - User corrections
    """
    
    # Keywords indicating important information
    PERSONAL_INFO_KEYWORDS = [
        'my name is', 'i am', "i'm", 'i live', 'i work', 'my job',
        'my birthday', 'i like', 'i love', 'i hate', 'i prefer'
    ]
    
    PREFERENCE_KEYWORDS = [
        'favorite', 'prefer', 'like', 'dislike', 'love', 'hate',
        'always', 'never', 'usually', 'often'
    ]
    
    FUTURE_KEYWORDS = [
        'will', 'going to', 'plan to', 'want to', 'need to',
        'tomorrow', 'next week', 'later', 'soon', 'remember to'
    ]
    
    EMOTIONAL_KEYWORDS = [
        'feel', 'feeling', 'happy', 'sad', 'angry', 'excited',
        'worried', 'stressed', 'anxious', 'grateful'
    ]
    
    CORRECTION_KEYWORDS = [
        'actually', 'correction', 'i meant', 'not', "didn't", "don't"
    ]
    
    def score_message(self, message: Message) -> float:
        """
        Score message importance from 0.0 (trivial) to 1.0 (critical).
        
        Returns:
            Importance score
        """
        if message.role != 'user':
            return 0.3  # Assistant messages less important
        
        content = message.content.lower()
        score = 0.5  # Base score
        
        # Check for personal information
        if any(kw in content for kw in self.PERSONAL_INFO_KEYWORDS):
            score += 0.3
        
        # Check for preferences
        if any(kw in content for kw in self.PREFERENCE_KEYWORDS):
            score += 0.2
        
        # Check for future plans
        if any(kw in content for kw in self.FUTURE_KEYWORDS):
            score += 0.2
        
        # Check for emotional content
        if any(kw in content for kw in self.EMOTIONAL_KEYWORDS):
            score += 0.15
        
        # Check for corrections (very important!)
        if any(kw in content for kw in self.CORRECTION_KEYWORDS):
            score += 0.25
        
        # Length bonus (longer messages often more substantial)
        word_count = len(content.split())
        if word_count > 30:
            score += 0.1
        elif word_count < 3:
            score -= 0.2  # Very short messages likely trivial
        
        # Question mark indicates seeking information
        if '?' in content:
            score += 0.1
        
        # Clamp score
        return max(0.0, min(1.0, score))
    
    def filter_by_importance(
        self, 
        messages: List[Message], 
        threshold: float = 0.6
    ) -> List[Message]:
        """Filter messages by importance threshold."""
        important_messages = []
        
        for msg in messages:
            score = self.score_message(msg)
            if score >= threshold:
                # Add score to metadata
                msg.metadata['importance_score'] = score
                important_messages.append(msg)
        
        return important_messages