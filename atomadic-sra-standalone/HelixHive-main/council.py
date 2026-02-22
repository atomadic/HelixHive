"""
Council – governance and voting for HelixHive Phase 2.
Implements weighted voting with fitness, constitutional checks (supermajority, protected keys),
guardian veto, and audit‑grade vote recording.
"""

import logging
import time
from typing import Dict, List, Tuple, Any, Optional

from genome import Genome
from helixdb_git_adapter import HelixDBGit

logger = logging.getLogger(__name__)


class Council:
    """
    HelixHive Council with six fixed members.
    Each member has a base weight, may have additional weight based on proposal fitness,
    and may have preferences for certain tags.
    Constitution defines protected parameters and supermajority thresholds.
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

    def __init__(self, genome: Genome, db: HelixDBGit):
        """
        Args:
            genome: Genome object containing council weights and constitution.
            db: Database adapter for recording votes.
        """
        self.genome = genome
        self.db = db
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

    def vote(self, proposal: Dict[str, Any]) -> Tuple[bool, str, Dict]:
        """
        Conduct a council vote on a proposal.
        Returns (approved, transcript, vote_record).
        """
        # Constitutional check
        allowed, reason = self._check_constitutional(proposal)
        if not allowed:
            return False, f"Constitutional veto: {reason}", {}

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
            self._record_vote(proposal, votes, reasons, approved=False, veto=True)
            return False, transcript, self._last_record

        # Weighted vote with fitness multiplier
        fitness = proposal.get('fitness_score', 0.5)
        total_weight = 0
        yes_weight = 0
        member_weights = {}
        for i, member in enumerate(self.MEMBERS):
            base = self.weights.get(member, 1)
            w = base * (1 + fitness)
            member_weights[member] = w
            total_weight += w
            if votes[i] == "yes":
                yes_weight += w

        # Determine if supermajority needed
        needs_super = (proposal.get('type') == 'genome' and
                       any(k in self.protected_keys for k in proposal.get('changes', {}).get('parameters', {})))
        required = self.supermajority if needs_super else 0.6

        approved = (yes_weight / total_weight) >= required

        transcript = self._format_transcript(votes, reasons, veto=False)
        self._record_vote(proposal, votes, reasons, approved, veto=False,
                          member_weights=member_weights, yes_weight=yes_weight, total_weight=total_weight,
                          required=required)
        return approved, transcript, self._last_record

    def _format_transcript(self, votes: List[str], reasons: List[str], veto: bool = False) -> str:
        lines = ["=== COUNCIL VOTE TRANSCRIPT ==="]
        for i, member in enumerate(self.MEMBERS):
            lines.append(f"{member.capitalize()}: {votes[i].upper()} – {reasons[i]}")
        if veto:
            lines.append("GUARDIAN VETO – Proposal rejected.")
        else:
            # Simple outcome, actual approval determined elsewhere
            lines.append("Vote recorded.")
        return "\n".join(lines)

    def _record_vote(self, proposal: Dict, votes: List[str], reasons: List[str],
                     approved: bool, veto: bool = False,
                     member_weights: Optional[Dict] = None,
                     yes_weight: float = 0, total_weight: float = 0,
                     required: float = 0.6):
        """Store vote record in database."""
        record_id = f"vote_{int(time.time())}_{hash(proposal.get('id', ''))}"
        record = {
            'id': record_id,
            'type': 'VoteRecord',
            'proposal_id': proposal.get('id'),
            'timestamp': time.time(),
            'approved': approved,
            'veto': veto,
            'votes': dict(zip(self.MEMBERS, votes)),
            'reasons': dict(zip(self.MEMBERS, reasons)),
            'member_weights': member_weights,
            'yes_weight': yes_weight,
            'total_weight': total_weight,
            'required_threshold': required,
        }
        self.db.update_properties(record_id, record)
        # Link to proposal (if proposal has an ID)
        if proposal.get('id'):
            # We need a way to link; could be via edge but we'll just store reference.
            # For now, proposal_id is stored in record.
            pass
        self._last_record = record
        logger.info(f"Vote recorded: {record_id}")

    # -------------------------------------------------------------------------
    # Constitution management
    # -------------------------------------------------------------------------

    def amend_constitution(self, proposed_changes: Dict) -> Tuple[bool, str]:
        """
        Special procedure to amend constitution (requires supermajority of council).
        This is a meta‑governance function.
        """
        # This would be called by a special proposal type
        # For now, we return False; implement if needed.
        return False, "Not implemented"
