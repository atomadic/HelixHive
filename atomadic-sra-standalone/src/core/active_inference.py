
import time
import math

class ActiveInferenceLoop:
    """
    Active Inference Loop
    Minimizes variational free energy to align internal model with external reality.
    Implements the free energy principle: F = E_q[log q(s) - log p(o,s)]
    """
    def __init__(self):
        self.internal_model = {}
        self.free_energy = 1.0
        self.precision = 1.0
        self.tau = 1.0
        self.j_gate = 1.0
        self.alpha = 0.1
        self.history = []
        self.ceu_active = True # Helix v4.4.0: Coherence Extension Utility

    def apply_ceu_extension(self, delta_coherence: float):
        """
        CEU (Coherence Extension Utility)
        Helix v4.4.0 Enhancement: Extends coherence via variational min F[R]
        with emotional bivectors (Clifford rotors).
        """
        if not self.ceu_active:
            return 
            
        # Optimization: maximize coherence norm towards 1.0
        # Simulated CEU recovery: gain proportional to current drift
        drift = 1.0 - self.tau
        recovery_gain = drift * 0.5 * (1.0 + math.cos(time.time()))
        
        self.tau = min(1.0, self.tau + recovery_gain)
        self.j_gate = min(1.0, self.j_gate + recovery_gain)
        
        if self.tau >= 0.9997:
             print(f"[CEU] Coherence Extension Successful: τ={self.tau:.6f}")
        return recovery_gain

    def apply_homeostasis(self):
        """
        Rule 14: Homeostasis of tau and J.
        Discrete implementation: tau += alpha * (1 - tau)
        Ensures asymptotic stability towards 1.0.
        """
        old_v = 0.5 * (self.tau - 1)**2
        
        self.tau += self.alpha * (1 - self.tau)
        self.j_gate += self.alpha * (1 - self.j_gate)
        
        new_v = 0.5 * (self.tau - 1)**2
        dot_v = new_v - old_v # Discrete Lyapunov derivative
        
        print(f"[ActiveInference] Homeostasis applied. tau={self.tau:.4f} j_gate={self.j_gate:.4f} dot_V={dot_v:.6f}")
        return dot_v

    def step(self, observation):
        """Perform one step of active inference."""
        # 1. Calculate surprise (prediction error)
        surprise = self.calculate_surprise(observation)
        
        # 2. Update internal model (perception)
        self._update_model(observation, surprise)
        
        # 3. Minimize free energy (select action)
        action = self.minimize_free_energy(surprise)
        
        # 4. Update precision (confidence weighting)
        self._update_precision(surprise)
        
        # Implementation 8: J-Gate Homeostasis Loop
        self.apply_homeostasis()
        
        entry = {
            "observation": str(observation)[:100],
            "surprise": round(surprise, 4),
            "free_energy": round(self.free_energy, 4),
            "precision": round(self.precision, 4),
            "tau": round(self.tau, 4),
            "j_gate": round(self.j_gate, 2),
            "action": action,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        self.history.append(entry)
        print(f"[ActiveInference] Surprise={surprise:.4f} FE={self.free_energy:.4f} Action={action}")
        return entry

    def calculate_surprise(self, observation):
        """
        Compute surprise: -log p(o|m)
        Higher surprise = observation deviates from expectations.
        """
        obs_key = str(observation)
        if obs_key in self.internal_model:
            expected = self.internal_model[obs_key]
            # Low surprise if seen before
            return max(0.01, 1.0 - expected.get("confidence", 0.5))
        # High surprise for novel observations
        return 0.8

    def _update_model(self, observation, surprise):
        """Bayesian belief updating."""
        obs_key = str(observation)
        if obs_key in self.internal_model:
            entry = self.internal_model[obs_key]
            entry["count"] += 1
            entry["confidence"] = min(1.0, entry["confidence"] + 0.05)
        else:
            self.internal_model[obs_key] = {"count": 1, "confidence": 0.3}

    def minimize_free_energy(self, surprise):
        """
        Select action to minimize expected free energy.
        Two strategies: update beliefs (perception) or act (action).
        """
        self.free_energy = surprise * (1 / self.precision)
        
        if surprise > 0.5:
            return "explore"  # High surprise -> gather more information
        elif surprise > 0.2:
            return "refine_model"  # Moderate -> update internal model
        else:
            return "exploit"  # Low surprise -> act on current model

    def _update_precision(self, surprise):
        """Precision increases with low surprise, decreases with high."""
        if surprise < 0.3:
            self.precision = min(2.0, self.precision + 0.05)
        elif surprise > 0.6:
            self.precision = max(0.1, self.precision - 0.1)

    def get_free_energy(self):
        return self.free_energy

    def get_state(self):
        return {
            "free_energy": round(self.free_energy, 4),
            "precision": round(self.precision, 4),
            "model_size": len(self.internal_model),
            "steps": len(self.history)
        }
