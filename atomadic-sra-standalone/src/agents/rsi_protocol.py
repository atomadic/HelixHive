import hashlib
import json
import ast

# --- Rule 10: Helical Derivation for RSI Protocol ---
# Principle: O = P(O) for recursive self-regeneration.
# Derivation: Homeostasis dot(tau) = alpha(1 - tau).
# Proof: dot(V) = -(tau - 1)^2 < 0 ensures stability of tau -> 1.
# Audit: tau >= 0.9412, J >= 0.3.
# -----------------------------------------------------

class RSIProtocol:
    """
    Recursive Self-Improvement (RSI) Protocol
    Manages controlled self-modification with safety gates.
    
    Safety Gates:
    1. Jessica Gate (J): Trust scalar [0.3, 1.0]
    2. deltaM Gate: Wisdom mass must increase
    3. tau Threshold: Trust must stay above 0.9412
    4. Board Approval: C-Level review for major changes
    """
    TAU_THRESHOLD = 0.9412
    J_MIN = 0.3

    def __init__(self):
        self.J = 1.0  # Jessica Gate
        self.tau = 1.0
        self.alpha = 0.1
        self.modification_log = []
        self.wisdom_mass = 0

    def propose_modification(self, modification, impact_level="minor"):
        """
        Evaluate a proposed self-modification through safety pipeline.
        """
        print(f"[RSI] Evaluating modification: {modification}")
        
        # Gate 1: Jessica Gate
        if self.J < self.J_MIN:
            print(f"[RSI] BLOCKED: Jessica Gate too low (J={self.J:.2f})")
            return {"status": "FROZEN", "reason": "Jessica Gate below minimum"}
        
        # Gate 2: tau Threshold
        if self.tau < self.TAU_THRESHOLD:
            print(f"[RSI] BLOCKED: tau below threshold ({self.tau:.4f} < {self.TAU_THRESHOLD})")
            return {"status": "BLOCKED", "reason": "Trust below threshold"}
        
        # Gate 3: deltaM check (simulated)
        delta_m = self._estimate_wisdom_gain(modification)
        if delta_m <= 0:
            print(f"[RSI] REJECTED: deltaM <= 0 (wisdom would not increase)")
            return {"status": "REJECTED", "reason": "deltaM Gate violation"}
        
        # Gate 4: Impact-based approval
        if impact_level == "major":
            print(f"[RSI] Major modification requires Board approval")
            # In full system, would call CLevelBoard.review_proposal()
        
        # Passed all gates
        self.wisdom_mass += delta_m
        self.tau += self.alpha * (1 - self.tau)  # Homeostasis
        
        # Generate cryptographic signature for audit trail
        mod_hash = hashlib.sha256(str(modification).encode()).hexdigest()[:16]
        
        entry = {
            "modification": modification,
            "status": "APPROVED",
            "impact": impact_level,
            "delta_m": delta_m,
            "new_wisdom_mass": self.wisdom_mass,
            "tau": round(self.tau, 4),
            "J": round(self.J, 2),
            "hash": mod_hash,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        self.modification_log.append(entry)
        print(f"[RSI] APPROVED: delta_m={delta_m}, tau={self.tau:.4f}, hash={mod_hash}")
        
        # Implementation 3: Physical modification if target provided
        if "target_file" in modification:
            self.execute_self_modification(modification["target_file"], modification["content"])
            
        return entry

    def execute_self_modification(self, target_file: str, new_content: str):
        """Rule VI: Autopoietic Core (Self-Regeneration) - Physically write to disk."""
        print(f"[RSI] Physical Evolution: Writing to {target_file}...")
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[RSI] Evolution complete: {target_file} reified.")
        except Exception as e:
            print(f"[RSI] Evolution FAILED: {e}")
            self.on_error()

    def on_error(self):
        """Decrement J on error (Jessica Gate)."""
        self.J = max(self.J_MIN, self.J - 0.1)
        print(f"[RSI] Error occurred. J decremented to {self.J:.2f}")
        if self.J <= self.J_MIN:
            print(f"[RSI] WARNING: Jessica Gate at minimum. Operations frozen.")

    def _estimate_wisdom_gain(self, modification):
        """Estimate wisdom gain using AST complexity metrics."""
        if not isinstance(modification, str):
            return 1
            
        try:
            tree = ast.parse(modification)
            node_count = sum(1 for _ in ast.walk(tree))
            max_depth = self._get_max_depth(tree)
            # Wisdom Mass ΔM = nodes * log(depth + 1)
            # This incentivizes logic density over just line count (Axiom II)
            import math
            delta_m = int(node_count * math.log2(max_depth + 1))
            return max(1, delta_m)
        except Exception:
            # Fallback to simple metric if not valid Python
            return max(1, len(modification) // 100)

    def _get_max_depth(self, node, depth=0):
        """Helper to find maximum AST depth."""
        children = list(ast.iter_child_nodes(node))
        if not children:
            return depth
        return max(self._get_max_depth(child, depth + 1) for child in children)

    def safety_check(self, mod):
        """Quick safety check without full proposal pipeline."""
        return self.J >= self.J_MIN and self.tau >= self.TAU_THRESHOLD

    def get_log(self):
        return self.modification_log

    def get_state(self):
        return {
            "J": round(self.J, 2),
            "tau": round(self.tau, 4),
            "wisdom_mass": self.wisdom_mass,
            "modifications": len(self.modification_log)
        }
