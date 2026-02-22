"""
Git‑backed database adapter for HelixHive Phase 2.

File structure inside the repo:
  helixdb/
    agents.jsonl          # JSON Lines: one agent per line
    products.jsonl
    factions.jsonl
    templates.jsonl
    proposals.jsonl
    vectors/              # Git LFS tracked directory
      <node_id>_<type>.npy  # Leech vectors as numpy binary files
    .gitattributes        # LFS config (auto‑generated)

Atomic commits: all changes are staged and committed together.
Locking: a `.lock` file prevents concurrent heartbeats.
"""

import os
import json
import time
import hashlib
import logging
import subprocess
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class HelixDBGit:
    """
    Git‑backed database with JSONL metadata and Git LFS for vectors.
    """

    # Supported node types (each corresponds to a .jsonl file)
    NODE_TYPES = ["Agent", "Product", "Faction", "Template", "Proposal", "FitnessRecord", "Transaction"]

    def __init__(self, repo_path: str = ".", lock_timeout: int = 60):
        """
        Args:
            repo_path: Path to the git repository root.
            lock_timeout: Seconds to wait for lock before giving up.
        """
        self.repo_path = Path(repo_path).resolve()
        self.db_path = self.repo_path / "helixdb"
        self.vectors_path = self.db_path / "vectors"
        self.lock_file = self.repo_path / ".helixhive.lock"
        self.lock_timeout = lock_timeout

        # Ensure directories exist
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.vectors_path.mkdir(parents=True, exist_ok=True)

        # Check/initialize Git LFS
        self._init_lfs()

        # In‑memory cache for the current heartbeat
        self._cache = {}          # node_id -> (node_type, data_dict, vector_path, vector)
        self._dirty = set()        # node_ids modified

    # -------------------------------------------------------------------------
    # Initialization and LFS setup
    # -------------------------------------------------------------------------

    def _init_lfs(self):
        """Ensure Git LFS is installed and configured for .npy files."""
        # Check if git is available
        try:
            subprocess.run(["git", "version"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("git is not installed or not in PATH")

        # Check if LFS is installed
        try:
            subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.warning("Git LFS not found; attempting to install...")
            subprocess.run(["git", "lfs", "install"], check=True)

        # Ensure .gitattributes tracks .npy files with LFS
        gitattributes_path = self.repo_path / ".gitattributes"
        if gitattributes_path.exists():
            with open(gitattributes_path, "r") as f:
                content = f.read()
            if "*.npy filter=lfs" not in content:
                with open(gitattributes_path, "a") as f:
                    f.write("\n*.npy filter=lfs diff=lfs merge=lfs -text\n")
        else:
            with open(gitattributes_path, "w") as f:
                f.write("*.npy filter=lfs diff=lfs merge=lfs -text\n")

        # Add .gitattributes to git if not already tracked
        subprocess.run(["git", "add", ".gitattributes"], cwd=self.repo_path, check=False)

    # -------------------------------------------------------------------------
    # Locking
    # -------------------------------------------------------------------------

    @contextmanager
    def _lock(self):
        """Acquire a file‑based lock with timeout."""
        start = time.time()
        while True:
            try:
                # Open in exclusive create mode – fails if file exists
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as f:
                    f.write(str(os.getpid()))
                break
            except FileExistsError:
                if time.time() - start > self.lock_timeout:
                    raise TimeoutError(f"Could not acquire lock after {self.lock_timeout}s")
                time.sleep(1)
        try:
            yield
        finally:
            os.remove(self.lock_file)

    # -------------------------------------------------------------------------
    # Loading and caching
    # -------------------------------------------------------------------------

    def _load_jsonl(self, node_type: str) -> Dict[str, Dict]:
        """
        Load all nodes of a given type from the corresponding .jsonl file.
        Returns dict mapping node_id -> node_data (including vector reference).
        """
        file_path = self.db_path / f"{node_type.lower()}s.jsonl"
        if not file_path.exists():
            return {}
        nodes = {}
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                node = json.loads(line)
                node_id = node.get("id")
                if node_id:
                    nodes[node_id] = node
        return nodes

    def _load_vector(self, node_id: str, node_type: str) -> Optional[np.ndarray]:
        """
        Load Leech vector from .npy file (if exists).
        """
        vec_path = self.vectors_path / f"{node_id}_{node_type}.npy"
        if vec_path.exists():
            return np.load(vec_path)
        return None

    def load_all(self):
        """
        Load all nodes and vectors into memory cache.
        Should be called at the beginning of each heartbeat.
        """
        self._cache.clear()
        self._dirty.clear()
        for nt in self.NODE_TYPES:
            nodes = self._load_jsonl(nt)
            for node_id, data in nodes.items():
                vec = self._load_vector(node_id, nt)
                # Store in cache: node_id -> (type, data, vector_path, vector)
                self._cache[node_id] = (nt, data, vec, vec is not None)

    def get_nodes_by_type(self, node_type: str) -> Dict[str, Dict]:
        """
        Return all nodes of a given type, with leech_vector included.
        (The vector is loaded from cache.)
        """
        result = {}
        for node_id, (nt, data, vec, has_vec) in self._cache.items():
            if nt == node_type:
                # Return a copy with vector added
                d = data.copy()
                if has_vec:
                    d["leech_vector"] = vec
                result[node_id] = d
        return result

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get a single node by ID (with vector)."""
        entry = self._cache.get(node_id)
        if not entry:
            return None
        nt, data, vec, has_vec = entry
        d = data.copy()
        if has_vec:
            d["leech_vector"] = vec
        return d

    def update_vector(self, node_id: str, node_type: str, vec: np.ndarray):
        """
        Update the Leech vector for a node.
        The change is recorded in cache and marked dirty.
        Actual file write happens during commit.
        """
        if node_id not in self._cache:
            # New node – create minimal entry
            self._cache[node_id] = (node_type, {"id": node_id}, vec, True)
        else:
            nt, data, old_vec, _ = self._cache[node_id]
            # Ensure type matches
            if nt != node_type:
                raise ValueError(f"Node {node_id} type mismatch: {nt} vs {node_type}")
            self._cache[node_id] = (nt, data, vec, True)
        self._dirty.add(node_id)

    def update_properties(self, node_id: str, properties: Dict):
        """
        Update JSON properties of a node (without changing vector).
        """
        if node_id not in self._cache:
            raise KeyError(f"Node {node_id} not found")
        nt, data, vec, has_vec = self._cache[node_id]
        data.update(properties)
        self._cache[node_id] = (nt, data, vec, has_vec)
        self._dirty.add(node_id)

    # -------------------------------------------------------------------------
    # Commit
    # -------------------------------------------------------------------------

    def commit(self, tick: int, summary: str = ""):
        """
        Atomically commit all changes to git.
        Must be called after all modifications.
        """
        if not self._dirty:
            logger.debug("No changes to commit.")
            return

        with self._lock():
            # Ensure we are on the latest main
            self._git_pull()

            # Write updated JSONL files for each type
            for nt in self.NODE_TYPES:
                self._write_jsonl(nt)

            # Write dirty vectors
            for node_id in self._dirty:
                nt, data, vec, has_vec = self._cache[node_id]
                if has_vec:
                    vec_path = self.vectors_path / f"{node_id}_{nt}.npy"
                    np.save(vec_path, vec)

            # Stage changes
            subprocess.run(["git", "add", "helixdb"], cwd=self.repo_path, check=True)

            # Commit
            msg = f"Heartbeat {tick}: {len(self._dirty)} nodes changed"
            if summary:
                msg += f" ({summary})"
            subprocess.run(["git", "commit", "-m", msg], cwd=self.repo_path, check=True)

            # Push with retries on conflict
            self._git_push_with_retry()

            # Clear dirty set after successful push
            self._dirty.clear()
            logger.info(f"Committed {len(self._dirty)} changes (tick {tick})")

    def _write_jsonl(self, node_type: str):
        """Write all nodes of a given type to the .jsonl file."""
        file_path = self.db_path / f"{node_type.lower()}s.jsonl"
        nodes = []
        for node_id, (nt, data, vec, has_vec) in self._cache.items():
            if nt == node_type:
                # For JSON, we do NOT store the vector; only metadata
                nodes.append(data)
        # Sort by id for deterministic output
        nodes.sort(key=lambda x: x.get("id", ""))
        with open(file_path, "w") as f:
            for node in nodes:
                f.write(json.dumps(node) + "\n")

    def _git_pull(self):
        """Pull latest changes (fast‑forward only)."""
        subprocess.run(["git", "pull", "--ff-only"], cwd=self.repo_path, check=True)

    def _git_push_with_retry(self, max_retries=3):
        """Push with exponential backoff on conflict."""
        for attempt in range(max_retries):
            try:
                subprocess.run(["git", "push"], cwd=self.repo_path, check=True)
                return
            except subprocess.CalledProcessError as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** attempt
                logger.warning(f"Push failed (attempt {attempt+1}), retrying in {wait}s")
                time.sleep(wait)
                # Pull again to incorporate remote changes
                self._git_pull()

    # -------------------------------------------------------------------------
    # Self‑test
    # -------------------------------------------------------------------------

    def self_test(self):
        """Run a basic integrity test in a temporary directory."""
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize a git repo
            subprocess.run(["git", "init"], cwd=tmpdir, check=True)
            subprocess.run(["git", "lfs", "install"], cwd=tmpdir, check=True)

            db = HelixDBGit(repo_path=tmpdir)
            db.load_all()

            # Create a test node
            test_vec = np.random.randn(24)
            db.update_vector("test-agent", "Agent", test_vec)
            db.update_properties("test-agent", {"name": "Test"})

            # Commit
            db.commit(tick=0, summary="test")

            # Reload into a new instance
            db2 = HelixDBGit(repo_path=tmpdir)
            db2.load_all()
            node = db2.get_node("test-agent")
            assert node is not None
            assert np.allclose(node["leech_vector"], test_vec)
            assert node.get("name") == "Test"
            logger.info("Self‑test passed.")
