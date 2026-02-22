"""
External Resources Manager for HelixHive Phase 2 – handles GitHub App authentication,
daughter repository spawning, and secure secret management with full mathematical grounding.
Daughter repositories are tracked in the database with Leech vectors for provenance.
"""

import os
import time
import base64
import json
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import aiohttp
import jwt
from nacl import public
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from helixdb_git_adapter import HelixDBGit
from memory import leech_encode, _LEECH_PROJ, HD
from genome import Genome
from config import Config

logger = logging.getLogger(__name__)


class Vault:
    """
    Simple secret vault that reads from environment variables.
    For production, use Secret Manager (AWS/GCP/HashiCorp).
    """

    @staticmethod
    def get(key: str) -> Optional[str]:
        return os.environ.get(key)


class GitHubApp:
    """
    GitHub App authentication and API operations.
    Handles JWT generation, installation token caching, and repository operations.
    Uses aiohttp for async operations and tenacity for retries.
    """

    # Required permissions for the GitHub App:
    # - Administration: write (to create repositories)
    # - Secrets: write (to set repository secrets)
    # - Metadata: read (to verify repo existence)

    def __init__(self, app_id: str, private_key_pem: str, installation_id: str):
        """
        Args:
            app_id: GitHub App ID (from app settings)
            private_key_pem: PEM string of the app's private key
            installation_id: ID of the installation (which account/organization the app is installed on)
        """
        self.app_id = app_id
        self.installation_id = installation_id
        self._private_key = private_key_pem
        self._token_cache: Dict[str, Tuple[str, float]] = {}  # installation_id -> (token, expiry)

    @classmethod
    async def create(cls, genome: Genome) -> Optional['GitHubApp']:
        """Factory method: load credentials from genome/ vault."""
        app_id = genome.get('github_app_id')
        key_path = genome.get('github_private_key_path')
        installation_id = genome.get('github_installation_id')

        if not app_id or not key_path or not installation_id:
            logger.warning("GitHub App not fully configured")
            return None

        # Load private key from file
        key_path = Path(key_path)
        if not key_path.is_absolute():
            key_path = Path(__file__).parent / key_path
        if not key_path.exists():
            logger.error(f"GitHub private key file not found: {key_path}")
            return None
        try:
            with open(key_path, 'r') as f:
                private_key_pem = f.read()
        except Exception as e:
            logger.error(f"Failed to read private key: {e}")
            return None

        return cls(str(app_id), private_key_pem, str(installation_id))

    def _generate_jwt(self) -> str:
        """Generate a JSON Web Token (JWT) for GitHub App authentication (valid 10 minutes)."""
        now = int(time.time())
        payload = {
            'iat': now,
            'exp': now + 600,  # 10 minutes
            'iss': self.app_id
        }
        return jwt.encode(payload, self._private_key, algorithm='RS256')

    async def _get_installation_token(self, session: aiohttp.ClientSession) -> str:
        """
        Get a short-lived installation access token (1 hour). Cached.
        """
        now = time.time()
        cached = self._token_cache.get(self.installation_id)
        if cached and cached[1] > now + 60:  # refresh if less than 1 minute left
            return cached[0]

        jwt_token = self._generate_jwt()
        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(aiohttp.ClientError)
        )
        async def _request():
            async with session.post(url, headers=headers) as resp:
                if resp.status == 403:
                    text = await resp.text()
                    if 'rate limit' in text.lower():
                        raise aiohttp.ClientError("Rate limited")
                resp.raise_for_status()
                return await resp.json()

        try:
            data = await _request()
            token = data['token']
            expires_at = data['expires_at']
            # Parse expires_at (ISO 8601) to timestamp
            expiry = time.mktime(time.strptime(expires_at, "%Y-%m-%dT%H:%M:%SZ"))
            self._token_cache[self.installation_id] = (token, expiry)
            logger.info("Obtained new GitHub installation token")
            return token
        except Exception as e:
            logger.error(f"Failed to get installation token: {e}")
            raise

    async def _api_request(self, method: str, url: str, session: aiohttp.ClientSession,
                           json: Optional[Dict] = None) -> Dict:
        """Make an authenticated API request using the installation token."""
        token = await self._get_installation_token(session)
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(aiohttp.ClientError)
        )
        async def _request():
            async with session.request(method, url, headers=headers, json=json) as resp:
                if resp.status == 403:
                    text = await resp.text()
                    if 'rate limit' in text.lower():
                        raise aiohttp.ClientError("Rate limited")
                resp.raise_for_status()
                if resp.content_type == 'application/json':
                    return await resp.json()
                return {}

        return await _request()

    async def create_repository_from_template(self, template_owner: str, template_repo: str,
                                              new_owner: str, new_name: str,
                                              description: str = "", private: bool = False) -> str:
        """
        Create a new repository from a template repository.
        Returns the URL of the new repository.
        """
        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/repos/{template_owner}/{template_repo}/generate"
            payload = {
                'owner': new_owner,
                'name': new_name,
                'description': description,
                'private': private,
                'include_all_branches': False
            }
            logger.info(f"Creating repository {new_owner}/{new_name} from template {template_owner}/{template_repo}")
            result = await self._api_request('POST', url, session, json=payload)

            # Wait for the repo to be ready
            if not await self._wait_for_repo_ready(new_owner, new_name, session):
                raise RuntimeError(f"Repository {new_owner}/{new_name} not ready after creation")

            return result.get('html_url', f"https://github.com/{new_owner}/{new_name}")

    async def _wait_for_repo_ready(self, owner: str, repo: str, session: aiohttp.ClientSession,
                                   timeout: int = 60) -> bool:
        """Poll the repository until it is fully initialized."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                url = f"https://api.github.com/repos/{owner}/{repo}"
                await self._api_request('GET', url, session)
                return True
            except Exception as e:
                logger.debug(f"Repo not ready yet: {e}")
                await asyncio.sleep(2)
        logger.warning(f"Timeout waiting for repository {owner}/{repo} to be ready")
        return False

    async def set_repository_secret(self, owner: str, repo: str, secret_name: str,
                                    secret_value: str, session: aiohttp.ClientSession) -> None:
        """Set a secret in a repository using libsodium encryption."""
        # Get the repository's public key
        key_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
        key_data = await self._api_request('GET', key_url, session)
        public_key = key_data['key']
        key_id = key_data['key_id']

        # Encrypt the secret using libsodium (sealed box)
        pub = public.PublicKey(public_key.encode('utf-8'))
        sealed_box = public.SealedBox(pub)
        encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')

        # Set the secret
        secret_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
        payload = {
            'encrypted_value': encrypted_b64,
            'key_id': key_id
        }
        await self._api_request('PUT', secret_url, session, json=payload)
        logger.info(f"Secret {secret_name} set in {owner}/{repo}")

    async def delete_repository(self, owner: str, repo: str) -> None:
        """Delete a repository (for cleanup on failure)."""
        async with aiohttp.ClientSession() as session:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            await self._api_request('DELETE', url, session)
            logger.info(f"Deleted repository {owner}/{repo}")


# ----------------------------------------------------------------------
# Main resource manager (integrates with database)
# ----------------------------------------------------------------------

class ResourceManager:
    """
    High‑level resource manager for HelixHive.
    Handles daughter spawning and tracks them in the database with Leech vectors.
    """

    def __init__(self, db: HelixDBGit, genome: Genome, config: Config):
        self.db = db
        self.genome = genome
        self.config = config
        self.github_app: Optional[GitHubApp] = None

    async def initialize(self):
        """Initialize GitHub App if configured."""
        self.github_app = await GitHubApp.create(self.genome)

    async def spawn_daughter(self, name: str, niche: str = "AI_coding_agents",
                             template_owner: Optional[str] = None,
                             template_repo: str = "helixhive-template",
                             custom_genome: Optional[Dict] = None) -> str:
        """
        Spawn a daughter repository from the HelixHive template.
        Returns the URL of the created repository.
        """
        if not self.github_app:
            raise RuntimeError("GitHub App not configured")

        # Get configuration
        if template_owner is None:
            template_owner = self.genome.get('template_owner') or os.environ.get('GITHUB_REPOSITORY_OWNER')
        new_owner = self.genome.get('daughter_owner') or template_owner

        if not template_owner:
            raise RuntimeError("Template owner not configured")

        # Create repository
        logger.info(f"Spawning daughter repository: {new_owner}/{name}")
        try:
            repo_url = await self.github_app.create_repository_from_template(
                template_owner=template_owner,
                template_repo=template_repo,
                new_owner=new_owner,
                new_name=name,
                description=f"Daughter of HelixHive, specialized in {niche}",
                private=False
            )
        except Exception as e:
            logger.error(f"Failed to create repository: {e}")
            raise

        # Set secrets
        async with aiohttp.ClientSession() as session:
            secrets_to_set = [
                ('GROQ_API_KEY', Vault.get('GROQ_API_KEY')),
                ('OPENROUTER_API_KEY', Vault.get('OPENROUTER_API_KEY')),
                ('GITHUB_TOKEN', Vault.get('GITHUB_TOKEN')),
                ('GITHUB_APP_ID', self.genome.get('github_app_id')),
                ('GITHUB_INSTALLATION_ID', self.genome.get('github_installation_id')),
            ]
            for secret_name, secret_value in secrets_to_set:
                if not secret_value:
                    continue
                try:
                    await self.github_app.set_repository_secret(new_owner, name, secret_name, secret_value, session)
                except Exception as e:
                    logger.error(f"Failed to set secret {secret_name}: {e}")
                    # Attempt to clean up: delete the partially created repo
                    try:
                        await self.github_app.delete_repository(new_owner, name)
                    except:
                        pass
                    raise RuntimeError(f"Failed to set secret {secret_name}, repository may be incomplete.")

        # Compute Leech vector for the daughter (based on niche and name)
        leech_vec = self._compute_daughter_leech(name, niche)

        # Record daughter in database
        daughter_id = f"daughter_{int(time.time())}_{name[:8]}"
        daughter_record = {
            'id': daughter_id,
            'type': 'Daughter',
            'name': name,
            'niche': niche,
            'repo_url': repo_url,
            'owner': new_owner,
            'repo_name': name,
            'leech_vector': leech_vec.tolist(),
            'created_at': time.time(),
            'status': 'active',
        }
        self.db.update_properties(daughter_id, daughter_record)
        self.db.update_vector(daughter_id, 'Daughter', 'leech', leech_vec)

        logger.info(f"Daughter repository spawned successfully: {repo_url}")
        return repo_url

    def _compute_daughter_leech(self, name: str, niche: str) -> np.ndarray:
        """
        Compute a Leech vector for the daughter based on name and niche.
        This can be used for similarity search and provenance.
        """
        text = f"{name} {niche}"
        words = text.split()[:100]
        if not words:
            return np.zeros(24, dtype=int)
        word_vecs = [HD.from_word(w) for w in words]
        hd_vec = HD.bundle(word_vecs)
        leech_float = np.dot(hd_vec.astype(np.float32), _LEECH_PROJ)
        return leech_encode(leech_float)

    async def list_daughters(self) -> List[Dict]:
        """Return all active daughter records."""
        daughters = self.db.get_nodes_by_type('Daughter')
        return [d for d in daughters.values() if d.get('status') == 'active']

    async def get_daughter(self, name: str) -> Optional[Dict]:
        """Find a daughter by name."""
        daughters = self.db.get_nodes_by_type('Daughter')
        for d in daughters.values():
            if d.get('name') == name:
                return d
        return None


# ----------------------------------------------------------------------
# Convenience functions for orchestrator
# ----------------------------------------------------------------------

_resource_manager_instance: Optional[ResourceManager] = None


async def get_resource_manager(db: HelixDBGit, genome: Genome, config: Config) -> ResourceManager:
    """Singleton resource manager."""
    global _resource_manager_instance
    if _resource_manager_instance is None:
        _resource_manager_instance = ResourceManager(db, genome, config)
        await _resource_manager_instance.initialize()
    return _resource_manager_instance


async def spawn_daughter(name: str, niche: str = "AI_coding_agents",
                         db: Optional[HelixDBGit] = None,
                         genome: Optional[Genome] = None,
                         config: Optional[Config] = None) -> str:
    """
    Spawn a daughter repository. If db/genome/config not provided, load them.
    """
    from genome import load_genome
    from config import load_config
    if db is None:
        from helixdb_git_adapter import HelixDBGit
        db = HelixDBGit()
    if genome is None:
        genome = load_genome()
    if config is None:
        config = load_config()

    mgr = await get_resource_manager(db, genome, config)
    return await mgr.spawn_daughter(name, niche)
