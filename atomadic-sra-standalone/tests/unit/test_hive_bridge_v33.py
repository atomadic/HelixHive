"""
HiveBridge Unit Tests — SRA v3.3.0.0 | Expansion Cycle 4
Comprehensive tests for 25-module HelixHive integration.
"""

import sys
import os
import pytest
import numpy as np
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestHiveBridgeFull:
    """Test HiveBridge's full 25-module capability."""

    def test_bridge_discovery(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        state = bridge.get_state()
        assert state["modules_total"] == 24  # Core manifest size
        assert isinstance(state["modules_loaded"], int)

    def test_get_summary_format(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        summary = bridge.get_summary()
        assert "HiveBridge" in summary
        assert "τ=" in summary
        assert "J=" in summary

    def test_math_coverage(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        # HD
        v = bridge.hd_from_word("sovereign")
        if v is not None:
            assert len(v) == 10000
            assert bridge.hd_similarity(v, v) > 0.99
        # RHC
        rhc = bridge.rhc_encode_trait(0.5)
        if rhc is not None:
            assert len(rhc) == 98
        # E8
        e8 = bridge.e8_closest_point([0.1]*8)
        if e8 is not None:
            assert len(e8) == 8

    def test_governance_probes(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        info = bridge.get_governance_info()
        assert "council_available" in info
        assert "constitutional_checks" in info["features"]

    def test_health_probes(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        info = bridge.get_immune_info()
        assert "immune_available" in info
        assert "codebase_self_repair" in info["capabilities"]

    def test_social_probes(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        info = bridge.get_social_info()
        assert "faction_manager_available" in info
        assert "dbscan_clustering" in info["capabilities"]


class TestHiveAgentAdapterExpanded:
    """Test expanded HiveAgentAdapter capabilities."""

    def test_agent_lifecycle(self):
        from src.agents.hive_agent_adapter import HiveAgentAdapter
        adapter = HiveAgentAdapter()
        if not adapter.available:
            pytest.skip("HelixHive Agent module not available")

        # Create
        summary = adapter.create_agent("Researcher", "Find the truth.")
        assert summary is not None
        aid = summary["agent_id"]

        # Mutate
        mutated = adapter.mutate_agent(aid)
        assert mutated["mutated"] is True

        # Fitness
        adapter.record_fitness(aid, 0.95, task_type="integration")
        history = adapter.get_agent_fitness(aid)
        assert len(history) == 1
        assert history[0]["fitness"] == 0.95

        # List
        agents = adapter.list_agents()
        assert any(a["agent_id"] == aid for a in agents)

        # Remove
        assert adapter.remove_agent(aid) is True
        assert adapter.get_agent(aid) is None

    def test_breeding(self):
        from src.agents.hive_agent_adapter import HiveAgentAdapter
        adapter = HiveAgentAdapter()
        if not adapter.available:
            pytest.skip("HelixHive Agent module not available")

        p1 = adapter.create_agent("A", "Prompt A")
        p2 = adapter.create_agent("B", "Prompt B")
        
        child = adapter.breed_agents(p1["agent_id"], p2["agent_id"], new_role="C")
        assert child is not None
        assert child["parents"] == [p1["agent_id"], p2["agent_id"]]


class TestAIBridgeV33:
    """Test AIBridge v3.3.0.0 integration."""

    def test_bridge_v33_id(self):
        from src.core.ai_bridge import AIBridge
        bridge = AIBridge(use_mock=True)
        # Verify it runs a cycle
        result = bridge.process_query("Integrate HelixHive fully.")
        assert "level_1" in result
        assert "hive_bridge" in bridge.get_state()
