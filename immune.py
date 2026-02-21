"""
Immune System for HelixHive Phase 2 – monitors agent health, detects anomalies,
and generates healing proposals for council consideration.
Focused on behavioral anomalies (high failures, low fitness) – low‑level Golay repair
is handled by the self‑repair engine.
"""

import logging
import time
from typing import List, Dict, Any, Optional
import numpy as np

from agent import Agent
from helixdb_git_adapter import HelixDBGit
from memory import LeechErrorCorrector

logger = logging.getLogger(__name__)


class ImmuneSystem:
    """
    Monitors agent health and generates healing proposals.
    """

    def __init__(self, db: HelixDBGit, genome: Any):
        self.db = db
        self.genome = genome
        # Load thresholds from genome
        self.failure_threshold = genome.data.get('immune', {}).get('failure_threshold', 5)
        self.anomaly_threshold = genome.data.get('immune', {}).get('anomaly_threshold', 2.0)
        self.healing_cooldown = genome.data.get('immune', {}).get('healing_cooldown', 3600)
        self.max_healing_proposals = genome.data.get('immune', {}).get('max_per_heartbeat', 3)

        # In-memory cache of last healing times (agent_id -> timestamp)
        self.last_healing = {}

    def run_check(self, agents: List[Agent]) -> List[Dict[str, Any]]:
        """
        Main entry point: check all agents and return a list of healing proposals.
        """
        proposals = []

        # Check failures
        fail_props = self._check_failures(agents)
        proposals.extend(fail_props)

        # Check anomalies (low fitness, etc.)
        anomaly_props = self._check_anomalies(agents)
        proposals.extend(anomaly_props)

        # Limit total proposals per heartbeat
        if len(proposals) > self.max_healing_proposals:
            logger.info(f"Immune system generated {len(proposals)} proposals, limiting to {self.max_healing_proposals}")
            proposals = proposals[:self.max_healing_proposals]

        return proposals

    def _check_failures(self, agents: List[Agent]) -> List[Dict[str, Any]]:
        """
        Identify agents with too many failures and generate healing proposals.
        """
        proposals = []
        now = time.time()
        for agent in agents:
            if agent.failures >= self.failure_threshold:
                # Check cooldown
                last = self.last_healing.get(agent.agent_id, 0)
                if now - last < self.healing_cooldown:
                    continue

                proposal = self._generate_healing_proposal(agent, reason=f"High failure count: {agent.failures}")
                proposals.append(proposal)
                self.last_healing[agent.agent_id] = now
                logger.info(f"Immune: healing proposal for {agent.agent_id} due to failures")
        return proposals

    def _check_anomalies(self, agents: List[Agent]) -> List[Dict[str, Any]]:
        """
        Detect agents with unusually low fitness or other behavioral anomalies.
        """
        if len(agents) < 3:
            return []

        # Compute average fitness from fitness history
        proposals = []
        now = time.time()
        for agent in agents:
            if not agent.fitness_history:
                continue
            # Get recent fitness (last 5)
            recent = [f['fitness'] for f in agent.fitness_history[-5:]]
            avg_fitness = sum(recent) / len(recent)
            if avg_fitness < 0.3:  # threshold
                # Check cooldown
                last = self.last_healing.get(agent.agent_id, 0)
                if now - last < self.healing_cooldown:
                    continue
                proposal = self._generate_healing_proposal(agent, reason=f"Low average fitness: {avg_fitness:.2f}")
                proposals.append(proposal)
                self.last_healing[agent.agent_id] = now
                logger.info(f"Immune: healing proposal for {agent.agent_id} due to low fitness")
        return proposals

    def _generate_healing_proposal(self, agent: Agent, reason: str) -> Dict[str, Any]:
        """
        Create a proposal to heal an agent.
        """
        # Simple healing: reset prompt to default and reduce failures
        default_prompt = self.genome.data.get('default_prompt', 'You are a helpful agent.')
        proposal = {
            'type': 'agent',
            'proposer_id': None,  # system-generated
            'description': f"Heal agent {agent.role} ({agent.agent_id[:8]}): {reason}",
            'tags': ['healing', 'immune'],
            'changes': {
                'agent_id': agent.agent_id,
                'prompt': default_prompt,
                # Optionally reset failures count (handled in application)
            },
            'timestamp': time.time()
        }
        return proposal


# -------------------------------------------------------------------------
# Standalone function for orchestrator
# -------------------------------------------------------------------------

def immune_check(db: HelixDBGit, agents: List[Agent], genome: Any) -> List[Dict]:
    """
    Run immune system check and return healing proposals.
    These proposals are added as nodes and will be processed by the proposals engine.
    """
    immune = ImmuneSystem(db, genome)
    proposals = immune.run_check(agents)

    # Add proposals to database as 'Proposal' nodes
    for prop in proposals:
        prop_id = f"heal_{int(time.time())}_{prop['changes']['agent_id'][-8:]}"
        prop['id'] = prop_id
        prop['status'] = 'pending'
        db.update_properties(prop_id, prop)
        logger.debug(f"Added healing proposal {prop_id}")

    return proposals
