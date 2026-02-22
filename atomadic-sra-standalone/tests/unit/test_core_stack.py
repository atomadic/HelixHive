"""
Unit Tests — SRA Core Geometric Stack
Tests E8Core, LeechOuter, CliffordRotors, FormalPrecisionLayer, ActiveInferenceLoop.
Validates Aletheia Axioms: tau >= 0.9412, deltaM > 0, coherence >= 0.92.
"""

import sys
import os
import math

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.e8_core import E8Core
from src.core.leech_outer import LeechOuter
from src.core.clifford_rotors import CliffordRotors
from src.core.formal_precision import FormalPrecisionLayer
from src.core.active_inference import ActiveInferenceLoop


# ═══════════════════════════════════════════════════════════════════════
# E8Core Tests
# ═══════════════════════════════════════════════════════════════════════

class TestE8Core:

    def test_init_defaults(self):
        core = E8Core()
        assert core.tau == 1.0
        assert core.coherence == 1.0
        assert len(core.lattice_matrix) == 8
        assert len(core.lattice_matrix[0]) == 8

    def test_project_to_e8_quantizes(self):
        core = E8Core()
        vec = [1.4, 2.6, -0.3, 0.7, 3.14, -1.9, 0.0, 5.5]
        proj = core.project_to_e8(vec)
        assert proj == [1, 3, 0, 1, 3, -2, 0, 6]  # rounded

    def test_project_to_e8_truncates_to_8d(self):
        core = E8Core()
        vec = list(range(20))
        proj = core.project_to_e8(vec)
        assert len(proj) == 8

    def test_step_tau_homeostasis(self):
        """tau += alpha*(1-tau) → converges to 1.0."""
        core = E8Core()
        core.tau = 0.5
        for _ in range(50):
            core.step_tau()
        assert core.tau > 0.99

    def test_step_tau_stays_at_one(self):
        core = E8Core()
        core.step_tau()
        assert core.tau == 1.0

    def test_optimize_system_geometry(self):
        core = E8Core()
        result = core.optimize_system_geometry()
        assert result["status"] == "OPTIMIZED"
        assert result["coherence"] >= 1.0
        assert "entropy" in result

    def test_field_resonance_identical_vectors(self):
        core = E8Core()
        v = [1.0, 0.0, 0.0, 0.0]
        assert core.compute_field_resonance(v, v) == 1.0

    def test_field_resonance_orthogonal_vectors(self):
        core = E8Core()
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert core.compute_field_resonance(a, b) == 0.0

    def test_field_resonance_zero_vector(self):
        core = E8Core()
        a = [0.0, 0.0]
        b = [1.0, 0.0]
        assert core.compute_field_resonance(a, b) == 0.0

    def test_resonance_cache_works(self):
        core = E8Core()
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        r1 = core.compute_field_resonance(a, b)
        r2 = core.compute_field_resonance(a, b)
        assert r1 == r2
        assert len(core._resonance_cache) >= 1


# ═══════════════════════════════════════════════════════════════════════
# LeechOuter Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeechOuter:

    def test_init(self):
        leech = LeechOuter()
        assert leech.DIMENSION == 24
        assert len(leech.reasoning_traces) == 0

    def test_explore_returns_trace(self):
        leech = LeechOuter()
        trace = leech.explore("quantum computing")
        assert "id" in trace
        assert "vector" in trace
        assert len(trace["vector"]) == 24
        assert "quantum computing" in leech.concept_space

    def test_explore_increments_traces(self):
        leech = LeechOuter()
        leech.explore("concept_a")
        leech.explore("concept_b")
        assert len(leech.reasoning_traces) == 2

    def test_compress_trace(self):
        leech = LeechOuter()
        trace = leech.explore("test concept")
        compressed = leech.compress_trace(trace)
        assert compressed["original_dim"] == 24
        assert "quantized_vector" in compressed
        assert "fidelity" in compressed

    def test_project_to_24d_normalized(self):
        leech = LeechOuter()
        vec = leech._project_to_24d("any text here")
        norm = math.sqrt(sum(v**2 for v in vec))
        assert abs(norm - 1.0) < 0.01

    def test_creative_connections(self):
        leech = LeechOuter()
        result = leech.find_creative_connections("alpha", "beta")
        assert "similarity" in result
        assert "connection_strength" in result
        assert -1.0 <= result["similarity"] <= 1.0

    def test_get_stats(self):
        leech = LeechOuter()
        leech.explore("x")
        stats = leech.get_stats()
        assert stats["traces"] == 1
        assert stats["concepts"] == 1
        assert stats["dimension"] == 24


# ═══════════════════════════════════════════════════════════════════════
# CliffordRotors Tests  
# ═══════════════════════════════════════════════════════════════════════

