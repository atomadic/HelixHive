"""
Integration Test — SRA Full Pipeline Coherence
Validates end-to-end query processing through AIBridge with geometric coherence >= 0.92.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.ai_bridge import AIBridge, TAU_THRESHOLD, J_FLOOR


class TestPipelineIntegration:

    def _make_bridge(self):
        return AIBridge(use_mock=False, force_offline=True)

    # ---------------------------------------------------------------
    # Full pipeline tests
    # ---------------------------------------------------------------

    def test_process_query_returns_helical_json(self):
        """Rule 16: output must be helical JSON."""
        bridge = self._make_bridge()
        result = bridge.process_query("What is E8 lattice theory?")
        assert "level_1" in result
        assert "changelog" in result
        assert "principle" in result["level_1"]
        assert "audit" in result["level_1"]

    def test_coherence_above_threshold(self):
        """Geometric coherence must be >= 0.92."""
        bridge = self._make_bridge()
        result = bridge.process_query("Test coherence pipeline")
        coherence = result["level_1"]["audit"]["coherence"]
        assert coherence >= 0.92, f"Coherence {coherence} < 0.92"

    def test_tau_above_threshold(self):
        """Aletheia Axiom I: tau > 0.9412."""
        bridge = self._make_bridge()
        result = bridge.process_query("Test tau enforcement")
        tau = result["level_1"]["audit"]["tau"]
        assert tau >= TAU_THRESHOLD, f"tau {tau} < {TAU_THRESHOLD}"

    def test_jessica_gate_maintained(self):
        """Jessica Gate must remain >= 0.3."""
        bridge = self._make_bridge()
        result = bridge.process_query("Test J gate")
        j = result["level_1"]["audit"]["J"]
        assert j >= J_FLOOR, f"J {j} < {J_FLOOR}"

    def test_delta_m_positive(self):
        """Flipped Invariance: deltaM > 0."""
        bridge = self._make_bridge()
        result = bridge.process_query("Test deltaM enforcement")
        delta_m = result["changelog"]["deltaM"]
        assert delta_m > 0, f"deltaM {delta_m} <= 0"

    def test_multiple_cycles_stable(self):
        """System remains stable across 5 consecutive cycles."""
        bridge = self._make_bridge()
        for i in range(5):
            result = bridge.process_query(f"Stability test cycle {i}")
            assert "error" not in result, f"Error in cycle {i}: {result}"
            assert result["level_1"]["audit"]["tau"] >= TAU_THRESHOLD
            assert result["level_1"]["audit"]["J"] >= J_FLOOR
        assert bridge.cycle_count == 5
        assert bridge.wisdom_mass > 0

    def test_vault_logging(self):
        """Pipeline cycles are logged to Evolution Vault."""
        bridge = self._make_bridge()
        bridge.process_query("Vault logging test")
        recent = bridge.vault.get_recent("evolutions", n=1)
        assert len(recent) >= 1
        assert "Pipeline Cycle" in recent[-1].get("title", "")

    def test_get_state_complete(self):
        """Bridge state contains all diagnostic fields."""
        bridge = self._make_bridge()
        bridge.process_query("State test")
        state = bridge.get_state()
        assert "tau" in state
        assert "J" in state
        assert "wisdom_mass" in state
        assert "cycles" in state
        assert "e8_coherence" in state
        assert "inference" in state
        assert "hott" in state
        assert "leech" in state

    def test_audit_output(self):
        """Audit gate validates tau/J/deltaM."""
        bridge = self._make_bridge()
        bridge.process_query("Audit test")
        audit = bridge.audit_output({})
        assert audit["passed"] is True
        assert audit["tau_ok"] is True
        assert audit["j_ok"] is True
        assert audit["delta_m_ok"] is True

    def test_route_to_panel(self):
        """Panel routing returns expected structure."""
        bridge = self._make_bridge()
        result = bridge.route_to_panel("code_creation", {"task": "generate"})
        assert result["panel"] == "code_creation"
        assert result["status"] == "routed"

    def test_fallback_response_when_offline(self):
        """Force-offline bridge produces fallback response."""
        bridge = self._make_bridge()
        result = bridge.process_query("Offline test query")
        impl = result["level_1"]["impl"]
        assert impl["source"] == "fallback"
        assert "SRA-Fallback" in impl["content"]
