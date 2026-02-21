"""
Model proposals – allow users to propose entirely new HelixHive models (e.g., HelixQuantStack).
Includes validator agents that perform security, economic, and constitutional analysis.
"""

import uuid
import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

import helixdb
from resources import spawn_daughter
from llm import call_llm  # for validators

logger = logging.getLogger(__name__)


class ModelValidator:
    """
    Runs a suite of validations on a proposed model.
    """

    def __init__(self, db: 'helixdb.HelixDB', genome: Any):
        self.db = db
        self.genome = genome

    def validate(self, model_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform all validations and return a report.
        """
        report = {
            'model_id': model_spec.get('model_id'),
            'security': self._security_audit(model_spec),
            'economic': self._economic_simulation(model_spec),
            'constitutional': self._constitutional_check(model_spec),
            'privacy': self._privacy_assessment(model_spec),
            'overall_score': 0.0,
            'approved': False
        }

        # Compute overall score (simple average of numeric scores)
        scores = []
        for key in ['security', 'economic', 'constitutional', 'privacy']:
            if isinstance(report[key], dict) and 'score' in report[key]:
                scores.append(report[key]['score'])
        if scores:
            report['overall_score'] = sum(scores) / len(scores)
        report['approved'] = report['overall_score'] >= 0.7  # threshold

        return report

    def _security_audit(self, spec: Dict) -> Dict:
        """Check smart contracts, API keys, etc."""
        # For now, use an LLM to analyze any smart contract code provided.
        code = spec.get('smart_contract', '')
        if not code:
            return {'score': 1.0, 'notes': 'No smart contract provided'}
        prompt = f"Analyze this smart contract for vulnerabilities (reentrancy, overflow, etc.):\n{code}"
        response = call_llm(prompt, max_tokens=500)
        # Simple heuristic: if response contains "vulnerability", score low
        score = 0.2 if 'vulnerability' in response.lower() else 0.9
        return {'score': score, 'notes': response[:200]}

    def _economic_simulation(self, spec: Dict) -> Dict:
        """Simulate market dynamics."""
        # Placeholder – in reality, run an agent‑based simulation.
        return {'score': 0.8, 'notes': 'Simulation not yet implemented'}

    def _constitutional_check(self, spec: Dict) -> Dict:
        """Check if model aligns with core values."""
        # Simple check: must include a rights declaration.
        if 'rights_declaration' not in spec:
            return {'score': 0.0, 'notes': 'Missing rights declaration'}
        return {'score': 1.0, 'notes': 'Rights declaration present'}

    def _privacy_assessment(self, spec: Dict) -> Dict:
        """Ensure data handling meets privacy standards."""
        if spec.get('privacy_policy', ''):
            return {'score': 0.9, 'notes': 'Privacy policy provided'}
        else:
            return {'score': 0.3, 'notes': 'No privacy policy'}


def submit_model_proposal(model_spec: Dict[str, Any]) -> str:
    """
    CLI entry point: user submits a model specification.
    """
    model_id = str(uuid.uuid4())
    model_spec['model_id'] = model_id
    model_spec['status'] = 'pending'
    model_spec['created_at'] = time.time()

    # Save to file (or directly to DB via orchestrator)
    models_dir = Path('./model_proposals')
    models_dir.mkdir(exist_ok=True)
    path = models_dir / f"{model_id}.json"
    with open(path, 'w') as f:
        json.dump(model_spec, f)

    logger.info(f"Model proposal {model_id} submitted")
    return model_id


def process_pending_models(db: 'helixdb.HelixDB', genome: Any, config: Any):
    """
    Called by orchestrator: validate pending model proposals and, if approved, spawn daughters.
    """
    models_dir = Path('./model_proposals')
    if not models_dir.exists():
        return

    for model_file in models_dir.glob('*.json'):
        with open(model_file, 'r') as f:
            model_spec = json.load(f)

        if model_spec['status'] != 'pending':
            continue

        # Validate
        validator = ModelValidator(db, genome)
        report = validator.validate(model_spec)

        # Create a proposal for council vote
        proposal = {
            'type': 'model_proposal',
            'proposer_id': model_spec.get('user_id'),
            'description': f"New model: {model_spec.get('name', 'Unnamed')}",
            'tags': ['model', model_spec.get('domain', 'general')],
            'changes': {
                'model_id': model_spec['model_id'],
                'spec': model_spec,
                'validation_report': report
            },
            'timestamp': time.time()
        }

        prop_id = db.add_node('Proposal', properties=proposal)
        db.add_edge(prop_id, model_spec['model_id'], 'PROPOSES')

        # Mark as in_progress
        model_spec['status'] = 'in_progress'
        with open(model_file, 'w') as f:
            json.dump(model_spec, f)

        logger.info(f"Created proposal {prop_id} for model {model_spec['model_id']}")


def handle_approved_model(changes: Dict, db: 'helixdb.HelixDB', genome: Any):
    """
    Called by proposals engine when a model proposal is approved.
    Spawns a daughter repository.
    """
    model_id = changes['model_id']
    spec = changes['spec']
    # Spawn daughter
    repo_url = spawn_daughter(
        name=spec.get('repo_name', f"helix-{model_id[:8]}"),
        niche=spec.get('domain', 'general'),
        template_owner=genome.data.get('template_owner'),
        template_repo=genome.data.get('template_repo', 'helixhive-template')
    )
    logger.info(f"Spawned daughter for model {model_id} at {repo_url}")
    # Record in DB
    db.add_node('ModelInstance', properties={
        'model_id': model_id,
        'repo_url': repo_url,
        'status': 'active',
        'spawned_at': time.time()
    })
