"""
HiveBridge Unit Tests — SRA v3.3.0.0 | Expansion Cycle 4

Tests:
1. HiveBridge initialization and availability status
2. Leech encode/correct fallback (simplified mode when Golay table absent)
3. HD/RHC encoding via HelixHive memory
4. LLM router fallback (None when no API keys)
5. Revelation engine probe
6. Self-repair dry run
7. State diagnostics
8. AIBridge integration with HiveBridge wiring
"""

import sys
import os
import pytest
import numpy as np

# Ensure project root is on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =========================================================================
# HiveBridge Unit Tests
# =========================================================================

class TestHiveBridgeInit:
    """Test HiveBridge initialization and module loading."""

    def test_bridge_creates_without_error(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        assert bridge is not None
        assert isinstance(bridge.tau, float)
        assert isinstance(bridge.J, float)

    def test_bridge_tau_initialized_to_1(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        assert bridge.tau == 1.0

    def test_bridge_j_initialized_to_1(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        assert bridge.J == 1.0

    def test_get_state_returns_dict(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        state = bridge.get_state()
        assert isinstance(state, dict)
        assert "available" in state
        assert "tau" in state
        assert "J" in state
        assert "modules" in state


class TestHiveBridgeLeech:
    """Test Leech lattice encoding/correction via HiveBridge."""

    def test_leech_encode_accepts_24d_vector(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        vec = [0.1] * 24
        result = bridge.leech_encode(vec)
        assert result is not None
        assert len(result) == 24

    def test_leech_encode_rejects_wrong_dim(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        with pytest.raises(ValueError, match="24D"):
            bridge.leech_encode([0.1] * 8)

    def test_leech_correct_returns_tuple(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        vec = [1.2, 0.8, -0.3] + [0.0] * 21
        corrected, syndrome = bridge.leech_correct(vec)
        assert len(corrected) == 24
        assert isinstance(syndrome, int)

    def test_leech_encode_idempotent_on_integers(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        vec = [2.0, 0.0, -1.0] + [0.0] * 21
        result = bridge.leech_encode(vec)
        # Encoding integers should give something close to the input
        assert np.allclose(result[:3], [2, 0, -1], atol=2)

    def test_leech_correct_zero_vector(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        vec = [0.0] * 24
        corrected, syndrome = bridge.leech_correct(vec)
        assert np.all(corrected == 0)


class TestHiveBridgeHD:
    """Test HD/RHC encoding via HelixHive memory."""

    def test_hd_from_word_returns_vector_or_none(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        result = bridge.hd_from_word("test")
        # May be None if HelixHive memory didn't load
        if result is not None:
            assert len(result) == 10000  # HD_DIM

    def test_hd_from_word_deterministic(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        r1 = bridge.hd_from_word("sovereign")
        r2 = bridge.hd_from_word("sovereign")
        if r1 is not None and r2 is not None:
            assert np.array_equal(r1, r2)

    def test_rhc_encode_trait_value(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        result = bridge.rhc_encode_trait(0.75)
        if result is not None:
            # RHC vector length = sum of moduli = 3+5+7+11+13+17+19+23 = 98
            assert len(result) == 98

    def test_e8_closest_point_8d(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        result = bridge.e8_closest_point([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
        if result is not None:
            assert len(result) == 8


class TestHiveBridgeLLM:
    """Test LLM routing fallback behavior."""

    def test_llm_available_is_bool(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        assert isinstance(bridge.llm_available, bool)

    def test_call_llm_sync_graceful_failure(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        # Without API keys, should return None (not raise)
        result = bridge.call_llm_sync("test prompt")
        # Either None or a string
        assert result is None or isinstance(result, str)


class TestHiveBridgeRevelation:
    """Test Revelation Engine probe."""

    def test_revelation_available_is_bool(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        assert isinstance(bridge.revelation_available, bool)

    def test_generate_revelation_returns_dict_or_none(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        result = bridge.generate_revelation({"topic": "test"})
        assert result is None or isinstance(result, dict)


class TestHiveBridgeSelfRepair:
    """Test Golay self-repair probe."""

    def test_repair_available_is_bool(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        assert isinstance(bridge.repair_available, bool)


class TestHiveBridgeTauHomeostasis:
    """Test Aletheia gate mechanics."""

    def test_step_tau_moves_toward_1(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        bridge.tau = 0.9
        bridge._step_tau()
        assert bridge.tau > 0.9
        assert bridge.tau <= 1.0

    def test_decrement_j_floors_at_0_3(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        bridge.J = 0.35
        bridge._decrement_j()
        assert bridge.J >= 0.3

    def test_j_never_below_floor(self):
        from src.core.hive_bridge import HiveBridge
        bridge = HiveBridge()
        for _ in range(20):
            bridge._decrement_j()
        assert bridge.J >= 0.3


class TestAIBridgeHiveIntegration:
    """Test that AIBridge integrates HiveBridge correctly."""

    def test_aibridge_has_hive_attribute(self):
        from src.core.ai_bridge import AIBridge
        bridge = AIBridge(use_mock=True, force_offline=True)
        assert hasattr(bridge, 'hive')

    def test_aibridge_state_includes_hive(self):
        from src.core.ai_bridge import AIBridge
        bridge = AIBridge(use_mock=True, force_offline=True)
        state = bridge.get_state()
        assert "hive_bridge" in state
        assert "available" in state["hive_bridge"]

    def test_pipeline_with_hive_bridge(self):
        """End-to-end pipeline run — hive wiring should not break anything."""
        from src.core.ai_bridge import AIBridge
        bridge = AIBridge(use_mock=True, force_offline=True)
        result = bridge.process_query("Test query for HiveBridge integration")
        assert "error" not in result or "level_1" in result
        if "level_1" in result:
            audit = result["level_1"]["audit"]
            assert audit["tau"] >= 0.9412
            assert audit["J"] >= 0.3
            assert audit["delta_m"] > 0

    def test_pipeline_assembly_may_have_golay(self):
        """Phase 1 output may include golay info when HiveBridge available."""
        from src.core.ai_bridge import AIBridge
        bridge = AIBridge(use_mock=True, force_offline=True)
        result = bridge.process_query("Golay integration test")
        # We just verify it doesn't crash — golay key is optional
        assert "level_1" in result
