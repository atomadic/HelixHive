#!/usr/bin/env python3
"""
HelixHive Orchestrator – Heartbeat loop and main entry point.
Manages atomic transactions, checkpoint/rollback, and coordination of all subsystems.
"""

import argparse
import logging
import os
import sys
import time
import shutil
import tempfile
from pathlib import Path

import yaml

from agent import Agent
from council import Council
from genome import Genome
from config import Config
import helixdb
from proposals import process_proposals
from immune import immune_check
from pipeline import run_pipeline
from revelation import RevelationEngine
from helical import update_phase
from fitness import FitnessPredictor
from user_requests import process_pending_requests
from model_proposals import process_pending_models, handle_approved_model
import memory

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent
PRODUCTS_DIR = REPO_ROOT / "products"
HELIXDB_DIR = REPO_ROOT / "helixdb"
CHECKPOINT_DIR = REPO_ROOT / "checkpoints"
REQUESTS_DIR = REPO_ROOT / "requests"
MODELS_DIR = REPO_ROOT / "model_proposals"

for d in [PRODUCTS_DIR, HELIXDB_DIR, CHECKPOINT_DIR, REQUESTS_DIR, MODELS_DIR]:
    d.mkdir(exist_ok=True)


def heartbeat():
    logger.info("❤️ Heartbeat started")
    genome = Genome.load()
    config = Config.load()

    # Check for consecutive failures
    consecutive_failures = genome.data.get('consecutive_failures', 0)
    if consecutive_failures >= 3:
        logger.error("Too many failures, attempting recovery")
        _restore_from_checkpoint()
        genome.data['consecutive_failures'] = 0
        genome.save()

    with tempfile.TemporaryDirectory(prefix="helixhive_") as tmpdir:
        tmp_path = Path(tmpdir)
        logger.debug(f"Working in {tmp_path}")

        # Copy live data to temp
        live_helixdb = HELIXDB_DIR
        live_genome = REPO_ROOT / "genome.yaml"
        temp_helixdb = tmp_path / "helixdb"
        temp_genome = tmp_path / "genome.yaml"

        if live_helixdb.exists():
            shutil.copytree(live_helixdb, temp_helixdb)
        else:
            temp_helixdb.mkdir()
        if live_genome.exists():
            shutil.copy(live_genome, temp_genome)

        os.chdir(tmp_path)

        # Reload genome and config from temp
        genome = Genome.load()
        config = Config.load()
        genome.data['tick'] = genome.data.get('tick', 0) + 1
        tick = genome.data['tick']
        logger.info(f"Tick {tick}")

        db = helixdb.HelixDB(str(temp_helixdb))

        # Load agents
        agents = []
        for node in db.query_nodes_by_label('Agent'):
            agent = Agent.load_from_db(db, node.id)
            if agent:
                agents.append(agent)

        # Create seed agent if none
        if not agents:
            logger.info("No agents found, creating seed agent")
            seed = Agent(role="founder", prompt="I am the founding agent.")
            seed.save_to_db(db)
            agents = [seed]

        # Immune check
        try:
            immune_check(db, agents, genome)
        except Exception as e:
            logger.warning(f"Immune check failed: {e}")

        # Process pending user requests
        try:
            process_pending_requests(db, genome, config)
        except Exception as e:
            logger.warning(f"User requests processing failed: {e}")

        # Process pending model proposals
        try:
            process_pending_models(db, genome, config)
        except Exception as e:
            logger.warning(f"Model proposals processing failed: {e}")

        # Process proposals (including those from immune, user, model)
        try:
            proposal_results = process_proposals(db, agents, genome, config)
            logger.info(f"Processed {len(proposal_results)} proposals")
        except Exception as e:
            logger.error(f"Proposals processing failed: {e}")
            proposal_results = []

        # Run product pipeline if enabled
        if genome.data.get('pipeline', {}).get('enabled', False) and agents:
            try:
                niche = genome.data.get('niche', 'AI_coding_agents')
                run_pipeline(niche, agents, genome, config, db)
            except Exception as e:
                logger.error(f"Product pipeline failed: {e}")

        # Update helical phase
        try:
            update_phase(genome, db)
        except Exception as e:
            logger.warning(f"Helical phase update failed: {e}")

        # Retrain world model occasionally
        if tick % 10 == 0:
            try:
                predictor = FitnessPredictor(db, genome)
                predictor.world_model.train()
            except Exception as e:
                logger.warning(f"World model training failed: {e}")

        # Memory consolidation
        if tick % 100 == 0:
            try:
                cutoff = time.time() - 30 * 24 * 3600  # 30 days
                db.consolidate(cutoff)
            except Exception as e:
                logger.warning(f"Consolidation failed: {e}")

        # Save genome and commit DB
        try:
            genome.save()
            db.commit()
        except Exception as e:
            logger.error(f"Commit failed: {e}")
            raise

        # Create checkpoint
        checkpoint_dir = CHECKPOINT_DIR / f"backup_{int(time.time())}"
        checkpoint_dir.mkdir()
        if live_helixdb.exists():
            shutil.copytree(live_helixdb, checkpoint_dir / "helixdb")
        if live_genome.exists():
            shutil.copy(live_genome, checkpoint_dir / "genome.yaml")

        # Replace live with temp
        if live_helixdb.exists():
            shutil.rmtree(live_helixdb)
        shutil.move(temp_helixdb, live_helixdb)
        shutil.move(temp_genome, live_genome)

        # Clean old checkpoints
        checkpoints = sorted(CHECKPOINT_DIR.glob("backup_*"))
        for cp in checkpoints[:-5]:
            shutil.rmtree(cp)

        genome.data['consecutive_failures'] = 0
        genome.save()
        logger.info("✅ Heartbeat completed")


def _restore_from_checkpoint():
    checkpoints = sorted(CHECKPOINT_DIR.glob("backup_*"))
    if not checkpoints:
        return
    latest = checkpoints[-1]
    logger.info(f"Restoring from {latest}")
    if (latest / "helixdb").exists():
        if HELIXDB_DIR.exists():
            shutil.rmtree(HELIXDB_DIR)
        shutil.copytree(latest / "helixdb", HELIXDB_DIR)
    if (latest / "genome.yaml").exists():
        shutil.copy(latest / "genome.yaml", REPO_ROOT / "genome.yaml")


def spawn_agent(role, prompt):
    genome = Genome.load()
    agent = Agent(role=role, prompt=prompt)
    db = helixdb.HelixDB(str(HELIXDB_DIR))
    agent.save_to_db(db)
    db.commit()
    logger.info(f"✅ Agent '{role}' spawned with ID {agent.agent_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tick", action="store_true", help="Run one heartbeat")
    parser.add_argument("--spawn-agent", nargs=2, metavar=("ROLE", "PROMPT"), help="Create a new agent")
    args = parser.parse_args()

    try:
        if args.tick:
            heartbeat()
        elif args.spawn_agent:
            spawn_agent(args.spawn_agent[0], args.spawn_agent[1])
        else:
            parser.print_help()
    except Exception as e:
        logger.exception("Unhandled exception")
        try:
            genome = Genome.load()
            genome.data['consecutive_failures'] = genome.data.get('consecutive_failures', 0) + 1
            genome.save()
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