class TestCliffordRotors:

    def test_init(self):
        cr = CliffordRotors()
        assert cr.dimension == 8
        assert len(cr.basis) == 8

    def test_inner_product(self):
        cr = CliffordRotors()
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        assert cr.inner_product(a, b) == 32.0

    def test_outer_product_antisymmetric(self):
        cr = CliffordRotors()
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        wp = cr.outer_product(a, b)
        assert len(wp) == 1
        assert wp[0] == 1.0  # a1*b2 - a2*b1

    def test_geometric_product_structure(self):
        cr = CliffordRotors()
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        gp = cr.geometric_product(a, b)
        assert "inner" in gp
        assert "outer" in gp
        assert "result" in gp

    def test_transform_identity(self):
        cr = CliffordRotors()
        v = [1.0, 0.0, 0.0, 0.0]
        result = cr.transform(v, [0.0])  # zero angle = identity
        assert abs(result[0] - 1.0) < 1e-6
        assert abs(result[1] - 0.0) < 1e-6

    def test_map_analogy_same_vectors(self):
        cr = CliffordRotors()
        v = [1.0, 0.0, 0.0]
        result = cr.map_analogy(v, v)
        assert result["angle"] == 0.0
        assert result["similarity"] == 1.0

    def test_compute_distance_zero(self):
        cr = CliffordRotors()
        v = [1.0, 2.0, 3.0]
        assert cr.compute_distance(v, v) == 0.0

    def test_check_coherence_single_vector(self):
        cr = CliffordRotors()
        assert cr.check_coherence([[1.0, 0.0]]) == 1.0

    def test_check_coherence_aligned(self):
        cr = CliffordRotors()
        vectors = [[1.0, 0.0], [2.0, 0.0], [3.0, 0.0]]
        assert cr.check_coherence(vectors) == 1.0

    def test_check_coherence_range(self):
        cr = CliffordRotors()
        vectors = [[1.0, 0.0], [0.0, 1.0]]
        c = cr.check_coherence(vectors)
        assert 0.0 <= c <= 1.0


# ═══════════════════════════════════════════════════════════════════════
# FormalPrecisionLayer Tests
# ═══════════════════════════════════════════════════════════════════════

class TestFormalPrecisionLayer:

    def test_init(self):
        fpl = FormalPrecisionLayer()
        assert fpl.get_verified_count() == 0

    def test_verify_valid_proof(self):
        fpl = FormalPrecisionLayer()
        proof = {
            "name": "test_proof",
            "hypothesis": "A implies B",
            "conclusion": "B",
            "steps": [
                {"type": "modus_ponens", "term": "A -> B"},
                {"type": "apply", "term": "A"},
            ]
        }
        result = fpl.verify_proof(proof)
        assert result["verified"] is True
        assert fpl.get_verified_count() == 1

    def test_verify_invalid_proof(self):
        fpl = FormalPrecisionLayer()
        proof = {"name": "bad_proof"}  # missing hypothesis & conclusion
        result = fpl.verify_proof(proof)
        assert result["verified"] is False

    def test_define_type(self):
        fpl = FormalPrecisionLayer()
        t = fpl.define_type("NatType", {"constructor": "succ", "base": "zero"})
        assert t["level"] == 0
        assert "NatType" in fpl.type_universe

    def test_check_equivalence_same(self):
        fpl = FormalPrecisionLayer()
        fpl.define_type("A", {"kind": "product"})
        fpl.define_type("B", {"kind": "product"})
        assert fpl.check_equivalence("A", "B") is True

    def test_check_equivalence_different(self):
        fpl = FormalPrecisionLayer()
        fpl.define_type("A", {"kind": "product"})
        fpl.define_type("B", {"kind": "sum"})
        assert fpl.check_equivalence("A", "B") is False

    def test_check_continuity(self):
        fpl = FormalPrecisionLayer()
        spec = {"domain": "Nat", "codomain": "Nat"}
        result = fpl.check_continuity(spec)
        assert result["continuous"] is True

    def test_get_state(self):
        fpl = FormalPrecisionLayer()
        fpl.define_type("X", {})
        state = fpl.get_state()
        assert state["types_registered"] == 1


# ═══════════════════════════════════════════════════════════════════════
# ActiveInferenceLoop Tests
# ═══════════════════════════════════════════════════════════════════════

class TestActiveInferenceLoop:

    def test_init(self):
        loop = ActiveInferenceLoop()
        assert loop.free_energy == 1.0
        assert loop.precision == 1.0
        assert len(loop.history) == 0

    def test_step_returns_entry(self):
        loop = ActiveInferenceLoop()
        entry = loop.step("test observation")
        assert "surprise" in entry
        assert "free_energy" in entry
        assert "action" in entry
        assert len(loop.history) == 1

    def test_novel_observation_high_surprise(self):
        loop = ActiveInferenceLoop()
        entry = loop.step("novel_input")
        assert entry["surprise"] >= 0.5

    def test_repeated_observation_low_surprise(self):
        loop = ActiveInferenceLoop()
        # Confidence accumulates at +0.05/step; need ~10 reps for surprise < 0.5
        for _ in range(12):
            loop.step("repeated")
        entry = loop.step("repeated")
        assert entry["surprise"] < 0.5

    def test_free_energy_decreases_with_learning(self):
        loop = ActiveInferenceLoop()
        e1 = loop.step("concept")
        e2 = loop.step("concept")
        assert e2["free_energy"] <= e1["free_energy"]

    def test_explore_action_on_high_surprise(self):
        loop = ActiveInferenceLoop()
        entry = loop.step("completely_new_thing")
        assert entry["action"] == "explore"

    def test_get_state(self):
        loop = ActiveInferenceLoop()
        loop.step("x")
        state = loop.get_state()
        assert state["steps"] == 1
        assert state["model_size"] == 1
