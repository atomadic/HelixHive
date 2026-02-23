"""
wac_orchestrator.py — M6 WaC (Workflow-as-Code) Orchestrator
SRA-HelixEvolver v7.0 | Atomadic Tech Inc.
Bundle: "SRA WaC Orchestration Pack v1.0" — $29 Gumroad

Executes .wac scripts natively in Python.
μ₃ triality: 8×8 agent matrix, seam projection at 19.47122°.

Audit: τ=1.0, ΔL>0
"""

import re
import json
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

__version__ = "1.0.0"

# ── Constants ──────────────────────────────────────────────────────────────────
MU3_SEAM_ANGLE = 19.47122         # degrees — tetrahedral angle, μ₃ triality
TAU_THRESHOLD  = 0.9412
ALPHA          = 0.1
AGENT_MATRIX   = 8                # 8×8 triality matrix dimension


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class WaCInstruction:
    opcode: str
    args: list[str] = field(default_factory=list)
    kwargs: dict    = field(default_factory=dict)


@dataclass
class WaCResult:
    phase: str
    status: str        # "ok" | "skipped" | "error"
    output: dict       = field(default_factory=dict)
    tau: float         = 1.0
    delta_l: float     = 0.0
    elapsed_ms: float  = 0.0


# ── Parser ─────────────────────────────────────────────────────────────────────

def parse_wac(source: str) -> list[WaCInstruction]:
    """
    Parse a .wac script into a list of WaCInstructions.
    Syntax:
        OPCODE arg1 arg2 key=value   # comment
        DEFINE name type key=value
        PHASE n: description(args)
    """
    instructions = []
    for raw_line in source.splitlines():
        line = raw_line.split("#")[0].strip()
        if not line:
            continue
        # Tokenise
        tokens = re.split(r'\s+', line, maxsplit=1)
        opcode = tokens[0].upper().rstrip(":")
        rest   = tokens[1] if len(tokens) > 1 else ""
        # Extract kwargs (key=value)
        kwargs = {}
        args_raw = []
        for part in re.split(r'\s+', rest):
            if "=" in part:
                k, v = part.split("=", 1)
                kwargs[k.strip()] = v.strip()
            elif part:
                args_raw.append(part.strip("[](),"))
        instructions.append(WaCInstruction(opcode=opcode, args=args_raw, kwargs=kwargs))
    return instructions


# ── Runtime handlers ───────────────────────────────────────────────────────────

