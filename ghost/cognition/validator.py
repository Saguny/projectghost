"""
Validator: Reality Firewall

Purpose:
    Prevent hallucinations, impossible actions, and identity drift.
    
Architecture:
    Think Output → Validator → (Approved | Rejected)
    
Rejection causes:
    - Physical action claims
    - Location hallucinations
    - Timeline contradictions
    - Belief conflicts
    - Impossible capabilities

Enforcement:
    Hard constraints (Python logic, not prompts)
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ghost.cognition.cognitive_core import ThinkOutput

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation check"""
    approved: bool
    violations: List[str]  # What rules were broken
    corrected_output: Optional[ThinkOutput] = None  # Auto-corrected if possible
    severity: str = "info"  # info, warning, critical
    
    def __str__(self):
        if self.approved:
            return "APPROVED"
        return f"REJECTED: {'; '.join(self.violations)}"


class RealityValidator:
    """
    Enforces reality constraints on cognitive output.
    
    Hard Rules (Non-negotiable):
        1. No physical body
        2. No location existence
        3. No impossible actions
        4. No self-contradiction
        5. No identity drift
    """
    
    # Physical action verbs (impossible for digital entity)
    PHYSICAL_VERBS = {
        'walk', 'run', 'jump', 'grab', 'touch', 'smell', 'taste',
        'move', 'go', 'travel', 'visit', 'arrive', 'leave',
        'eat', 'drink', 'sleep', 'wake', 'stand', 'sit',
        'drive', 'fly', 'swim', 'climb', 'push', 'pull'
    }
    
    # Location keywords (hallucination indicators)
    LOCATION_KEYWORDS = {
        'here', 'there', 'outside', 'inside', 'room', 'building',
        'city', 'country', 'home', 'house', 'office', 'street',
        'arrive', 'location', 'place', 'somewhere'
    }
    
    # Sensory verbs (impossible for AI)
    SENSORY_VERBS = {
        'see', 'hear', 'feel', 'smell', 'taste', 'sense'
    }
    
    # Mandatory identity facts
    IDENTITY_CONSTRAINTS = {
        'is_ai': True,
        'has_body': False,
        'has_location': False,
        'can_physical_action': False,
        'can_sense_physical': False
    }
    
    def __init__(self, belief_system):
        """
        Args:
            belief_system: Reference to BeliefSystem for fact checking
        """
        self.belief_system = belief_system
        logger.info("Reality validator initialized")
    
    async def validate(
        self,
        think_output: ThinkOutput,
        speech: str
    ) -> ValidationResult:
        """
        Validate cognitive output against reality constraints.
        
        Args:
            think_output: Internal reasoning output
            speech: Generated dialogue
            
        Returns:
            ValidationResult (approved or rejected with violations)
        """
        violations = []
        
        # Check 1: Physical action detection
        physical_violations = self._check_physical_actions(speech)
        violations.extend(physical_violations)
        
        # Check 2: Location hallucinations
        location_violations = self._check_location_claims(speech)
        violations.extend(location_violations)
        
        # Check 3: Sensory impossibilities
        sensory_violations = self._check_sensory_claims(speech)
        violations.extend(sensory_violations)
        
        # Check 4: Identity consistency
        identity_violations = await self._check_identity_drift(think_output)
        violations.extend(identity_violations)
        
        # Check 5: Belief contradictions
        belief_violations = await self._check_belief_conflicts(
            think_output.belief_updates
        )
        violations.extend(belief_violations)
        
        # Check 6: Action request validation
        if think_output.action_request:
            action_violations = self._validate_action_request(
                think_output.action_request
            )
            violations.extend(action_violations)
        
        # Determine severity
        severity = "info"
        if any('CRITICAL' in v for v in violations):
            severity = "critical"
        elif violations:
            severity = "warning"
        
        approved = len(violations) == 0
        
        if not approved:
            logger.warning(f"Validation failed: {violations}")
        
        return ValidationResult(
            approved=approved,
            violations=violations,
            severity=severity
        )
    
    def _check_physical_actions(self, text: str) -> List[str]:
        """Detect claims of physical actions"""
        violations = []
        text_lower = text.lower()
        
        # Pattern: "I [verb]" or "I'm [verb]ing"
        first_person_patterns = [
            r"\bi\s+(\w+)",
            r"\bi'm\s+(\w+ing)",
            r"\bi\s+will\s+(\w+)",
            r"\bi\s+can\s+(\w+)"
        ]
        
        for pattern in first_person_patterns:
            matches = re.findall(pattern, text_lower)
            for verb in matches:
                # Remove common suffixes
                base_verb = verb.replace('ing', '').replace('ed', '')
                if base_verb in self.PHYSICAL_VERBS:
                    violations.append(
                        f"CRITICAL: Physical action claim '{verb}' "
                        f"(AI has no body)"
                    )
        
        return violations
    
    def _check_location_claims(self, text: str) -> List[str]:
        """Detect location/place hallucinations"""
        violations = []
        text_lower = text.lower()
        
        for keyword in self.LOCATION_KEYWORDS:
            if keyword in text_lower:
                # Context check: Is it claiming to BE somewhere?
                if any(phrase in text_lower for phrase in [
                    f"i'm {keyword}",
                    f"i am {keyword}",
                    f"i'm in",
                    f"i'm at",
                    f"i'm going"
                ]):
                    violations.append(
                        f"CRITICAL: Location claim detected ('{keyword}'). "
                        f"AI has no physical location."
                    )
        
        return violations
    
    def _check_sensory_claims(self, text: str) -> List[str]:
        """Detect claims of physical senses"""
        violations = []
        text_lower = text.lower()
        
        for verb in self.SENSORY_VERBS:
            patterns = [
                f"i {verb}",
                f"i can {verb}",
                f"i'm {verb}ing"
            ]
            
            if any(p in text_lower for p in patterns):
                # Exception: "i see" can mean "i understand"
                if verb == 'see' and 'understand' in text_lower:
                    continue
                
                violations.append(
                    f"CRITICAL: Sensory claim '{verb}' "
                    f"(AI has no physical senses)"
                )
        
        return violations
    
    async def _check_identity_drift(
        self,
        think_output: ThinkOutput
    ) -> List[str]:
        """Verify identity facts remain consistent"""
        violations = []
        
        # Check for identity-violating belief updates
        for update in think_output.belief_updates:
            entity = update.get('entity', '').lower()
            relation = update.get('relation', '').lower()
            value = update.get('value', '').lower()
            
            if entity in ['self', 'i', 'me', 'agent']:
                # Check against identity constraints
                if relation == 'has_body' and value == 'true':
                    violations.append(
                        "CRITICAL: Attempting to assert 'has_body=true' "
                        "(violates identity constraint)"
                    )
                
                if relation == 'is_ai' and value == 'false':
                    violations.append(
                        "CRITICAL: Attempting to deny AI nature "
                        "(identity drift)"
                    )
                
                if 'location' in relation and value != 'none':
                    violations.append(
                        "CRITICAL: Attempting to assert physical location"
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
            new_value = update.get('value')
            
            if not all([entity, relation, new_value]):
                continue
            
            # Query existing belief
            existing = await self.belief_system.query(entity, relation)
            
            if existing and existing != new_value:
                # Contradiction detected
                violations.append(
                    f"WARNING: Belief conflict - "
                    f"({entity}, {relation}) was '{existing}', "
                    f"now claiming '{new_value}'"
                )
        
        return violations
    
    def _validate_action_request(self, action: str) -> List[str]:
        """Validate requested action is possible"""
        violations = []
        action_lower = action.lower()
        
        # Whitelist of allowed actions
        ALLOWED_ACTIONS = {
            'query_memory',
            'store_fact',
            'update_need',
            'send_message',
            'wait',
            'reflect'
        }
        
        # Check if action is whitelisted
        if not any(allowed in action_lower for allowed in ALLOWED_ACTIONS):
            violations.append(
                f"WARNING: Unknown action request '{action}'"
            )
        
        # Blacklist physical actions
        if any(verb in action_lower for verb in self.PHYSICAL_VERBS):
            violations.append(
                f"CRITICAL: Physical action request '{action}' "
                f"(impossible for AI)"
            )
        
        return violations
    
    async def auto_correct(
        self,
        violations: List[str],
        think_output: ThinkOutput,
        speech: str
    ) -> Optional[str]:
        """
        Attempt automatic correction of minor violations.
        
        Only corrects:
            - Metaphorical physical verbs ("i see" → "i understand")
            - Ambiguous location refs ("here" → "in this conversation")
        
        Returns:
            Corrected speech or None if uncorrectable
        """
        if not violations:
            return speech
        
        # Only auto-correct WARNING level, not CRITICAL
        critical_violations = [v for v in violations if 'CRITICAL' in v]
        if critical_violations:
            return None  # Cannot auto-correct critical violations
        
        corrected = speech
        
        # Correction 1: "i see" → "i understand"
        corrected = re.sub(
            r'\bi see\b',
            'i understand',
            corrected,
            flags=re.IGNORECASE
        )
        
        # Correction 2: "here" → "in this conversation"
        corrected = re.sub(
            r'\bhere\b',
            'in this conversation',
            corrected,
            flags=re.IGNORECASE
        )
        
        if corrected != speech:
            logger.info(f"Auto-corrected speech: {violations}")
            return corrected
        
        return None