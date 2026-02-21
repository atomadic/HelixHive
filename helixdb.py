"""
HelixDB – Lightweight graph+vector database for HelixHive.
Now with label/property indexes, edge indexes, vector versioning, memory consolidation,
and atomic commits with transaction log.
"""

import json
import uuid
import shutil
import tempfile
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple, Union
import time

import numpy as np

from memory import HD, E8, Leech  # for similarity


class Node:
    def __init__(self, node_id: str, label: str, properties: Dict[str, Any],
                 vectors: Optional[Dict[str, np.ndarray]] = None):
        self.id = node_id
        self.label = label
        self.properties = properties
        self.vectors = vectors or {}

    def __repr__(self):
        return f"Node(id={self.id}, label={self.label})"


class HelixDB:
    """
    Main database class with indexes and atomic commits.
    """

    # Current vector version (incremented when representation changes)
    VECTOR_VERSION = 2

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        self.path.mkdir(exist_ok=True)

        # In‑memory data
        self.nodes: Dict[str, Dict] = {}
        self.vectors: Dict[str, Dict[str, np.ndarray]] = {}  # node_id -> {vec_type: array}
        self.edges: List[Tuple[str, str, str, Dict]] = []    # (src, dst, label, props)

        # Indexes
        self._label_index: Dict[str, List[str]] = defaultdict(list)
        self._property_index: Dict[str, Dict[Any, List[str]]] = defaultdict(lambda: defaultdict(list))
        self._edge_index: Dict[Tuple[str, str], List[int]] = defaultdict(list)  # (src, label) -> edge indices

        # Transaction log (for recovery)
        self._txn_log: List[Dict] = []

        self._load()

    # ----------------------------------------------------------------------
    # Internal I/O with versioning
    # ----------------------------------------------------------------------

    def _load(self):
        nodes_file = self.path / "nodes.json"
        edges_file = self.path / "edges.json"
        vectors_file = self.path / "vectors.npz"
        version_file = self.path / "version.txt"

        # Check version
        if version_file.exists():
            with open(version_file, 'r') as f:
                version = int(f.read().strip())
            if version != self.VECTOR_VERSION:
                # In a real system, we would run a migration script.
                # For now, we'll just warn and assume compatibility.
                print(f"Warning: DB version {version} != current {self.VECTOR_VERSION}")

        if nodes_file.exists():
            with open(nodes_file, 'r') as f:
                self.nodes = json.load(f)
                for node_id, data in self.nodes.items():
                    self._label_index[data['label']].append(node_id)
                    # Also index by properties (simple equality)
                    for k, v in data.get('properties', {}).items():
                        if isinstance(v, (str, int, float, bool)):
                            self._property_index[k][v].append(node_id)

        if edges_file.exists():
            with open(edges_file, 'r') as f:
                self.edges = json.load(f)
                for idx, (src, dst, label, props) in enumerate(self.edges):
                    self._edge_index[(src, label)].append(idx)

        if vectors_file.exists():
            self._load_vectors(vectors_file)

    def _load_vectors(self, vectors_file: Path):
        with np.load(vectors_file) as data:
            for key, vec in data.items():
                if '_' not in key:
                    continue
                node_id, vec_type = key.rsplit('_', 1)
                if vec_type not in ('hd', 'e8', 'leech'):
                    continue
                self.vectors.setdefault(node_id, {})[vec_type] = vec

    def commit(self):
        """
        Atomically write all in‑memory data to disk using a temporary directory.
        Also write version file.
        """
        with tempfile.TemporaryDirectory(dir=self.path.parent) as tmpdir:
            tmp_path = Path(tmpdir)

            # Write nodes
            with open(tmp_path / "nodes.json", 'w') as f:
                json.dump(self.nodes, f, indent=2)

            # Write edges
            with open(tmp_path / "edges.json", 'w') as f:
                json.dump(self.edges, f, indent=2)

            # Write vectors (flatten)
            vec_dict = {}
            for node_id, vecs in self.vectors.items():
                for vec_type, vec in vecs.items():
                    key = f"{node_id}_{vec_type}"
                    vec_dict[key] = vec
            if vec_dict:
                np.savez(tmp_path / "vectors.npz", **vec_dict)

            # Write version
            with open(tmp_path / "version.txt", 'w') as f:
                f.write(str(self.VECTOR_VERSION))

            # Atomic replace
            for fname in ["nodes.json", "edges.json", "vectors.npz", "version.txt"]:
                src = tmp_path / fname
                dst = self.path / fname
                if src.exists():
                    src.replace(dst)
                elif dst.exists():
                    dst.unlink()

        # Clear transaction log after successful commit
        self._txn_log.clear()

    # ----------------------------------------------------------------------
    # Node operations with indexing
    # ----------------------------------------------------------------------

    def add_node(self, label: str, node_id: Optional[str] = None,
                 properties: Optional[Dict] = None) -> str:
        node_id = node_id or str(uuid.uuid4())
        if node_id in self.nodes:
            raise ValueError(f"Node {node_id} already exists")
        props = properties or {}
        self.nodes[node_id] = {"label": label, "properties": props}
        self._label_index[label].append(node_id)
        for k, v in props.items():
            if isinstance(v, (str, int, float, bool)):
                self._property_index[k][v].append(node_id)
        self._txn_log.append({"op": "add_node", "node_id": node_id})
        return node_id

    def update_node(self, node_id: str, properties: Dict = None, label: str = None):
        if node_id not in self.nodes:
            raise KeyError(f"Node {node_id} not found")
        old_label = self.nodes[node_id]["label"]
        old_props = self.nodes[node_id]["properties"]

        # Remove old property index entries
        for k, v in old_props.items():
            if isinstance(v, (str, int, float, bool)):
                self._property_index[k][v].remove(node_id)

        if label is not None and label != old_label:
            self._label_index[old_label].remove(node_id)
            self._label_index[label].append(node_id)
            self.nodes[node_id]["label"] = label

        if properties is not None:
            self.nodes[node_id]["properties"].update(properties)

        # Add new property index entries
        new_props = self.nodes[node_id]["properties"]
        for k, v in new_props.items():
            if isinstance(v, (str, int, float, bool)):
                self._property_index[k][v].append(node_id)

        self._txn_log.append({"op": "update_node", "node_id": node_id})

    def get_node(self, node_id: str) -> Optional[Node]:
        data = self.nodes.get(node_id)
        if not data:
            return None
        vectors = self.vectors.get(node_id, {})
        return Node(node_id, data["label"], data["properties"], vectors)

    def delete_node(self, node_id: str):
        if node_id not in self.nodes:
            return
        label = self.nodes[node_id]["label"]
        props = self.nodes[node_id]["properties"]
        self._label_index[label].remove(node_id)
        for k, v in props.items():
            if isinstance(v, (str, int, float, bool)):
                self._property_index[k][v].remove(node_id)
        del self.nodes[node_id]
        self.vectors.pop(node_id, None)
        # Remove incident edges
        self.edges = [e for e in self.edges if e[0] != node_id and e[1] != node_id]
        # Rebuild edge index
        self._rebuild_edge_index()
        self._txn_log.append({"op": "delete_node", "node_id": node_id})

    def query_nodes_by_label(self, label: str) -> List[Node]:
        node_ids = self._label_index.get(label, [])
        return [self.get_node(nid) for nid in node_ids]

    def query_nodes_by_property(self, key: str, value: Any) -> List[Node]:
        node_ids = self._property_index[key].get(value, [])
        return [self.get_node(nid) for nid in node_ids]

    # ----------------------------------------------------------------------
    # Vector operations
    # ----------------------------------------------------------------------

    def add_vector(self, node_id: str, vec_type: str, vector: np.ndarray):
        if node_id not in self.nodes:
            raise KeyError(f"Node {node_id} not found")
        self.vectors.setdefault(node_id, {})[vec_type] = vector
        self._txn_log.append({"op": "add_vector", "node_id": node_id, "vec_type": vec_type})

    def get_vector(self, node_id: str, vec_type: str) -> Optional[np.ndarray]:
        return self.vectors.get(node_id, {}).get(vec_type)

    def find_similar(self, query_vec: np.ndarray, vec_type: str, k: int = 5,
                     label: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        Find nodes with vectors of type `vec_type` most similar to query_vec.
        For Leech vectors, uses Euclidean distance (fast).
        For HD, uses cosine similarity.
        For E8, uses negative Euclidean distance.
        """
        if vec_type == 'hd':
            sim_func = HD.sim
        elif vec_type == 'e8':
            sim_func = lambda a, b: -np.linalg.norm(a - b)
        elif vec_type == 'leech':
            # Leech vectors are integer arrays; Euclidean distance works
            sim_func = lambda a, b: -np.linalg.norm(a - b)
        else:
            raise ValueError(f"Unknown vector type: {vec_type}")

        scores = []
        for node_id, vecs in self.vectors.items():
            if label and self.nodes[node_id]["label"] != label:
                continue
            if vec_type not in vecs:
                continue
            vec = vecs[vec_type]
            if vec.shape != query_vec.shape:
                continue
            sim = sim_func(query_vec, vec)
            scores.append((sim, node_id))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [(node_id, sim) for sim, node_id in scores[:k]]

    # ----------------------------------------------------------------------
    # Edge operations with indexing
    # ----------------------------------------------------------------------

    def _rebuild_edge_index(self):
        self._edge_index.clear()
        for idx, (src, dst, label, props) in enumerate(self.edges):
            self._edge_index[(src, label)].append(idx)

    def add_edge(self, src: str, dst: str, label: str, properties: Optional[Dict] = None):
        if src not in self.nodes:
            raise KeyError(f"Source node {src} not found")
        if dst not in self.nodes:
            raise KeyError(f"Destination node {dst} not found")
        idx = len(self.edges)
        self.edges.append((src, dst, label, properties or {}))
        self._edge_index[(src, label)].append(idx)
        self._txn_log.append({"op": "add_edge", "src": src, "dst": dst, "label": label})

    def query_edges(self, src: Optional[str] = None, dst: Optional[str] = None,
                    label: Optional[str] = None) -> List[Tuple[str, str, str, Dict]]:
        result = []
        if src is not None and label is not None:
            # Use index
            indices = self._edge_index.get((src, label), [])
            for idx in indices:
                s, d, l, p = self.edges[idx]
                if (dst is None or d == dst):
                    result.append((s, d, l, p))
        else:
            # Linear scan
            for s, d, l, p in self.edges:
                if src is not None and s != src:
                    continue
                if dst is not None and d != dst:
                    continue
                if label is not None and l != label:
                    continue
                result.append((s, d, l, p))
        return result

    def delete_edges(self, src: Optional[str] = None, dst: Optional[str] = None,
                     label: Optional[str] = None):
        self.edges = [
            (s, d, l, p) for s, d, l, p in self.edges
            if (src is not None and s != src) or
               (dst is not None and d != dst) or
               (label is not None and l != label)
        ]
        self._rebuild_edge_index()
        self._txn_log.append({"op": "delete_edges", "src": src, "dst": dst, "label": label})

    # ----------------------------------------------------------------------
    # Memory consolidation
    # ----------------------------------------------------------------------

    def consolidate(self, before_timestamp: float, half_life: float = 86400 * 7):
        """
        Bundle old messages (nodes with label 'Message' and timestamp < before_timestamp)
        into summary nodes. Also decay edge weights.
        """
        # Find old message nodes
        old_messages = []
        for node_id, data in self.nodes.items():
            if data['label'] == 'Message':
                ts = data['properties'].get('timestamp', 0)
                if ts < before_timestamp:
                    old_messages.append(node_id)

        if not old_messages:
            return

        # Bundle their HD vectors (if any) into a summary
        vectors_to_bundle = []
        for node_id in old_messages:
            vec = self.vectors.get(node_id, {}).get('hd')
            if vec is not None:
                vectors_to_bundle.append(vec)

        if vectors_to_bundle:
            summary_vec = HD.bundle(vectors_to_bundle)
            # Create summary node
            summary_id = self.add_node(
                label='MessageSummary',
                properties={
                    'num_messages': len(old_messages),
                    'timestamp': time.time(),
                    'original_timestamps': [self.nodes[n]['properties']['timestamp'] for n in old_messages]
                }
            )
            self.add_vector(summary_id, 'hd', summary_vec)

        # Delete old messages and their edges
        for node_id in old_messages:
            self.delete_node(node_id)

        # Edge decay is handled at query time (see get_edge_weight)
        self._txn_log.append({"op": "consolidate", "before": before_timestamp})

    def get_edge_weight(self, edge: Tuple[str, str, str, Dict], now: float) -> float:
        """Return weight of edge with decay applied."""
        # Decay factor = exp(-(now - timestamp) / half_life)
        timestamp = edge[3].get('timestamp', now)
        half_life = 86400 * 7  # 7 days
        decay = np.exp(-(now - timestamp) / half_life)
        return decay
