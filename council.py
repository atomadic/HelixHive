"""
Council – governance and voting for HelixHive.
Implements weighted voting with fitness, constitutional checks, and guardian veto.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)


class Council:
    """
    HelixHive Council with six fixed members.
    Each member has a base weight and may have additional weight based on fitness.
    Guardian has veto power.
    """

    MEMBERS = ["visionary", "skeptic", "pragmatist", "innovator", "guardian", "harmonizer"]
    DEFAULT_WEIGHTS = {"guardian": 2, "visionary": 1.5}  # others default 1

    MEMBER_PREFERENCES = {
        "visionary": ["longterm", "visionary", "bold"],
        "skeptic": ["evidence", "proven", "data"],
        "pragmatist": ["feasible", "practical", "cost-effective"],
        "innovator": ["novel", "innovative", "breakthrough"],
        "guardian": [],  # guardian uses ethics check, not tags
        "harmonizer": ["consensus", "balanced", "harmonious"]
    }

    def __init__(self, genome: Any):
        self.genome = genome
        self.weights = self.DEFAULT_WEIGHTS.copy()
        if 'council' in genome.data and 'weights' in genome.data['council']:
            self.weights.update(genome.data['council']['weights'])

        # Load constitution
        self.constitution = genome.data.get('constitution', {})
        self.protected_keys = self.constitution.get('protected', [])
        self.supermajority = self.constitution.get('supermajority_threshold', 5/6)

    def _check_ethics(self, text: str) -> bool:
        """Return True if text is ethical (no forbidden patterns)."""
        forbidden = self.genome.data.get('ethics', {}).get('forbidden_patterns', [])
        text_lower = text.lower()
        for pattern in forbidden:
            if pattern.lower() in text_lower:
                logger.warning(f"Ethics veto triggered by pattern: {pattern}")
                return False
        return True

    def _check_constitutional(self, proposal: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if proposal violates any constitutional protections.
        Returns (allowed, reason).
        """
        changes = proposal.get('changes', {})
        # For genome proposals, check if any protected key is being modified
        if proposal.get('type') == 'genome':
            params = changes.get('parameters', {})
            for key in params:
                if key in self.protected_keys:
                    return False, f"Modification of protected key '{key}' requires supermajority"
        return True, ""

    def _get_member_vote(self, member: str, proposal: Dict[str, Any]) -> Tuple[str, str]:
        """Determine a member's vote based on tags and description."""
        tags = proposal.get('tags', [])
        description = proposal.get('description', '')

        if member == "guardian":
            if not self._check_ethics(description):
                return "no", "Ethics manifest violation"
            if 'safe' in tags:
                return "yes", "Proposal is safe"
            else:
                return "no", "Missing 'safe' tag"

        prefs = self.MEMBER_PREFERENCES.get(member, [])
        for tag in prefs:
            if tag in tags:
                return "yes", f"Matches preference: {tag}"
        return "no", "No matching preference"

    def vote(self, proposal: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Conduct a council vote on a proposal.
        Returns (approved, transcript).
        """
        # Constitutional check
        allowed, reason = self._check_constitutional(proposal)
        if not allowed:
            return False, f"Constitutional veto: {reason}"

        votes = []
        reasons = []
        for member in self.MEMBERS:
            vote, reason = self._get_member_vote(member, proposal)
            votes.append(vote)
            reasons.append(reason)
            logger.debug(f"{member} votes {vote}: {reason}")

        # Guardian veto
        guardian_index = self.MEMBERS.index("guardian")
        if votes[guardian_index] == "no":
            transcript = self._format_transcript(votes, reasons, veto=True)
            return False, transcript

        # Weighted vote with fitness multiplier
        fitness = proposal.get('fitness_score', 0.5)
        total_weight = 0
        yes_weight = 0
        for i, member in enumerate(self.MEMBERS):
            base = self.weights.get(member, 1)
            # Apply fitness multiplier (e.g., weight = base * (1 + fitness))
            w = base * (1 + fitness)
            total_weight += w
            if votes[i] == "yes":
                yes_weight += w

        # Determine if supermajority needed
        required = self.supermajority if proposal.get('type') == 'genome' and any(
            k in self.protected_keys for k in proposal.get('changes', {}).get('parameters', {})
        ) else 0.6

        approved = (yes_weight / total_weight) >= required

        transcript = self._format_transcript(votes, reasons, veto=False)
        return approved, transcript

    def _format_transcript(self, votes: List[str], reasons: List[str], veto: bool = False) -> str:
        lines = ["=== COUNCIL VOTE TRANSCRIPT ==="]
        for i, member in enumerate(self.MEMBERS):
            lines.append(f"{member.capitalize()}: {votes[i].upper()} – {reasons[i]}")
        if veto:
            lines.append("GUARDIAN VETO – Proposal rejected.")
        else:
            lines.append(f"Vote result: {'APPROVED' if (sum(1 for v in votes if v=='yes') >= 4) else 'REJECTED'}")
        return "\n".join(lines)
