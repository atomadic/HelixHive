
import time

class GoalEngine:
    """
    Goal Engine
    Hierarchical goal/sub-goal tracking with alignment verification.
    Maintains a tree of goals and ensures all actions align with root objectives.
    Includes ML-based Gradient Goal Alignment (GDGA).
    """
    def __init__(self):
        self.goals = []
        self.goal_tree = {}
        self.alignment_log = []

    def add_goal(self, goal, parent_id=None):
        """Add a goal. If parent_id given, it becomes a sub-goal."""
        goal_id = f"G-{len(self.goals):04d}"
        goal_entry = {
            "id": goal_id,
            "title": goal,
            "status": "active",
            "parent_id": parent_id,
            "sub_goals": [],
            "progress": 0.0,
            "priority": 1.0,
            "created": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        self.goals.append(goal_entry)
        
        if parent_id:
            for g in self.goals:
                if g["id"] == parent_id:
                    g["sub_goals"].append(goal_id)
                    break
        
        print(f"[GoalEngine] Added: {goal_id} -- {goal}")
        return goal_entry

    def update_progress(self, goal_id, progress):
        """Update goal progress (0.0 to 1.0)."""
        for g in self.goals:
            if g["id"] == goal_id:
                g["progress"] = min(1.0, max(0.0, progress))
                if g["progress"] >= 1.0:
                    g["status"] = "completed"
                print(f"[GoalEngine] {goal_id} progress: {g['progress']:.0%}")
                if g["parent_id"]:
                    self._propagate_progress(g["parent_id"])
                return g
        return None

    def _propagate_progress(self, parent_id):
        """Recalculate parent progress from sub-goals."""
        for g in self.goals:
            if g["id"] == parent_id and g["sub_goals"]:
                sub_progress = []
                for sg_id in g["sub_goals"]:
                    for sg in self.goals:
                        if sg["id"] == sg_id:
                            sub_progress.append(sg["progress"])
                if sub_progress:
                    g["progress"] = sum(sub_progress) / len(sub_progress)

    def check_alignment(self, action, context=None):
        """Check if an action aligns with active goals."""
        if not self.goals:
            return 1.0
        
        active_goals = self.get_active_goals()
        if not active_goals:
            return 1.0
        
        action_lower = str(action).lower()
        matches = 0
        for g in active_goals:
            # Weight by priority
            words = g["title"].lower().split()
            if any(w in action_lower for w in words):
                matches += g.get("priority", 1.0)
        
        score = min(1.0, 0.5 + (matches / len(active_goals)) * 0.5)
        
        self.alignment_log.append({
            "action": action,
            "score": round(score, 4),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        })
        
        print(f"[GoalEngine] Alignment for '{action}': {score:.2f}")
        return score

    def detect_logic_drift(self, agent_name, thoughts, threshold=0.3):
        """Logic Drift Detection (OPT-003)."""
        if not self.goals: return 0.0
        active_goals = self.get_active_goals()
        if not active_goals: return 0.0
        
        resonance = 0.0
        thought_text = " ".join([t.get("thought", "") for t in thoughts]).lower()
        for g in active_goals:
            if any(w in thought_text for w in g["title"].lower().split()):
                resonance += 1
        
        drift = 1.0 - (resonance / len(active_goals) if active_goals else 1.0)
        if drift >= threshold:
            print(f"[GoalEngine] CRITICAL DRIFT in {agent_name}: {drift:.2f}")
        return drift

    def apply_gdga(self, goal_id, reward_signal):
        """Gradient Goal Alignment (NOV-005)."""
        for g in self.goals:
            if g["id"] == goal_id:
                # Signal 0.0 to 1.0; adjust priority
                g["priority"] = g.get("priority", 1.0) + (reward_signal - 0.5) * 0.1
                print(f"[GoalEngine] GDGA refined priority for {goal_id}: {g['priority']:.4f}")
                return g
        return None

    def get_active_goals(self):
        return [g for g in self.goals if g["status"] == "active"]

    def get_all_goals(self):
        return self.goals
