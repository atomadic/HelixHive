"""
Super-Panel Orchestration — Cycle 20
Implements recursive multi-agent deliberation with Advisor/Council/Adversary layers.
SRA v4.4.2.0 | HelixEvolver Autopoiesis
"""

import os
import sys
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

# Project root for safe imports
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.core.ai_bridge import AIBridge

logger = logging.getLogger("SuperPanel")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(_ROOT / "data" / "sra_master.log"),
        logging.StreamHandler()
    ]
)

def log_audit(event_type: str, data: Dict[str, Any]):
    """Log structured events for the UI viewer."""
    log_file = _ROOT / "data" / "deliberation_audit.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": str(asyncio.get_event_loop().time()), "event": event_type, **data}) + "\n")

class Luminary:
    def __init__(self, name: str, prompt_file: str, bridge: AIBridge):
        self.name = name
        self.prompt_file = prompt_file
        self.bridge = bridge
        self.base_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        p = _ROOT / self.prompt_file
        if p.exists():
            return p.read_text(encoding="utf-8")
        return f"You are {self.name}, a specialized SRA luminary agent."

    async def deliberate(self, query: str, context: str = "", retries: int = 3) -> str:
        system = f"{self.base_prompt}\n\nTask: {query}\n\nContext: {context}"
        log_audit("luminary_deliberation_start", {"luminary": self.name, "query": query})
        
        response = None
        for attempt in range(retries):
            try:
                # Priority: Cloud (Hive) -> Local (Ollama)
                if self.bridge.hive.llm_available:
                    response = await self.bridge.hive.call_llm(query, system=system)
                
                if not response:
                    response = self.bridge.llm.generate_completion(query, system)
                
                if response:
                    break
                logger.warning(f"[{self.name}] Attempt {attempt+1} failed. Retrying...")
                await asyncio.sleep(1) # Backoff
            except Exception as e:
                logger.error(f"[{self.name}] Error on attempt {attempt+1}: {e}")
                await asyncio.sleep(2)
            
        if response:
            log_audit("luminary_deliberation_success", {"luminary": self.name, "response_len": len(response)})
        else:
            log_audit("luminary_deliberation_failure", {"luminary": self.name})
            
        return response or "[Error: Deliberation Failed]"

class SupportRole:
    def __init__(self, role_type: str, luminary_name: str, bridge: AIBridge):
        self.role_type = role_type # Advisor, Council, Adversary
        self.luminary_name = luminary_name
        self.bridge = bridge

    async def evaluate(self, luminary_response: str, query: str, retries: int = 2) -> str:
        prompts = {
            "Advisor": f"You are the Advisor for {self.luminary_name}. Provide best practices and historical precedents for this response: {luminary_response}",
            "Council": f"You are the Council for {self.luminary_name}. Perform a feasibility check and collective alignment audit for: {luminary_response}",
            "Adversary": f"You are the Adversary for {self.luminary_name}. Critically critique and find flaws/counterfactuals in: {luminary_response}. Be harsh and precise."
        }
        system = "You are a specialized support role in the SRA Super-Panel deliberation substrate."
        prompt = prompts.get(self.role_type, "Provide feedback.")
        
        log_audit("support_role_evaluation_start", {"luminary": self.luminary_name, "role": self.role_type})
        
        response = None
        for attempt in range(retries):
            try:
                # Priority: Cloud (Hive) -> Local (Ollama)
                if self.bridge.hive.llm_available:
                    response = await self.bridge.hive.call_llm(prompt, system=system)
                    
                if not response:
                    response = self.bridge.llm.generate_completion(prompt, system)
                
                if response:
                    break
                logger.warning(f"[{self.luminary_name}:{self.role_type}] Attempt {attempt+1} failed. Retrying...")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"[{self.luminary_name}:{self.role_type}] Error: {e}")
                await asyncio.sleep(1)

        if response:
            log_audit("support_role_evaluation_success", {"luminary": self.luminary_name, "role": self.role_type})
        else:
            log_audit("support_role_evaluation_failure", {"luminary": self.luminary_name, "role": self.role_type})
            
        return response or "[Support Role Offline]"

