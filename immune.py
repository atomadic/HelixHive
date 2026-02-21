"""
Immune System for HelixHive – monitors agent health, detects anomalies,
and generates healing proposals.
"""

import logging
import time
from typing import List, Dict, Any, Optional
import numpy as np

from agent import Agent
import helixdb
from memory import LeechProjection

logger = logging.getLogger(__name__)


class ImmuneSystem:
    """
    Monitors agent health and generates healing proposals.
    """

    def __init__(self, db: 'helixdb.HelixDB', genome: Any):
        self.db = db
        self.genome = genome
        # Load thresholds from genome
        self.failure_threshold = genome.data.get('immune', {}).get('failure_threshold', 5)
        self.anomaly_threshold = genome.data.get('immune', {}).get('anomaly_threshold', 2.0)  # std deviations
        self.healing_cooldown = genome.data.get('immune', {}).get('healing_cooldown', 3600)  # seconds
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

        # Check anomalies
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

                # Generate proposal
                proposal = self._generate_healing_proposal(agent, reason=f"High failure count: {agent.failures}")
                proposals.append(proposal)
                self.last_healing[agent.agent_id] = now
                logger.info(f"Immune: generated healing proposal for agent {agent.agent_id} due to failures")
        return proposals

    def _check_anomalies(self, agents: List[Agent]) -> List[Dict[str, Any]]:
        """
        Detect agents whose Leech vector deviates significantly from the population centroid.
        """
        if len(agents) < 3:
            return []  # Not enough agents for meaningful anomaly detection

        # Collect Leech vectors
        leech_vecs = []
        valid_agents = []
        for agent in agents:
            vec = agent.leech_vec
            if vec is not None:
                leech_vecs.append(vec)
                valid_agents.append(agent)

        if len(valid_agents) < 3:
            return []

        # Compute centroid (mean)
        centroid = np.mean(leech_vecs, axis=0)

        # Compute distances and standard deviation
        distances = [np.linalg.norm(v - centroid) for v in leech_vecs]
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)

        if std_dist == 0:
            return []

        proposals = []
        now = time.time()
        for agent, vec, dist in zip(valid_agents, leech_vecs, distances):
            z_score = (dist - mean_dist) / std_dist
            if z_score > self.anomaly_threshold:
                # Check cooldown
                last = self.last_healing.get(agent.agent_id, 0)
                if now - last < self.healing_cooldown:
                    continue

                proposal = self._generate_healing_proposal(
                    agent,
                    reason=f"Anomalous Leech vector (z-score: {z_score:.2f})"
                )
                proposals.append(proposal)
                self.last_healing[agent.agent_id] = now
                logger.info(f"Immune: generated healing proposal for agent {agent.agent_id} due to anomaly")

        return proposals

    def _generate_healing_proposal(self, agent: Agent, reason: str) -> Dict[str, Any]:
        """
        Create a proposal to heal an agent.
        The proposal will be added to the blackboard for council consideration.
        """
        # Simple healing: reset prompt to default (from genome) and reduce failures
        default_prompt = self.genome.data.get('default_prompt', 'You are a helpful agent.')
        proposal = {
            'type': 'agent',
            'proposer_id': None,  # system-generated
            'description': f"Heal agent {agent.role} ({agent.agent_id[:8]}): {reason}",
            'tags': ['healing', 'immune'],
            'changes': {
                'agent_id': agent.agent_id,
                'prompt': default_prompt,
                'traits': agent.traits,  # keep traits? Or reset to defaults? We'll keep traits.
                # Optionally reset failures count
            },
            # We'll also include a note to reset failures after approval (handled in proposal application)
        }
        return proposal


# Standalone function for orchestrator to call
def immune_check(db: 'helixdb.HelixDB', agents: List[Agent], genome: Any) -> List[Dict]:
    """
    Run immune system check and return healing proposals.
    These proposals should be added to the blackboard for processing in the next heartbeat.
    """
    immune = ImmuneSystem(db, genome)
    proposals = immune.run_check(agents)

    # Add proposals to blackboard (as messages)
    for prop in proposals:
        # Create a message node in HelixDB
        msg_id = db.add_node(
            label='Message',
            properties={
                'type': 'proposal',
                'agent_id': None,
                'text': prop['description'],
                'phase': genome.data.get('helicity', {}).get('current_phase', 0),
                'timestamp': time.time(),
                'proposal_data': prop  # store the actual proposal
            }
        )
        logger.debug(f"Added healing proposal as message {msg_id}")

    return proposals