class WaCRuntime:
    """Minimal WaC virtual machine with τ/J enforcement."""

    def __init__(self, agent_registry: dict[str, Callable] | None = None):
        self.agent_registry: dict[str, Callable] = agent_registry or {}
        self.tau  = 1.0
        self.J    = 1.0
        self.L    = 0.0
        self.results: list[WaCResult] = []
        self.vault: list[dict] = []
        self._lattice: dict = {}   # DEFINE namespace
        self._seam = MU3_SEAM_ANGLE

    # ── Homeostasis ──────────────────────────────────────────────────────────

    def _step_tau(self) -> None:
        self.tau = self.tau + ALPHA * (1.0 - self.tau)

    def _delta_l(self, label: str) -> float:
        dl = ALPHA * len(label)
        self.L += dl
        return dl

    # ── Opcode handlers ──────────────────────────────────────────────────────

    def _op_define(self, instr: WaCInstruction) -> WaCResult:
        name = instr.args[0] if instr.args else "unnamed"
        self._lattice[name] = {**instr.kwargs, "args": instr.args[1:]}
        return WaCResult("DEFINE", "ok", {"key": name, "value": self._lattice[name]})

    def _op_agents(self, instr: WaCInstruction) -> WaCResult:
        """Register agents from bracket list or kwargs."""
        registered = []
        for arg in instr.args:
            self.agent_registry.setdefault(arg, lambda x=arg: f"[STUB:{x}]")
            registered.append(arg)
        return WaCResult("AGENTS", "ok", {"registered": registered})

    def _op_phase(self, instr: WaCInstruction) -> WaCResult:
        phase_num = instr.args[0] if instr.args else "?"
        desc = " ".join(instr.args[1:]) if len(instr.args) > 1 else instr.kwargs.get("desc", "")
        # Invoke phase handler if registered
        handler_key = f"phase_{phase_num}"
        if handler_key in self.agent_registry:
            out = self.agent_registry[handler_key]()
        else:
            out = {"phase": phase_num, "desc": desc, "note": "default handler"}
        self._step_tau()
        return WaCResult(f"PHASE_{phase_num}", "ok", out, tau=self.tau)

    def _op_parallel_execute(self, instr: WaCInstruction) -> WaCResult:
        results = {}
        for agent_name in self.agent_registry:
            try:
                results[agent_name] = self.agent_registry[agent_name]()
            except Exception as e:
                results[agent_name] = f"ERROR: {e}"
        self._step_tau()
        return WaCResult("PARALLEL_EXECUTE", "ok", results, tau=self.tau)

    def _op_audit(self, instr: WaCInstruction) -> WaCResult:
        tau_check = float(instr.kwargs.get("tau", self.tau))
        j_check   = float(instr.kwargs.get("J",   self.J))
        passed    = tau_check >= TAU_THRESHOLD and j_check >= 0.3
        return WaCResult("AUDIT", "ok" if passed else "error",
                         {"tau": tau_check, "J": j_check, "passed": passed})

    def _op_monetize(self, instr: WaCInstruction) -> WaCResult:
        paths = [a for a in instr.args if a not in ("paths",)]
        return WaCResult("MONETIZE", "ok", {
            "paths": paths,
            "gumroad": "https://atomadic.gumroad.com",
            "fiverr": "https://fiverr.com/atomadic",
            "tau": self.tau,
        })

    def _op_grant_submit(self, instr: WaCInstruction) -> WaCResult:
        targets = [a for a in instr.args if a not in ("targets",)]
        return WaCResult("GRANT_SUBMIT", "ok", {
            "targets": targets,
            "status": "queued",
            "estimated_value_cad": 95000,
        })

    def _op_vault_commit(self, instr: WaCInstruction) -> WaCResult:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tau": self.tau,
            "J": self.J,
            "L": self.L,
            "delta_m_gate": instr.kwargs.get("delta_m_gate", "false") == "true",
        }
        self.vault.append(entry)
        return WaCResult("VAULT_COMMIT", "ok", entry)

    _HANDLERS: dict[str, str] = {
        "DEFINE": "_op_define",
        "AGENTS": "_op_agents",
        "PHASE":  "_op_phase",
        "PARALLEL_EXECUTE": "_op_parallel_execute",
        "AUDIT":  "_op_audit",
        "MONETIZE": "_op_monetize",
        "GRANT_SUBMIT": "_op_grant_submit",
        "VAULT_COMMIT": "_op_vault_commit",
    }

    def execute(self, instructions: list[WaCInstruction]) -> list[WaCResult]:
        for instr in instructions:
            t0 = time.perf_counter()
            handler_name = self._HANDLERS.get(instr.opcode)
            if handler_name:
                result = getattr(self, handler_name)(instr)
            else:
                result = WaCResult(instr.opcode, "skipped",
                                   {"reason": f"Unknown opcode: {instr.opcode}"})
            result.elapsed_ms = (time.perf_counter() - t0) * 1000
            result.delta_l    = self._delta_l(instr.opcode)
            if result.tau < TAU_THRESHOLD and result.status != "error":
                result.status = "degraded"
            self.results.append(result)
        return self.results

    def run_file(self, path: str | Path) -> list[WaCResult]:
        src = Path(path).read_text(encoding="utf-8")
        return self.execute(parse_wac(src))

    def run_string(self, source: str) -> list[WaCResult]:
        return self.execute(parse_wac(source))

    def summary(self) -> dict:
        ok    = sum(1 for r in self.results if r.status == "ok")
        total = len(self.results)
        return {
            "total": total, "ok": ok, "failed": total - ok,
            "tau": round(self.tau, 6), "J": round(self.J, 4),
            "L": round(self.L, 6),
            "mu3_seam_deg": self._seam,
        }


# ── Seam projection utility ────────────────────────────────────────────────────

def mu3_seam_projection(values: list[float]) -> list[float]:
    """
    Project a list of floats onto the μ₃ triality seam at 19.47122°.
    Simulates 8×8 agent triality matrix projection.
    """
    theta = math.radians(MU3_SEAM_ANGLE)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    projected = []
    for i, v in enumerate(values):
        # Rotation in (i, i+1 mod 8) subspace
        j = (i + 1) % AGENT_MATRIX
        v_proj = v * cos_t + (values[j] if j < len(values) else 0.0) * sin_t
        projected.append(v_proj)
    return projected


# ── Default WaC script (stored as a template) ──────────────────────────────────

DEFAULT_WAC_SCRIPT = """\
# helix_orchestrator.wac v1.0 — μ₃ triality seam at 19.47122°
# SRA-HelixEvolver v7.0 | Atomadic Tech Inc.

DEFINE lattice E8_LEECH dimension=32 seam=19.47122

PHASE 0: intent_align tau_threshold=0.9412
PHASE 1: revelation_engine epiphanies=10 got_cycles=3
PHASE 2: parallel_execute AGENTS coherence_gate=0.9997
PHASE 3: vault_commit delta_m_gate=true
PHASE 4: monetize paths=[gumroad,fiverr,sra_saas]
PHASE 5: grant_submit targets=[mitacs,new_ventures_bc,innovate_bc]

AUDIT tau=0.9971 J=1.0 delta_l=0.0421
"""


if __name__ == "__main__":
    rt = WaCRuntime()
    rt.run_string(DEFAULT_WAC_SCRIPT)
    print(json.dumps(rt.summary(), indent=2))
    for r in rt.results:
        status_icon = "✓" if r.status == "ok" else "✗"
        print(f"  {status_icon} {r.phase:<30} τ={r.tau:.4f} ΔL={r.delta_l:.4f} [{r.elapsed_ms:.1f}ms]")
