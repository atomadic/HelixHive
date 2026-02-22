
import os
import json
import shutil
import time
import hashlib
import glob

class RollbackSystem:
    """
    Robust Rollback System for SRA
    Provides versioned snapshots of all source files with instant rollback capability.
    
    Features:
    - Automatic snapshots before any modification
    - Content-addressable storage (SHA-256 deduplication)
    - Rollback to any named checkpoint
    - Diff viewing between versions
    - Integrity verification via checksums
    """
    def __init__(self, project_root, snapshot_dir=None):
        self.project_root = os.path.abspath(project_root)
        self.snapshot_dir = snapshot_dir or os.path.join(self.project_root, "data", "rollback")
        self.manifest_file = os.path.join(self.snapshot_dir, "manifest.json")
        self.objects_dir = os.path.join(self.snapshot_dir, "objects")
        
        os.makedirs(self.objects_dir, exist_ok=True)
        
        self.manifest = self._load_manifest()

    def _load_manifest(self):
        if os.path.exists(self.manifest_file):
            with open(self.manifest_file, "r") as f:
                return json.load(f)
        return {"snapshots": [], "current_head": None}

    def _save_manifest(self):
        with open(self.manifest_file, "w") as f:
            json.dump(self.manifest, f, indent=2)

    def _hash_content(self, content):
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _store_object(self, content):
        """Content-addressable storage: store by SHA-256 hash."""
        obj_hash = self._hash_content(content)
        obj_path = os.path.join(self.objects_dir, obj_hash)
        if not os.path.exists(obj_path):
            with open(obj_path, "w", encoding="utf-8") as f:
                f.write(content)
        return obj_hash

    def _retrieve_object(self, obj_hash):
        """Retrieve stored content by hash."""
        obj_path = os.path.join(self.objects_dir, obj_hash)
        if os.path.exists(obj_path):
            with open(obj_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def create_snapshot(self, name, description=""):
        """
        Create a named snapshot of all source files.
        """
        print(f"[Rollback] Creating snapshot: {name}")
        
        file_hashes = {}
        file_count = 0
        
        src_dir = os.path.join(self.project_root, "src")
        for root, dirs, files in os.walk(src_dir):
            # Skip __pycache__
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fname in files:
                if fname.endswith(".py"):
                    filepath = os.path.join(root, fname)
                    rel_path = os.path.relpath(filepath, self.project_root)
                    
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    obj_hash = self._store_object(content)
                    file_hashes[rel_path] = {
                        "hash": obj_hash,
                        "size": len(content),
                        "lines": content.count("\n") + 1
                    }
                    file_count += 1
        
        snapshot = {
            "name": name,
            "description": description,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "file_count": file_count,
            "files": file_hashes,
            "id": hashlib.sha256(f"{name}{time.time()}".encode()).hexdigest()[:12]
        }
        
        self.manifest["snapshots"].append(snapshot)
        self.manifest["current_head"] = snapshot["id"]
        self._save_manifest()
        
        print(f"[Rollback] Snapshot '{name}' created: {file_count} files, ID={snapshot['id']}")
        return snapshot

    def rollback(self, snapshot_name_or_id):
        """
        Rollback all source files to a named snapshot.
        Creates a safety snapshot of current state before rollback.
        """
        target = self._find_snapshot(snapshot_name_or_id)
        if not target:
            print(f"[Rollback] ERROR: Snapshot '{snapshot_name_or_id}' not found")
            return {"status": "error", "reason": "Snapshot not found"}
        
        # Safety: snapshot current state before rollback
        safety_name = f"pre_rollback_{int(time.time())}"
        self.create_snapshot(safety_name, f"Auto-snapshot before rollback to '{target['name']}'")
        
        print(f"[Rollback] Rolling back to '{target['name']}' ({target['timestamp']})...")
        
        restored = 0
        errors = 0
        
        for rel_path, file_info in target["files"].items():
            full_path = os.path.join(self.project_root, rel_path)
            content = self._retrieve_object(file_info["hash"])
            
            if content is not None:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                restored += 1
            else:
                print(f"   Missing object for {rel_path}")
                errors += 1
        
        self.manifest["current_head"] = target["id"]
        self._save_manifest()
        
        print(f"[Rollback] Complete: {restored} restored, {errors} errors")
        return {"status": "success", "restored": restored, "errors": errors, "target": target["name"]}

    def diff(self, snapshot_a, snapshot_b=None):
        """
        Show differences between two snapshots.
        If snapshot_b is None, compare snapshot_a to current state.
        """
        snap_a = self._find_snapshot(snapshot_a)
        if not snap_a:
            return {"error": f"Snapshot '{snapshot_a}' not found"}
        
        if snapshot_b:
            snap_b = self._find_snapshot(snapshot_b)
            if not snap_b:
                return {"error": f"Snapshot '{snapshot_b}' not found"}
            files_b = snap_b["files"]
        else:
            # Compare to current working tree
            files_b = {}
            src_dir = os.path.join(self.project_root, "src")
            for root, dirs, files in os.walk(src_dir):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for fname in files:
                    if fname.endswith(".py"):
                        filepath = os.path.join(root, fname)
                        rel_path = os.path.relpath(filepath, self.project_root)
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        files_b[rel_path] = {"hash": self._hash_content(content), "size": len(content)}
        
        added = []
        removed = []
        modified = []
        unchanged = []
        
        all_paths = set(list(snap_a["files"].keys()) + list(files_b.keys()))
        
        for path in sorted(all_paths):
            in_a = path in snap_a["files"]
            in_b = path in files_b
            
            if in_a and in_b:
                if snap_a["files"][path]["hash"] == files_b[path]["hash"]:
                    unchanged.append(path)
                else:
                    modified.append(path)
            elif in_a:
                removed.append(path)
            else:
                added.append(path)
        
        return {
            "added": added,
            "removed": removed,
            "modified": modified,
            "unchanged_count": len(unchanged),
            "total_changes": len(added) + len(removed) + len(modified)
        }

    def verify_integrity(self, snapshot_name_or_id=None):
        """Verify all stored objects are intact."""
        if snapshot_name_or_id:
            snapshots = [self._find_snapshot(snapshot_name_or_id)]
        else:
            snapshots = self.manifest["snapshots"]
        
        total = 0
        valid = 0
        missing = 0
        
        for snap in snapshots:
            if not snap:
                continue
            for rel_path, info in snap["files"].items():
                total += 1
                content = self._retrieve_object(info["hash"])
                if content is not None:
                    actual_hash = self._hash_content(content)
                    if actual_hash == info["hash"]:
                        valid += 1
                    else:
                        print(f"   CORRUPT: {rel_path} in {snap['name']}")
                else:
                    missing += 1
        
        return {"total": total, "valid": valid, "missing": missing, "integrity": valid / total if total > 0 else 1.0}

    def list_snapshots(self):
        """List all available snapshots."""
        return [{
            "name": s["name"],
            "id": s["id"],
            "timestamp": s["timestamp"],
            "file_count": s["file_count"],
            "description": s.get("description", "")
        } for s in self.manifest["snapshots"]]

    def _find_snapshot(self, name_or_id):
        for s in self.manifest["snapshots"]:
            if s["name"] == name_or_id or s["id"] == name_or_id:
                return s
        return None

    def cleanup_old(self, keep_count=10):
        """Remove old snapshots, keeping the most recent ones."""
        if len(self.manifest["snapshots"]) <= keep_count:
            return 0
        
        removed = len(self.manifest["snapshots"]) - keep_count
        self.manifest["snapshots"] = self.manifest["snapshots"][-keep_count:]
        self._save_manifest()
        print(f"[Rollback] Cleaned up {removed} old snapshots")
        return removed
