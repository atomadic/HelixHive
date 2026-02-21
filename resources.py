"""
External Resources Manager for HelixHive – handles GitHub App authentication,
daughter repository spawning, and secure secret management.
"""

import os
import time
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import jwt
from nacl import public
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import Config

logger = logging.getLogger(__name__)


class Vault:
    """Simple secret vault that reads from environment variables."""

    @staticmethod
    def get(key: str) -> Optional[str]:
        return os.environ.get(key)


class GitHubApp:
    """GitHub App authentication and API operations."""

    def __init__(self, app_id: str, private_key_path: str, installation_id: str):
        self.app_id = app_id
        self.installation_id = installation_id
        self._private_key = self._load_private_key(private_key_path)
        self._token_cache = {}

    def _load_private_key(self, path: str) -> str:
        with open(path, 'r') as f:
            return f.read()

    def _generate_jwt(self) -> str:
        now = int(time.time())
        payload = {'iat': now, 'exp': now + 600, 'iss': self.app_id}
        return jwt.encode(payload, self._private_key, algorithm='RS256')

    def _get_installation_token(self) -> str:
        now = time.time()
        cached = self._token_cache.get(self.installation_id)
        if cached and cached[1] > now + 60:
            return cached[0]

        jwt_token = self._generate_jwt()
        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
        headers = {'Authorization': f'Bearer {jwt_token}', 'Accept': 'application/vnd.github.v3+json'}

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
               retry=retry_if_exception_type(requests.exceptions.RequestException))
        def _request():
            resp = requests.post(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()

        data = _request()
        token = data['token']
        expires_at = data['expires_at']
        expiry = time.mktime(time.strptime(expires_at, "%Y-%m-%dT%H:%M:%SZ"))
        self._token_cache[self.installation_id] = (token, expiry)
        return token

    def _api_request(self, method: str, url: str, json: Optional[Dict] = None) -> Dict:
        token = self._get_installation_token()
        headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
               retry=retry_if_exception_type(requests.exceptions.RequestException))
        def _request():
            resp = requests.request(method, url, headers=headers, json=json, timeout=30)
            if resp.status_code == 403 and 'rate limit' in resp.text.lower():
                raise requests.exceptions.RequestException("Rate limited")
            resp.raise_for_status()
            return resp

        resp = _request()
        return resp.json() if resp.content else {}

    def create_repository_from_template(self, template_owner: str, template_repo: str,
                                        new_owner: str, new_name: str,
                                        description: str = "", private: bool = False) -> str:
        url = f"https://api.github.com/repos/{template_owner}/{template_repo}/generate"
        payload = {
            'owner': new_owner,
            'name': new_name,
            'description': description,
            'private': private,
            'include_all_branches': False
        }
        result = self._api_request('POST', url, json=payload)
        # Wait for repo to be ready (polling)
        self._wait_for_repo_ready(new_owner, new_name)
        return result.get('html_url', f"https://github.com/{new_owner}/{new_name}")

    def _wait_for_repo_ready(self, owner: str, repo: str, timeout: int = 60) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            try:
                url = f"https://api.github.com/repos/{owner}/{repo}"
                self._api_request('GET', url)
                return True
            except:
                time.sleep(2)
        return False

    def set_repository_secret(self, owner: str, repo: str, secret_name: str, secret_value: str) -> None:
        key_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
        key_data = self._api_request('GET', key_url)
        public_key = key_data['key']
        key_id = key_data['key_id']

        pub = public.PublicKey(public_key.encode('utf-8'))
        sealed_box = public.SealedBox(pub)
        encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')

        secret_url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
        payload = {'encrypted_value': encrypted_b64, 'key_id': key_id}
        self._api_request('PUT', secret_url, json=payload)

    def delete_repository(self, owner: str, repo: str) -> None:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        self._api_request('DELETE', url)


_github_app: Optional[GitHubApp] = None


def get_github_app() -> Optional[GitHubApp]:
    global _github_app
    if _github_app is not None:
        return _github_app

    config = Config.load()
    app_id = config.data.get('github_app_id')
    key_path = config.data.get('github_private_key_path')
    installation_id = config.data.get('github_installation_id')

    if not app_id or not key_path or not installation_id:
        return None

    key_path = Path(key_path)
    if not key_path.is_absolute():
        key_path = Path(__file__).parent / key_path
    if not key_path.exists():
        return None

    _github_app = GitHubApp(str(app_id), str(key_path), str(installation_id))
    return _github_app


def spawn_daughter(name: str, niche: str = "AI_coding_agents",
                   template_owner: Optional[str] = None,
                   template_repo: str = "helixhive-template") -> str:
    app = get_github_app()
    if not app:
        raise RuntimeError("GitHub App not configured")

    config = Config.load()
    if template_owner is None:
        template_owner = config.data.get('template_owner', os.environ.get('GITHUB_REPOSITORY_OWNER'))
    new_owner = config.data.get('daughter_owner', template_owner)

    if not template_owner:
        raise RuntimeError("Template owner not configured")

    repo_url = app.create_repository_from_template(
        template_owner=template_owner,
        template_repo=template_repo,
        new_owner=new_owner,
        new_name=name,
        description=f"Daughter of HelixHive, specialized in {niche}",
        private=False
    )

    # Set secrets
    secrets = [
        ('GROQ_API_KEY', Vault.get('GROQ_API_KEY')),
        ('OPENROUTER_API_KEY', Vault.get('OPENROUTER_API_KEY')),
        ('GITHUB_TOKEN', Vault.get('GITHUB_TOKEN')),
    ]
    for secret_name, secret_value in secrets:
        if secret_value:
            app.set_repository_secret(new_owner, name, secret_name, secret_value)

    return repo_url
