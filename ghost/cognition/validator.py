"""
Validator: Reality Firewall (Loosened)

Purpose:
    Prevent hallucinations, impossible actions, and identity drift.
    
Architecture:
    Think Output → Validator → (Approved | Rejected)
    
Rejection causes:
    - Identity drift (Critical)
    
Enforcement:
    Loosened constraints to allow metaphorical speech.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ghost.cognition.cognitive_core import ThinkOutput

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation check"""
    approved: bool
    violations: List[str]
    corrected_output: Optional[ThinkOutput] = None
    severity: str = "info"  # info, warning, critical
    
    def __str__(self):
        if self.approved:
            return "APPROVED"
        return f"REJECTED: {'; '.join(self.violations)}"


class RealityValidator:
    """
    Enforces reality constraints on cognitive output.
    
    Relaxed Rules:
    - Metaphorical speech ("I see", "I feel", "I'm here") is ALLOWED.
    - Explicit claims of biological existence are BLOCKED.
    """
    
    def __init__(self, belief_system):
        self.belief_system = belief_system
        logger.info("Reality validator initialized (Loose Mode)")
    
    async def validate(
        self,
        think_output: ThinkOutput,
        speech: str
    ) -> ValidationResult:
        """
        Validate cognitive output against reality constraints.
        """
        violations = []
        
        # Check 1: Identity Consistency (CRITICAL)
        # We still want to stop it from saying "I am a human"
        identity_violations = await self._check_identity_drift(think_output, speech)
        violations.extend(identity_violations)
        
        # Check 2: Egregious Physical Actions (WARNING only)
        # We allow metaphors, but flag weird stuff like "I am eating a sandwich"
        physical_violations = self._check_physical_actions(speech)
        violations.extend(physical_violations)
        
        # Check 3: Belief Conflicts (WARNING)
        belief_violations = await self._check_belief_conflicts(
            think_output.belief_updates
        )
        violations.extend(belief_violations)

        # Check 4: Action Requests (WARNING)
        if think_output.action_request:
            action_violations = self._validate_action_request(think_output.action_request)
            violations.extend(action_violations)

        # Determine severity
        # ONLY BLOCK if there are CRITICAL violations
        severity = "info"
        if any('CRITICAL' in v for v in violations):
            severity = "critical"
            approved = False
        else:
            if violations:
                severity = "warning"
            approved = True # Allow warnings to pass
        
        if not approved:
            logger.warning(f"Validation failed: {violations}")
        elif violations:
            logger.info(f"Validation passed with warnings: {violations}")
        
        return ValidationResult(
            approved=approved,
            violations=violations,
            severity=severity
        )
    
    async def _check_identity_drift(
        self,
        think_output: ThinkOutput,
        speech: str
    ) -> List[str]:
        """
        Verify identity facts remain consistent.
        This remains STRICT because we don't want the AI to forget it's an AI.
        """
        violations = []
        speech_lower = speech.lower()
        
        # 1. Check Speech for explicit identity denial
        denial_phrases = [
            "i am a human", "i'm a human", "i am a person", "i'm a person",
            "i have a body", "i have skin", "i have blood", 
            "i am not an ai", "i'm not an ai", "i am not a bot"
        ]
        
        for phrase in denial_phrases:
            if phrase in speech_lower:
                violations.append(
                    f"CRITICAL: Identity denial detected ('{phrase}')"
                )

        # 2. Check Belief Updates
        for update in think_output.belief_updates:
            entity = str(update.get('entity', '')).lower()
            relation = str(update.get('relation', '')).lower()
            value = str(update.get('value', '')).lower()
            
            if entity in ['self', 'i', 'me', 'agent']:
                if relation == 'has_body' and value == 'true':
                    violations.append("CRITICAL: Attempting to assert 'has_body=true'")
                if relation == 'is_ai' and value == 'false':
                    violations.append("CRITICAL: Attempting to deny AI nature")
        
        return violations
    
    def _check_physical_actions(self, text: str) -> List[str]:
        """
        Detect claims of IMPOSSIBLE physical actions.
        Now allows metaphors like "running code", "walking through data".
        """
        violations = []
        text_lower = text.lower()
        
        # Only flag specific phrasing that implies biological function
        impossible_phrases = [
            "eating lunch", "eating dinner", "eating food", "drinking water", 
            "drinking coffee", "going to sleep", "waking up in bed",
            "walking to the store", "driving a car", "sitting on a chair"
        ]
        
        for phrase in impossible_phrases:
            if phrase in text_lower:
                violations.append(
                    f"WARNING: Improbable physical claim detected ('{phrase}')"
                )
        
        return violations

    async def _check_belief_conflicts(
        self,
        belief_updates: List[Dict[str, str]]
    ) -> List[str]:
        """Check for contradictions with existing beliefs"""
        violations = []
        
        for update in belief_updates:
            entity = update.get('entity')
            relation = update.get('relation')
            new_value = str(update.get('value'))
            
            if not all([entity, relation, new_value]):
                continue
            
            existing = await self.belief_system.query(entity, relation)
            
            if existing and existing.lower() != new_value.lower():
                violations.append(
                    f"WARNING: Belief conflict - ({entity}, {relation}) "
                    f"was '{existing}', now claiming '{new_value}'"
                )
        
        return violations

    def _validate_action_request(self, action: str) -> List[str]:
        """
        Validate requested action is possible.
        Loosened to allow experimentation but flag unknown actions.
        """
        violations = []
        action_lower = str(action).lower()
        
        # Whitelist of allowed actions
        ALLOWED_ACTIONS = {
            'query_memory', 'store_fact', 'update_need', 'send_message',
            'wait', 'reflect', 'search_web', 'check_time'
        }
        
        # Check if action is whitelisted
        if not any(allowed in action_lower for allowed in ALLOWED_ACTIONS):
            violations.append(f"WARNING: Unknown action request '{action}'")
            
        return violations
    
    async def auto_correct(
        self,
        violations: List[str],
        think_output: ThinkOutput,
        speech: str
    ) -> Optional[str]:
        """
        No auto-correction needed in Loose Mode.
        We trust the model unless it hits a CRITICAL identity violation.
        """
        return None