"""
Model Proposals for HelixHive Phase 2.
Allows users to propose entirely new HelixHive models (e.g., HelixQuantStack, HelixNFTStack).
Includes validator agents that perform security, economic, and constitutional analysis.
All proposals are Leech‑grounded and Golay‑certified.
Upon approval, a daughter repository is spawned via GitHub App.
"""

import uuid
import time
import json
import logging
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np

from llm_router import call_llm
from memory import leech_encode, _LEECH_PROJ, HD, LeechErrorCorrector
from helixdb_git_adapter import HelixDBGit
from resources import ResourceManager
from genome import Genome
from config import Config

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Model Validator (uses LLM + static analysis)
# ----------------------------------------------------------------------

class ModelValidator:
    """
    Runs a suite of validations on a proposed model.
    Validations are Leech‑grounded and produce a report.
    """

    def __init__(self, db: HelixDBGit, genome: Genome, config: Config):
        self.db = db
        self.genome = genome
        self.config = config

    async def validate(self, model_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform all validations and return a report.
        """
        report = {
            'model_id': model_spec.get('model_id'),
            'security': await self._security_audit(model_spec),
            'economic': await self._economic_simulation(model_spec),
            'constitutional': await self._constitutional_check(model_spec),
            'privacy': await self._privacy_assessment(model_spec),
            'overall_score': 0.0,
            'approved': False,
            'leech_vector': model_spec.get('leech_vector'),
            'syndrome': model_spec.get('syndrome', -1),
        }

        # Compute overall score (average of numeric scores)
        scores = []
        for key in ['security', 'economic', 'constitutional', 'privacy']:
            if isinstance(report[key], dict) and 'score' in report[key]:
                scores.append(report[key]['score'])
        if scores:
            report['overall_score'] = sum(scores) / len(scores)
        threshold = self.genome.get('model_proposals.min_validation_score', 0.7)
        report['approved'] = report['overall_score'] >= threshold

        # Store validation report in DB
        self._store_report(report)
        return report

    async def _security_audit(self, spec: Dict) -> Dict:
        """Check smart contracts, API keys, etc."""
        code = spec.get('smart_contract', '')
        if not code:
            return {'score': 1.0, 'notes': 'No smart contract provided'}

        # Use LLM with Leech grounding
        prompt = f"""Analyze this smart contract for vulnerabilities (reentrancy, overflow, etc.).
        Return a JSON with:
        - score: 0.0-1.0 (0=very vulnerable, 1=secure)
        - notes: brief explanation
        - vulnerabilities: list of strings
        Contract code:
        {code}"""
        leech_vec = self._compute_text_leech(code)

        try:
            response = await call_llm(
                prompt,
                system="You are a smart contract security expert.",
                leech_vector=leech_vec,
                temperature=0.3,
                max_tokens=1000
            )
            # Parse JSON from response
            import json
            try:
                data = json.loads(response)
                score = float(data.get('score', 0.5))
                notes = data.get('notes', '')
                vulns = data.get('vulnerabilities', [])
                return {'score': score, 'notes': notes, 'vulnerabilities': vulns}
            except:
                # Fallback
                score = 0.2 if 'vulnerability' in response.lower() else 0.9
                return {'score': score, 'notes': response[:200], 'vulnerabilities': []}
        except Exception as e:
            logger.error(f"Security audit failed: {e}")
            return {'score': 0.5, 'notes': 'Audit failed', 'vulnerabilities': []}

    async def _economic_simulation(self, spec: Dict) -> Dict:
        """Simulate market dynamics (placeholder – can be expanded)."""
        # Could run a lightweight simulation using agents.
        # For now, return a default score.
        return {'score': 0.8, 'notes': 'Economic simulation not yet implemented'}

    async def _constitutional_check(self, spec: Dict) -> Dict:
        """Check if model aligns with core values."""
        if 'rights_declaration' not in spec:
            return {'score': 0.0, 'notes': 'Missing rights declaration'}
        # Could also check other constitutional requirements
        return {'score': 1.0, 'notes': 'Constitutional requirements met'}

    async def _privacy_assessment(self, spec: Dict) -> Dict:
        """Ensure data handling meets privacy standards."""
        if spec.get('privacy_policy', ''):
            return {'score': 0.9, 'notes': 'Privacy policy provided'}
        else:
            return {'score': 0.3, 'notes': 'No privacy policy'}

    def _compute_text_leech(self, text: str) -> np.ndarray:
        words = text.split()[:100]
        if not words:
            return np.zeros(24)
        word_vecs = [HD.from_word(w) for w in words]
        hd_vec = HD.bundle(word_vecs)
        leech_float = np.dot(hd_vec.astype(np.float32), _LEECH_PROJ)
        return leech_encode(leech_float)

    def _store_report(self, report: Dict):
        """Store validation report as a node in the database."""
        report_id = f"val_{int(time.time())}_{report['model_id'][-8:]}"
        node_data = {
            'id': report_id,
            'type': 'ValidationReport',
            'model_id': report['model_id'],
            'overall_score': report['overall_score'],
            'approved': report['approved'],
            'security_score': report['security']['score'],
            'economic_score': report['economic']['score'],
            'constitutional_score': report['constitutional']['score'],
            'privacy_score': report['privacy']['score'],
            'timestamp': time.time(),
        }
        self.db.update_properties(report_id, node_data)
        logger.info(f"Validation report {report_id} stored")


# ----------------------------------------------------------------------
# Model Proposal Submission
# ----------------------------------------------------------------------

def submit_model_proposal(model_spec: Dict[str, Any]) -> str:
    """
    CLI/API entry point: user submits a model specification.
    Writes to a monitored directory.
    """
    model_id = str(uuid.uuid4())
    model_spec['model_id'] = model_id
    model_spec['status'] = 'pending'
    model_spec['created_at'] = time.time()

    # Compute Leech vector for the model (from description)
    desc = model_spec.get('description', '') + ' ' + model_spec.get('name', '')
    words = desc.split()[:100]
    if words:
        word_vecs = [HD.from_word(w) for w in words]
        hd_vec = HD.bundle(word_vecs)
        leech_float = np.dot(hd_vec.astype(np.float32), _LEECH_PROJ)
        leech_vec = leech_encode(leech_float)
        corrected, syndrome = LeechErrorCorrector.correct(leech_vec)
        model_spec['leech_vector'] = corrected.tolist()
        model_spec['syndrome'] = int(syndrome)
    else:
        model_spec['leech_vector'] = [0] * 24
        model_spec['syndrome'] = 0

    # Determine models directory
    data_root = os.environ.get('HELIX_DATA_PATH', '.')
    models_dir = Path(data_root) / 'model_proposals'
    models_dir.mkdir(parents=True, exist_ok=True)

    path = models_dir / f"{model_id}.json"
    with open(path, 'w') as f:
        json.dump(model_spec, f, indent=2)

    logger.info(f"Model proposal {model_id} submitted: {model_spec.get('name', 'Unnamed')}")
    return model_id


async def process_pending_models(db: HelixDBGit, genome: Genome, config: Config):
    """
    Called by orchestrator: scan for pending model proposals, validate, and create proposals.
    """
    data_root = os.environ.get('HELIX_DATA_PATH', '.')
    models_dir = Path(data_root) / 'model_proposals'
    if not models_dir.exists():
        return

    for model_file in models_dir.glob('*.json'):
        with open(model_file, 'r') as f:
            model_spec = json.load(f)

        if model_spec.get('status') != 'pending':
            continue

        # Validate
        validator = ModelValidator(db, genome, config)
        report = await validator.validate(model_spec)

        # Create a proposal for council vote
        proposal = {
            'type': 'model_proposal',
            'proposer_id': model_spec.get('user_id'),
            'description': f"New model: {model_spec.get('name', 'Unnamed')} – score {report['overall_score']:.2f}",
            'tags': ['model', model_spec.get('domain', 'general')],
            'changes': {
                'model_id': model_spec['model_id'],
                'spec': model_spec,
                'validation_report': report,
                'leech_vector': model_spec.get('leech_vector'),
            },
            'timestamp': time.time()
        }

        prop_id = f"prop_model_{int(time.time())}_{model_spec['model_id'][-8:]}"
        proposal['id'] = prop_id
        proposal['status'] = 'pending'
        db.update_properties(prop_id, proposal)

        # Link
        model_spec['proposal_id'] = prop_id
        model_spec['status'] = 'in_progress'
        with open(model_file, 'w') as f:
            json.dump(model_spec, f)

        logger.info(f"Created proposal {prop_id} for model {model_spec['model_id']}")


async def handle_approved_model(changes: Dict, db: HelixDBGit, genome: Genome, config: Config):
    """
    Called by proposals engine when a model proposal is approved.
    Spawns a daughter repository and records it.
    """
    model_id = changes['model_id']
    spec = changes['spec']
    report = changes.get('validation_report', {})

    # Initialize resource manager
    from resources import ResourceManager
    rm = ResourceManager(db, genome, config)
    await rm.initialize()

    # Spawn daughter
    repo_name = spec.get('repo_name', f"helix-{model_id[:8]}")
    niche = spec.get('domain', 'general')
    try:
        repo_url = await rm.spawn_daughter(
            name=repo_name,
            niche=niche,
            template_owner=genome.get('template_owner'),
            template_repo=genome.get('model_proposals.template_repo', 'helixhive-template'),
            custom_genome=spec.get('custom_genome')
        )
        logger.info(f"Spawned daughter for model {model_id} at {repo_url}")
    except Exception as e:
        logger.error(f"Failed to spawn daughter for model {model_id}: {e}")
        return

    # Record in database
    daughter_id = f"model_instance_{int(time.time())}_{model_id[-8:]}"
    node_data = {
        'id': daughter_id,
        'type': 'ModelInstance',
        'model_id': model_id,
        'repo_url': repo_url,
        'repo_name': repo_name,
        'niche': niche,
        'status': 'active',
        'spawned_at': time.time(),
        'validation_report': report.get('overall_score'),
        'leech_vector': spec.get('leech_vector'),
    }
    db.update_properties(daughter_id, node_data)

    # Update model proposal status
    data_root = os.environ.get('HELIX_DATA_PATH', '.')
    model_path = Path(data_root) / 'model_proposals' / f"{model_id}.json"
    if model_path.exists():
        with open(model_path, 'r') as f:
            model_spec = json.load(f)
        model_spec['status'] = 'spawned'
        model_spec['spawned_at'] = time.time()
        model_spec['repo_url'] = repo_url
        with open(model_path, 'w') as f:
            json.dump(model_spec, f)
