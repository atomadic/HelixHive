"""
User Request Handling for HelixHive Phase 2.
Allows users to submit requests for products, which are then processed by the agent community.
Requests are stored as nodes in the database, tracked with status, and upon approval
trigger the product pipeline to generate the requested assets.
All requests are Leech‑grounded and Golay‑certified for provenance.
"""

import uuid
import time
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from agent import Agent
from pipeline import run_pipeline
from memory import leech_encode, _LEECH_PROJ, HD, LeechErrorCorrector
from helixdb_git_adapter import HelixDBGit
from genome import Genome
from config import Config

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# User Request Submission (CLI or API)
# ----------------------------------------------------------------------

def submit_request(niche: str,
                   style: Optional[str] = None,
                   target_audience: Optional[str] = None,
                   quantity: int = 1,
                   user_id: Optional[str] = None,
                   custom_prompt: Optional[str] = None) -> str:
    """
    CLI/API entry point: create a user request and write to a monitored directory.
    The orchestrator will pick it up on the next heartbeat.
    """
    request_id = str(uuid.uuid4())
    request = {
        'id': request_id,
        'type': 'UserRequest',
        'niche': niche,
        'style': style,
        'target_audience': target_audience,
        'quantity': quantity,
        'user_id': user_id,
        'custom_prompt': custom_prompt,
        'status': 'pending',
        'created_at': time.time(),
    }

    # Compute Leech vector for the request (for similarity matching)
    text = f"{niche} {style or ''} {target_audience or ''}"
    words = text.split()[:100]
    if words:
        word_vecs = [HD.from_word(w) for w in words]
        hd_vec = HD.bundle(word_vecs)
        leech_float = np.dot(hd_vec.astype(np.float32), _LEECH_PROJ)
        leech_vec = leech_encode(leech_float)
        corrected, syndrome = LeechErrorCorrector.correct(leech_vec)
        request['leech_vector'] = corrected.tolist()
        request['syndrome'] = int(syndrome)
    else:
        request['leech_vector'] = [0] * 24
        request['syndrome'] = 0

    # Determine requests directory (from environment or default)
    data_root = os.environ.get('HELIX_DATA_PATH', '.')
    requests_dir = Path(data_root) / 'requests'
    requests_dir.mkdir(parents=True, exist_ok=True)

    path = requests_dir / f"{request_id}.json"
    with open(path, 'w') as f:
        json.dump(request, f, indent=2)

    logger.info(f"User request {request_id} submitted for niche: {niche}")
    return request_id


def process_pending_requests(db: HelixDBGit, genome: Genome, config: Config):
    """
    Called by orchestrator: scan for pending user requests and create proposals.
    """
    data_root = os.environ.get('HELIX_DATA_PATH', '.')
    requests_dir = Path(data_root) / 'requests'
    if not requests_dir.exists():
        return

    for req_file in requests_dir.glob('*.json'):
        with open(req_file, 'r') as f:
            request = json.load(f)

        if request.get('status') != 'pending':
            continue

        # Create a proposal for this request
        proposal = {
            'type': 'user_product',
            'proposer_id': request.get('user_id'),
            'description': f"User request: {request['niche']} – {request.get('style', '')}",
            'tags': ['user_request', request['niche']],
            'changes': {
                'request_id': request['id'],
                'niche': request['niche'],
                'style': request.get('style'),
                'target_audience': request.get('target_audience'),
                'quantity': request.get('quantity', 1),
                'custom_prompt': request.get('custom_prompt'),
                'leech_vector': request.get('leech_vector'),
            },
            'timestamp': time.time()
        }

        # Add proposal node to DB (will be picked up by proposals engine)
        prop_id = f"prop_req_{int(time.time())}_{request['id'][-8:]}"
        proposal['id'] = prop_id
        proposal['status'] = 'pending'
        db.update_properties(prop_id, proposal)

        # Store link (optional)
        request['proposal_id'] = prop_id
        request['status'] = 'in_progress'
        with open(req_file, 'w') as f:
            json.dump(request, f)

        logger.info(f"Created proposal {prop_id} for user request {request['id']}")


def handle_approved_user_request(changes: Dict, db: HelixDBGit, genome: Genome, config: Config):
    """
    Called by proposals engine when a user product proposal is approved.
    Triggers the product pipeline to fulfill the request.
    """
    request_id = changes['request_id']
    niche = changes['niche']
    style = changes.get('style')
    target_audience = changes.get('target_audience')
    quantity = changes.get('quantity', 1)
    custom_prompt = changes.get('custom_prompt')

    # Find the request file (or load from DB)
    data_root = os.environ.get('HELIX_DATA_PATH', '.')
    req_path = Path(data_root) / 'requests' / f"{request_id}.json"
    if not req_path.exists():
        # Maybe it's stored in the database? For now, assume file.
        logger.error(f"Request file {req_path} not found")
        return

    with open(req_path, 'r') as f:
        request = json.load(f)

    # Build context for pipeline
    user_context = {
        'target_audience': target_audience,
        'style': style,
        'custom_prompt': custom_prompt,
        'request_id': request_id,
    }

    # Run pipeline (this will create product nodes and marketplace entries)
    # Need to load agents first; we assume they are already loaded in the heartbeat.
    # We'll fetch them from the database.
    agents = []
    agent_nodes = db.get_nodes_by_type('Agent')
    for node_id, node in agent_nodes.items():
        agent = Agent.from_dict(node, vectors={'leech': node.get('leech_vector')})
        agents.append(agent)

    # Run pipeline (this may be async; but proposals engine is sync, so we need to handle)
    # For simplicity, we'll call the sync version; if pipeline is async, we need to run in event loop.
    # We'll assume we are in an async context; if not, we can use asyncio.run() but that's risky.
    # Better to make pipeline synchronous for now.
    product_ids = run_pipeline(
        niche=niche,
        agents=agents,
        genome=genome,
        config=config,
        db=db,
        user_context=user_context,
        simulate=config.get('simulation', False)
    )

    # Update request status
    request['status'] = 'completed'
    request['completed_at'] = time.time()
    request['product_ids'] = product_ids
    with open(req_path, 'w') as f:
        json.dump(request, f)

    logger.info(f"User request {request_id} fulfilled with products: {product_ids}")
