#!/usr/bin/env python3
"""
Full System Test for HelixHive Phase 2.

Simulates a complete heartbeat cycle in a temporary git repository.
All modules are exercised with simulation mode enabled where possible.
Errors are captured, reported verbosely, and self‑healing (Golay repair, retry) is attempted.
"""

import asyncio
import logging
import os
import shutil
import tempfile
import time
import traceback
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging first – set to DEBUG for maximum detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("system_test")

# Import all HelixHive modules (assuming they are in the same directory or PYTHONPATH)
from genome import Genome, load_genome
from config import Config, load_config
from helixdb_git_adapter import HelixDBGit
from agent import Agent
from council import Council
from proposals import process_proposals
from fitness import FitnessPredictor
from world_model import WorldModel
from immune import immune_check
from market import Market
from helical import check_phase_flip, execute_flip, check_invariance
from faction_manager import FactionManager
from evo2 import generate_synthetic_agent
from revelation import generate_revelation_proposal
from pipeline import run_pipeline
from marketplace_sync import sync_marketplace
from llm_router import HelixLLMRouter
from memory import LeechErrorCorrector, leech_encode, _LEECH_PROJ, HD
from golay_self_repair import GolaySelfRepairEngine
from resources import ResourceManager, spawn_daughter


class SystemTest:
    """
    Orchestrates a full system test with detailed error reporting and self‑healing.
    """

    def __init__(self, simulate_llm: bool = True):
        self.simulate_llm = simulate_llm
        self.temp_dir = None
        self.original_dir = None
        self.db = None
        self.genome = None
        self.config = None
        self.agents = []
        self.errors = []
        self.warnings = []
        self.healing_attempts = []

    def setup(self):
        """Create a temporary git repository and initialize all components."""
        logger.info("=" * 60)
        logger.info("SYSTEM TEST SETUP")
        logger.info("=" * 60)

        # Create temp directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="helixhive_test_"))
        self.original_dir = Path.cwd()
        os.chdir(self.temp_dir)
        logger.info(f"Working in temporary directory: {self.temp_dir}")

        # Initialize git repo
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "lfs", "install"], check=True, capture_output=True)
        logger.info("Git repository initialized with LFS")

        # Create genome.yaml with test values
        genome_data = {
            'tick': 0,
            'helicity': {'current_phase': 0, 'flip_interval': 5, 'last_flip_tick': 0,
                         'mutation_bias': 0.05, 'invariance_tolerance': 0.1},
            'council': {'weights': {'guardian': 2, 'visionary': 1.5}},
            'ethics': {'forbidden_patterns': []},
            'constitution': {'protected': [], 'supermajority_threshold': 0.833},
            'evo2': {'enabled': True, 'fitness_weights': {'leech_similarity': 0.5, 'novelty_bonus': 0.3, 'phase_alignment': 0.2},
                     'temperature': 0.8, 'max_tokens': 1000},
            'pipeline': {'enabled': True, 'refinement_rounds': 2, 'max_product_words': 500},
            'immune': {'failure_threshold': 2, 'anomaly_threshold': 2.0, 'healing_cooldown': 1, 'max_per_heartbeat': 3},
            'market': {'min_reputation': 1, 'auction_duration': 60, 'max_listings_per_agent': 5},
            'revelation': {'enabled': True, 'generate_interval': 2},
            'model_proposals': {'min_validation_score': 0.7, 'spawn_repo': False},
            'github_app_id': '', 'github_private_key_path': '', 'github_installation_id': '',
            'template_owner': '', 'daughter_owner': '',
            'mutation': {'base_rate': 0.1},
            'default_prompt': 'You are a helpful test agent.',
            'default_traits': {'creativity': 0.5, 'thoroughness': 0.5, 'cooperativeness': 0.5, 'ambition': 0.5, 'curiosity': 0.5},
            'niche': 'test_niche'
        }
        with open('genome.yaml', 'w') as f:
            import yaml
            yaml.dump(genome_data, f)
        logger.info("genome.yaml created")

        # Create config.yaml with simulation mode
        config_data = {
            'simulation': self.simulate_llm,
            'logging': {'level': 'DEBUG'},
            'cache': {'enabled': False},  # disable cache for testing
        }
        with open('config.yaml', 'w') as f:
            yaml.dump(config_data, f)
        logger.info("config.yaml created")

        # Load genome and config
        self.genome = load_genome()
        self.config = load_config()
        logger.info("Genome and config loaded")

        # Initialize database
        self.db = HelixDBGit()
        self.db.load_all()
        logger.info("Database initialized")

        # Create some test agents
        self._create_test_agents(3)
        logger.info(f"Created {len(self.agents)} test agents")

        # Commit initial state
        self.db.commit(tick=0, summary="test setup")

    def _create_test_agents(self, count: int):
        """Create test agents with random traits."""
        for i in range(count):
            traits = {
                'creativity': 0.5 + 0.1 * i,
                'thoroughness': 0.6 - 0.05 * i,
                'cooperativeness': 0.7,
                'ambition': 0.5,
                'curiosity': 0.8
            }
            agent = Agent(
                role=f"test_agent_{i}",
                prompt=f"I am test agent {i}.",
                traits=traits,
                generation=0
            )
            agent.save_to_db(self.db)
            self.agents.append(agent)

    def run_heartbeat(self, tick: int):
        """
        Execute one full heartbeat cycle with detailed error trapping.
        Returns a dict with step outcomes.
        """
        logger.info("=" * 60)
        logger.info(f"HEARTBEAT TICK {tick}")
        logger.info("=" * 60)

        results = {}
        self.errors = []
        self.warnings = []
        self.healing_attempts = []

        # Step 1: Golay self‑repair
        results['repair'] = self._run_step("Golay Self‑Repair", self._step_repair)

        # Step 2: Phase flip check
        results['phase_check'] = self._run_step("Phase Flip Check", self._step_phase_check, tick)

        # Step 3: Immune check
        results['immune'] = self._run_step("Immune Check", self._step_immune)

        # Step 4: Load agents into faction manager
        results['faction_load'] = self._run_step("Faction Load", self._step_faction_load)

        # Step 5: Process proposals
        results['proposals'] = self._run_step("Process Proposals", self._step_proposals)

        # Step 6: Run product pipeline
        results['pipeline'] = self._run_step("Product Pipeline", self._step_pipeline)

        # Step 7: Market auction processing
        results['market'] = self._run_step("Market Auctions", self._step_market)

        # Step 8: Revelation Engine (if interval)
        if tick % self.genome.get('revelation.generate_interval', 10) == 0:
            results['revelation'] = self._run_step("Revelation Engine", self._step_revelation)

        # Step 9: Marketplace sync
        results['marketplace'] = self._run_step("Marketplace Sync", self._step_marketplace)

        # Step 10: Invariance check (if pending)
        results['invariance'] = self._run_step("Invariance Check", self._step_invariance)

        # Step 11: Commit changes
        results['commit'] = self._run_step("Git Commit", self._step_commit, tick)

        return results

    def _run_step(self, name: str, func, *args, **kwargs) -> Dict:
        """
        Execute a step with error handling and self‑healing.
        Returns a dict with status, duration, error (if any), and healing attempts.
        """
        logger.info(f"\n--- {name} ---")
        start = time.time()
        result = {
            'name': name,
            'status': 'pending',
            'duration_ms': 0,
            'error': None,
            'healed': False,
            'details': {}
        }
        try:
            output = func(*args, **kwargs)
            result['status'] = 'success'
            result['details'] = output if output is not None else {}
        except Exception as e:
            logger.error(f"❌ {name} FAILED: {e}")
            tb = traceback.format_exc()
            logger.debug(tb)
            result['status'] = 'failed'
            result['error'] = {'type': type(e).__name__, 'message': str(e), 'traceback': tb}
            self.errors.append((name, e))

            # Attempt self‑healing
            healed = self._attempt_healing(name, e)
            if healed:
                result['healed'] = True
                # Re-run the step (optional, but we'll just record)
                # For now, we mark as healed but keep the error.
                self.healing_attempts.append((name, healed))

        result['duration_ms'] = (time.time() - start) * 1000
        logger.info(f"   → {result['status'].upper()} in {result['duration_ms']:.2f} ms")
        if result['healed']:
            logger.info(f"   → Self‑healing applied")
        return result

    def _attempt_healing(self, step_name: str, error: Exception) -> bool:
        """
        Attempt to repair the system based on the error.
        Returns True if healing was applied.
        """
        logger.info(f"Attempting self‑healing for {step_name}...")

        # Healing strategies
        if "LeechErrorCorrector" in str(error) or "Golay" in str(error):
            # Golay-related error: try to rebuild coset table
            logger.info("Healing: Reloading Golay coset table...")
            try:
                LeechErrorCorrector._coset_table = None
                LeechErrorCorrector._ensure_table()
                logger.info("✅ Golay table reloaded")
                return True
            except Exception as e:
                logger.error(f"❌ Healing failed: {e}")
                return False

        elif "database" in str(error).lower() or "git" in str(error).lower():
            # Database error: try to reset to last commit
            logger.info("Healing: Resetting database to last commit...")
            try:
                self.db._git_pull()
                self.db.load_all()
                logger.info("✅ Database reset")
                return True
            except Exception as e:
                logger.error(f"❌ Healing failed: {e}")
                return False

        elif "LLM" in str(error) or "router" in str(error).lower():
            # LLM error: switch to simulation mode
            logger.info("Healing: Enabling simulation mode for LLM...")
            self.config.set('simulation', True)
            return True

        else:
            logger.info("No healing strategy for this error.")
            return False

    # Step implementations
    def _step_repair(self):
        engine = GolaySelfRepairEngine(self.db, self.genome.get('tick', 0))
        result = engine.run_cycle()
        return {'vectors_repaired': result['vectors_repaired']}

    def _step_phase_check(self, tick):
        proposal = check_phase_flip(self.db, self.genome, tick)
        if proposal:
            return {'flip_proposed': True, 'proposal': proposal}
        return {'flip_proposed': False}

    def _step_immune(self):
        proposals = immune_check(self.db, self.agents, self.genome)
        return {'healing_proposals': len(proposals)}

    def _step_faction_load(self):
        fm = FactionManager(self.db)
        fm.load_agents(self.agents)
        changed = fm.run_clustering()
        return {'factions': len(fm.factions), 'changed': changed}

    def _step_proposals(self):
        outcomes = process_proposals(self.db, self.agents, self.genome, self.config)
        return {'processed': len(outcomes), 'outcomes': outcomes}

    def _step_pipeline(self):
        product_ids = run_pipeline(
            niche=self.genome.get('niche', 'test'),
            agents=self.agents,
            genome=self.genome,
            config=self.config,
            db=self.db,
            simulate=self.simulate_llm
        )
        return {'products': len(product_ids), 'product_ids': product_ids}

    def _step_market(self):
        market = Market(self.db, self.genome)
        proposals = market.process_auctions()
        return {'auction_proposals': len(proposals)}

    async def _step_revelation(self):
        # Need async for revelation
        prop = await generate_revelation_proposal(self.db, self.genome, self.config)
        return {'proposal_generated': prop.get('summary')}

    def _step_marketplace(self):
        changed = sync_marketplace(self.db, simulate=self.simulate_llm)
        return {'marketplace_updated': changed}

    def _step_invariance(self):
        repair_proposal = check_invariance(self.db, self.genome, self.agents)
        if repair_proposal:
            return {'drift_detected': True, 'repair_proposal': repair_proposal}
        return {'drift_detected': False}

    def _step_commit(self, tick):
        self.db.commit(tick, summary=f"test heartbeat {tick}")
        return {'committed': True}

    def teardown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_dir)
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
            logger.info(f"Removed temporary directory: {self.temp_dir}")

    def generate_report(self, results: Dict) -> str:
        """Generate a verbose human‑readable report."""
        lines = []
        lines.append("=" * 70)
        lines.append("HELIXHIVE SYSTEM TEST REPORT")
        lines.append("=" * 70)
        lines.append(f"Test completed with {len(self.errors)} errors, {len(self.warnings)} warnings.")
        lines.append("")

        for step_name, step_result in results.items():
            lines.append(f"\n--- {step_result['name']} ---")
            lines.append(f"  Status: {step_result['status'].upper()}")
            lines.append(f"  Duration: {step_result['duration_ms']:.2f} ms")
            if step_result.get('healed'):
                lines.append(f"  Self‑healing applied")
            if step_result['error']:
                lines.append(f"  ERROR: {step_result['error']['type']}: {step_result['error']['message']}")
                lines.append(f"  Traceback:")
                for line in step_result['error']['traceback'].split('\n'):
                    lines.append(f"    {line}")
            if step_result.get('details'):
                lines.append(f"  Details: {json.dumps(step_result['details'], indent=2)}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    async def run(self, ticks: int = 3):
        """
        Run multiple heartbeat ticks.
        """
        logger.info("\n\n" + "="*70)
        logger.info("STARTING FULL SYSTEM TEST")
        logger.info("="*70)

        all_results = {}
        try:
            self.setup()
            for tick in range(1, ticks + 1):
                results = self.run_heartbeat(tick)
                all_results[f"tick_{tick}"] = results
                # Optionally break if too many errors
                if len(self.errors) > 5:
                    logger.error("Too many errors, aborting test.")
                    break
            report = self.generate_report(all_results)
            logger.info("\n" + report)
        finally:
            self.teardown()

        return all_results, report


async def main():
    """Entry point for the test."""
    import sys
    # Parse command line arguments for number of ticks
    ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    simulate = True  # Use simulation mode to avoid real LLM calls
    test = SystemTest(simulate_llm=simulate)
    results, report = await test.run(ticks)

    # Write report to file
    with open("system_test_report.txt", "w") as f:
        f.write(report)

    # Exit with error code if any errors
    if test.errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
