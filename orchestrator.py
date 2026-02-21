#!/usr/bin/env python3
"""
HelixHive GitHub‑Native Orchestrator – Heartbeat loop.

Sequence:
1. Acquire data lock (if needed – actually deferred to commit)
2. Load database from git
3. Run Golay self‑repair engine
4. Load agents into memory
5. Run product pipeline (4‑round enhancement)
6. Run marketplace sync
7. Commit all changes to git
8. Log metrics
"""

import os
import sys
import time
import json
import logging
import signal
from pathlib import Path
from typing import Dict, Any

# HelixHive modules
from golay_self_repair import GolaySelfRepairEngine
from helixdb_git_adapter import HelixDBGit
from agent import Agent
from pipeline import run_pipeline
from marketplace_sync import sync_marketplace  # new module (to be created)
from genome import Genome
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Timeout for the entire heartbeat (seconds)
HEARTBEAT_TIMEOUT = 240  # 4 minutes

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Heartbeat timed out")

def heartbeat(simulate: bool = False):
    """Main heartbeat function."""
    logger.info("❤️ HelixHive GitHub‑native heartbeat started")

    # Set global timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(HEARTBEAT_TIMEOUT)

    start_time = time.time()
    metrics = {
        "tick": 0,
        "agents_loaded": 0,
        "vectors_repaired": 0,
        "products_created": 0,
        "marketplace_updated": False,
        "changes_committed": False,
        "elapsed_seconds": 0,
        "errors": []
    }

    try:
        # Load genome and config
        genome = Genome.load()
        config = Config.load()
        tick = genome.data.get('tick', 0) + 1
        metrics["tick"] = tick
        logger.info(f"Tick {tick}")

        # Initialize database adapter
        db = HelixDBGit()
        db.load_all()   # loads all nodes and vectors into memory

        # --- Step 1: Golay self‑repair ---
        try:
            repair_engine = GolaySelfRepairEngine(db, tick)
            repair_metrics = repair_engine.run_cycle()
            metrics["vectors_repaired"] = repair_metrics["vectors_repaired"]
            logger.info(f"Repair: {repair_metrics['vectors_repaired']} vectors repaired")
        except Exception as e:
            logger.exception("Repair engine failed")
            metrics["errors"].append("repair_failed")

        # --- Step 2: Load agents into memory (as Agent objects) ---
        try:
            agents = []
            agent_nodes = db.get_nodes_by_type("Agent")
            for node_id, data in agent_nodes.items():
                # Convert to Agent object (needs properties and vector)
                agent = Agent.from_dict(data)  # assuming Agent has from_dict
                # The vector is already in data["leech_vector"]
                agents.append(agent)
            metrics["agents_loaded"] = len(agents)
            logger.info(f"Loaded {len(agents)} agents")
        except Exception as e:
            logger.exception("Agent loading failed")
            metrics["errors"].append("agent_load_failed")
            agents = []   # proceed with empty list

        # --- Step 3: Product pipeline (if enabled) ---
        if genome.data.get('pipeline', {}).get('enabled', True) and agents:
            try:
                niche = genome.data.get('niche', 'general')
                # pipeline updates db directly (via db.update_*)
                products = run_pipeline(niche, agents, genome, config, db, simulate=simulate)
                metrics["products_created"] = len(products)
                logger.info(f"Pipeline created {len(products)} products")
            except Exception as e:
                logger.exception("Pipeline failed")
                metrics["errors"].append("pipeline_failed")

        # --- Step 4: Marketplace sync (generate index) ---
        try:
            changed = sync_marketplace(db, simulate=simulate)
            metrics["marketplace_updated"] = changed
            if changed:
                logger.info("Marketplace index updated")
        except Exception as e:
            logger.exception("Marketplace sync failed")
            metrics["errors"].append("marketplace_failed")

        # --- Step 5: Commit all changes to git ---
        try:
            if not simulate:
                # Generate a summary string for commit message
                summary = f"repaired={metrics['vectors_repaired']}, products={metrics['products_created']}"
                db.commit(tick, summary)
                metrics["changes_committed"] = True
                logger.info("Changes committed")
            else:
                logger.info("Simulation mode: skipping commit")
                metrics["changes_committed"] = False
        except Exception as e:
            logger.exception("Commit failed")
            metrics["errors"].append("commit_failed")

        # --- Step 6: Update genome tick and save ---
        try:
            genome.data['tick'] = tick
            genome.save()
        except Exception as e:
            logger.exception("Genome save failed")
            metrics["errors"].append("genome_save_failed")

        # Final metrics
        metrics["elapsed_seconds"] = time.time() - start_time
        logger.info(f"✅ Heartbeat completed in {metrics['elapsed_seconds']:.2f}s")

    except TimeoutError:
        logger.error("Heartbeat timed out")
        metrics["errors"].append("timeout")
    except Exception as e:
        logger.exception("Unhandled exception in heartbeat")
        metrics["errors"].append("unhandled")
    finally:
        signal.alarm(0)  # disable alarm

    # Output structured metrics (could be used by monitoring)
    print(json.dumps(metrics))
    return metrics


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tick", action="store_true", help="Run one heartbeat")
    parser.add_argument("--simulate", action="store_true", help="Simulation mode (no LLM, no commit)")
    args = parser.parse_args()

    if args.tick:
        heartbeat(simulate=args.simulate)
    else:
        parser.print_help()
