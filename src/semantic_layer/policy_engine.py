"""
Policy Engine

Runtime authorization enforcement for semantic layer access.
Implements allow/deny policies based on roles and conditions.
"""

import logging
from typing import Optional, List, Dict, Any

from .models import AccessPolicy, PolicyDeniedError
from .interfaces import PolicyStore
from .sqlite_stores import SQLitePolicyStore

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Enforces access policies for semantic object queries.

    Uses RBAC (Role-Based Access Control) with ABAC (Attribute-Based) conditions.
    Policies are evaluated in priority order.
    """

    def __init__(self, policy_store: Optional[PolicyStore] = None, db_path: Optional[str] = None):
        """
        Initialize the policy engine.

        Args:
            policy_store: Policy store implementation
            db_path: Path to SQLite database containing access_policy table
        """
        if policy_store is None:
            if not db_path:
                raise ValueError("db_path is required when policy_store is not provided")
            policy_store = SQLitePolicyStore(db_path)
        self.policy_store = policy_store

    def check_access(
        self,
        semantic_object_id: int,
        role: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check if a user with given role can perform action on semantic object.

        Args:
            semantic_object_id: ID of semantic object
            role: User role (e.g., 'operator', 'analyst', 'admin')
            action: Action to perform (e.g., 'query', 'execute', 'export')
            context: Additional context for conditional policies

        Returns:
            Decision dict with {allow: bool, reason: str, policies: list}

        Raises:
            PolicyDeniedError: If access is denied
        """
        logger.info(f"=== POLICY CHECK ===")
        logger.info(f"Semantic Object ID: {semantic_object_id}")
        logger.info(f"Role: {role}")
        logger.info(f"Action: {action}")
        logger.info(f"Context: {context}")

        # Get applicable policies
        policies = self._get_applicable_policies(semantic_object_id, role, action)
        logger.info(f"Found {len(policies)} applicable policies")

        if not policies:
            # Default deny: no policies means no access
            logger.warning("No policies found - default deny")
            decision = {
                'allow': False,
                'reason': 'No access policies defined - default deny',
                'policies': []
            }
        else:
            # Evaluate policies in priority order
            decision = self._evaluate_policies(policies, context)

        logger.info(f"Decision: {'ALLOW' if decision['allow'] else 'DENY'}")
        logger.info(f"Reason: {decision['reason']}")

        if not decision['allow']:
            raise PolicyDeniedError(decision['reason'])

        return decision

    def _get_applicable_policies(
        self,
        semantic_object_id: int,
        role: str,
        action: str
    ) -> List[AccessPolicy]:
        """
        Retrieve policies that match the object/role/action combination.
        Returns ordered by priority (highest first).
        """
        return self.policy_store.get_applicable_policies(semantic_object_id, role, action)

    def _evaluate_policies(
        self,
        policies: List[AccessPolicy],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate policies in priority order.

        Evaluation rules:
        1. Process policies from highest to lowest priority
        2. First matching policy (by condition) wins
        3. Deny policies take precedence over allow (security principle)
        4. Explicit deny stops evaluation
        5. If no policies match, default deny
        """
        matched_policies = []

        for policy in policies:
            # Check if policy conditions match context
            if self._matches_condition(policy, context):
                logger.debug(f"Policy matched: {policy.id} (effect={policy.effect})")
                matched_policies.append(policy)

                # Explicit deny stops evaluation
                if policy.effect == 'deny':
                    return {
                        'allow': False,
                        'reason': f'Denied by policy {policy.id}: {policy.condition}',
                        'policies': matched_policies
                    }

        # If we have matching allow policies, allow access
        if matched_policies and all(p.effect == 'allow' for p in matched_policies):
            return {
                'allow': True,
                'reason': f'Allowed by {len(matched_policies)} policy(ies)',
                'policies': matched_policies
            }

        # Default deny
        return {
            'allow': False,
            'reason': 'No matching allow policy found - default deny',
            'policies': matched_policies
        }

    def _matches_condition(self, policy: AccessPolicy, context: Optional[Dict[str, Any]]) -> bool:
        """
        Check if policy condition matches the given context.

        For POC, implements simple key-value matching.
        In production, would support complex expressions (e.g., CEL, JMESPath).
        """
        if not policy.condition:
            # No condition means policy always matches
            return True

        if not context:
            # Policy has condition but no context provided
            return False

        # Check all key-value pairs in condition
        for key, expected_value in policy.condition.items():
            if key not in context:
                return False
            if context[key] != expected_value:
                return False

        return True

    def get_user_policies(self, role: str) -> List[Dict[str, Any]]:
        """
        Get all policies applicable to a role (for debugging/display).

        Args:
            role: User role

        Returns:
            List of policy summaries
        """
        return self.policy_store.get_user_policies(role)

    def create_policy(
        self,
        semantic_object_id: int,
        role: str,
        action: str,
        effect: str,
        condition: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> int:
        """
        Create a new access policy.

        Args:
            semantic_object_id: Target semantic object
            role: Role this policy applies to
            action: Action this policy applies to
            effect: 'allow' or 'deny'
            condition: Optional condition dict (JSON)
            priority: Policy priority (higher evaluated first)

        Returns:
            ID of created policy
        """
        return self.policy_store.create_policy(
            semantic_object_id=semantic_object_id,
            role=role,
            action=action,
            effect=effect,
            condition=condition,
            priority=priority
        )
