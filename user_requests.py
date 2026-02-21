"""
User request handling for HelixHive.
Allows users to submit requests for products, which are then processed by the agent community.
"""

import uuid
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import helixdb
from proposals import process_proposals  # or call pipeline directly


def submit_request(niche: str, style: Optional[str] = None,
                   target_audience: Optional[str] = None,
                   quantity: int = 1, user_id: Optional[str] = None) -> str:
    """
    CLI entry point: create a user request and write to a file.
    The orchestrator will pick it up.
    """
    request = {
        'request_id': str(uuid.uuid4()),
        'niche': niche,
        'style': style,
        'target_audience': target_audience,
        'quantity': quantity,
        'user_id': user_id,
        'status': 'pending',
        'created_at': time.time()
    }
    # Write to a monitored directory (e.g., ./requests/)
    requests_dir = Path('./requests')
    requests_dir.mkdir(exist_ok=True)
    path = requests_dir / f"{request['request_id']}.json"
    with open(path, 'w') as f:
        json.dump(request, f)
    return request['request_id']


def process_pending_requests(db: 'helixdb.HelixDB', genome: Any, config: Any):
    """
    Called by orchestrator: scan for pending user requests and create proposals.
    """
    requests_dir = Path('./requests')
    if not requests_dir.exists():
        return

    for req_file in requests_dir.glob('*.json'):
        with open(req_file, 'r') as f:
            request = json.load(f)

        if request['status'] != 'pending':
            continue

        # Create a proposal for this request
        proposal = {
            'type': 'user_product',
            'proposer_id': request.get('user_id'),  # may be None
            'description': f"User request: {request['niche']}",
            'tags': ['user_request', request['niche']],
            'changes': {
                'request_id': request['request_id'],
                'niche': request['niche'],
                'style': request['style'],
                'target_audience': request['target_audience'],
                'quantity': request['quantity']
            },
            'timestamp': time.time()
        }

        # Add proposal node to DB (will be picked up by proposals engine)
        prop_id = db.add_node('Proposal', properties=proposal)
        db.add_edge(prop_id, request['request_id'], 'FULFILLS')

        # Mark request as in_progress
        request['status'] = 'in_progress'
        with open(req_file, 'w') as f:
            json.dump(request, f)

        logger.info(f"Created proposal {prop_id} for user request {request['request_id']}")