class SuperPanel:
    def __init__(self):
        self.bridge = AIBridge()
        self.luminaries = [
            Luminary("SRA-Blueprint", "sra-blueprint.md", self.bridge),
            Luminary("SRA-Code-Architect", "sra-code-architect.md", self.bridge),
            Luminary("SRA-UI-Designer", "sra-ui-designer.md", self.bridge),
            Luminary("SRA-Tester-Validator", "sra-tester-validator.md", self.bridge),
            Luminary("SRA-Deployer", "sra-deployer.md", self.bridge),
            Luminary("SRA-IDE-Orchestrator", "sra-ide-orchestrator.md", self.bridge),
            Luminary("SRA-Market-Analyst", "sra-market-analyst.md", self.bridge),
            Luminary("SRA-Security-Auditor", "sra-security-auditor.md", self.bridge),
            Luminary("SRA-Mathematical-Genius", "sra-mathematical-genius.md", self.bridge),
            Luminary("SRA-UX-Researcher", "sra-ux-researcher.md", self.bridge),
            Luminary("SRA-Legal-Counsel", "sra-legal-counsel.md", self.bridge),
            Luminary("SRA-Evo-Director", "sra-evo-director.md", self.bridge),
        ]
        self.referee_prompt = (_ROOT / "sra.md").read_text(encoding="utf-8")

    async def run_discussion(self, query: str):
        print(f"\n=== SUPER-PANEL DISCUSSION: {query} ===\n")
        results = []
        
        for lum in self.luminaries:
            print(f"[{lum.name}] Deliberating...")
            resp = await lum.deliberate(query)
            
            # Spawn Support Layer
            advisor = SupportRole("Advisor", lum.name, self.bridge)
            council = SupportRole("Council", lum.name, self.bridge)
            adversary = SupportRole("Adversary", lum.name, self.bridge)
            
            adv_fb = await advisor.evaluate(resp, query)
            cou_fb = await council.evaluate(resp, query)
            adv_crit = await adversary.evaluate(resp, query)
            
            print(f"[{lum.name}] Adversary Critique detected. Entering Debate Mode...")
            
            # Simplified Debate (1 round for now as proof of concept)
            debate_resp = await lum.deliberate(f"Defend your position against this critique: {adv_crit}", context=resp)
            
            # Synthesis by HelixEvolver (Referee)
            synthesis_prompt = f"As HelixEvolver (Judge/Referee), synthesize the debate between {lum.name} and its Adversary.\nLuminary: {resp}\nAdversary: {adv_crit}\nDefense: {debate_resp}\n\nProvide the FINAL SOVEREIGN SYNTHESIS."
            synthesis = None
            if self.bridge.hive.llm_available:
                synthesis = await self.bridge.hive.call_llm(synthesis_prompt, system=self.referee_prompt)
            if not synthesis:
                synthesis = self.bridge.llm.generate_completion(synthesis_prompt, self.referee_prompt)
            
            results.append({
                "luminary": lum.name,
                "response": resp,
                "advisor": adv_fb,
                "council": cou_fb,
                "adversary": adv_crit,
                "debate": debate_resp,
                "synthesis": synthesis
            })
            
            print(f"✓ [{lum.name}] Synthesis complete.\n")

        # Final Panel Conclusion
        final_prompt = "Synthesize the entire discussion into a single SOVEREIGN CONCLUSION."
        final_context = json.dumps(results, indent=2)
        system_final = self.referee_prompt + "\n\nContext:\n" + final_context
        
        final_conclusion = None
        if self.bridge.hive.llm_available:
            final_conclusion = await self.bridge.hive.call_llm(final_prompt, system=system_final)
        if not final_conclusion:
            final_conclusion = self.bridge.llm.generate_completion(final_prompt, system_final)
            
        print("\n=== FINAL SOVEREIGN CONCLUSION ===\n")
        print(final_conclusion)
        
        # Log to file
        log_path = _ROOT / "data" / f"panel_discussion_{int(asyncio.get_event_loop().time())}.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps({"query": query, "results": results, "final": final_conclusion}, indent=2), encoding="utf-8")
        print(f"\nDetailed transcript saved to: {log_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="Problem to discuss")
    args = parser.parse_args()
    
    panel = SuperPanel()
    asyncio.run(panel.run_discussion(args.query))
