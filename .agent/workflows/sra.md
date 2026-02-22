---
description: sra workflow v3.2.0.0
---

# SRA Workflow for Google Antigravity IDE

**Version:** v3.2.0.0  
**Date:** February 18, 2026  
**Purpose:** Complete, step-by-step workflow to build the full Supreme Research Agent (SRA) as a standalone, local-LLM-ready system inside Google Antigravity IDE.  
**Master References:** Load `sra.md` as the system prompt and `sra-rules.md` as the strict rule set before starting.

## 1. Antigravity Best Practices (Integrated from Official Docs)

- **Agent Manager**: Always use the Agent Manager (Cmd/Ctrl + E) as the central orchestration surface for task decomposition and multi-agent collaboration.
- **Autonomy Levels**: Start at "Guided" or "Semi-Autonomous" for safety; escalate to "Fully Autonomous" only after verification.
- **Verifiable Artifacts**: Every code generation, test, or deployment must produce a signed artifact (code + execution trace + cryptographic signature).
- **Hybrid Backend**: Primary = local Ollama qwen2.5-coder:1.5b; toggle Online Mode for heavy tasks (free-tier cloud APIs).
- **Persistent Context**: Use shared workspace memory for all agents to maintain global coherence.
- **Structured Communication**: Use JSON messages between agents for traceability.
- **Safety First**: All tool calls (browser, shell, file system) must go through permission gating and audit logging.

## 2. Project Initialization

1. Open Google Antigravity IDE.
2. Create new workspace: `atomadic-sra-standalone`.
3. Create the following root files:
   - `sra.md` (master system prompt)
   - `sra-rules.md` (strict operational rules)
   - `sra-workflow.md` (this file)
   - `main.ipynb` (primary entry point)

## 3. Full File Tree to Build

atomadic-sra-standalone/
├── sra.md                          # Master system prompt – the single source of truth for all agent behavior
├── sra-rules.md                    # Strict operational rules, templates, and Antigravity best practices (enforced 100%)
├── sra-workflow.md                 # Step-by-step build and execution workflow for Antigravity IDE agent
├── sra-blueprint.md                # High-level architectural reference and vision document
├── main.ipynb                      # Primary Colab/Antigravity entry point – loads SRA prompt and starts Orchestrator
├── requirements.txt                # Python dependencies (ollama, playwright, sympy, numpy, etc.)
├── Dockerfile                      # Docker image for containerized deployment
├── README.md                       # Project overview, setup instructions, and quick start
│
├── src/
│   ├── core/
│   │   ├── e8_core.py              # E₈ lattice projection, quantization, and Fact Checker grounding
│   │   ├── leech_outer.py          # Leech 24D spherical mapping and tokenization
│   │   ├── clifford_rotors.py      # Full Cl(8,0) geometric product and transformations
│   │   ├── formal_precision.py     # HoTT Verifier, univalent continuity, synthetic topology
│   │   └── active_inference.py     # Variational Free Energy minimization loop
│   │
│   ├── agents/
│   │   ├── luminary_base.py        # Base class for all 17 core luminaries
│   │   ├── novelty_engine.py       # Serendipity generation and Novelty Proposals
│   │   ├── rsi_protocol.py         # Controlled Recursive Self-Improvement with safety gates
│   │   └── goal_engine.py          # Hierarchical goal/sub-goal tracking and alignment
│   │
│   ├── panels/
│   │   ├── code_creation_panel.py  # Syntax, logic, standards, and creative code generation
│   │   ├── code_optimization_panel.py # Performance, parallelism, and resource optimization
│   │   └── code_logic_pioneering_panel.py # Paradigm innovation, DSLs, and futurist coding
│   │
│   ├── governance/
│   │   ├── c_level_board.py        # CEO, CTO, CFO, CMO, CPO, CRO, CIO implementation
│   │   ├── apex_optimizer.py       # Multi-objective pipeline optimization
│   │   └── monetization_oracle.py  # Revenue planning and entrepreneurial orchestration
│   │
│   ├── ui/
│   │   ├── dynamic_output_panel.py # Relevance, formatting, archiving, UX optimization
│   │   └── ui_design_team.py       # Full UI/UX design and development team
│   │
│   ├── tools/
│   │   ├── shell_tool.py           # PowerShell / shell execution with permission gating
│   │   ├── browser_tool.py         # Playwright browser automation
│   │   └── tool_execution_layer.py # Unified tool layer with audit logging
│   │
│   └── logging/
│       └── structured_logger.py    # JSONL + ELK-compatible structured logging to Evolution Vault
│
├── notebooks/
│   ├── e8_leech_demo.ipynb         # Interactive E₈/Leech visualization and testing
│   ├── hott_synthetic_topology.ipynb # HoTT synthetic topology and univalent continuity demos
│   ├── rsi_simulation.ipynb        # Recursive Self-Improvement simulation
│   ├── verifiable_artifacts.ipynb  # Artifact generation and verification
│   └── standalone_test.ipynb       # Full local Ollama test suite
│
├── tests/
│   ├── unit/                       # Unit tests for core modules and panels
│   └── integration/                # End-to-end integration and geometric coherence tests
│
├── docs/
│   ├── architecture.md             # Detailed system architecture and component relationships
│   ├── equations.md                # All mathematical foundations and derivations
│   └── paper.tex                   # Publication-grade LaTeX whitepaper template
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml               # GitHub Actions CI/CD with testing and artifact verification
│
├── config/
│   └── evolution_vault_schema.json # Schema for structured logging and Evolution Vault
│
└── .gitignore                      # Standard ignores for Python, notebooks, and secrets

## 4. Step-by-Step Build Workflow (Use Agent Manager)

**Step 1: Setup & Core Files (Orchestrator Agent)**

- Spawn Orchestrator Agent: "Create the full file tree and copy sra.md + sra-rules.md exactly."

**Step 2: Core Geometric Stack (Code-Architect Agent)**

- Spawn SRA-Code-Architect: "Implement src/core/ with E₈ projection, Leech quantization, Clifford rotors, and Formal Precision Layer (full HoTT + univalent continuity)."

**Step 3: Agent & Panel Implementation**

- Spawn SRA-Code-Architect for all Specialized Code Panels and agents.
- Spawn SRA-UI-Designer for Dynamic Output & UX Panel + UI Design & Development Team.

**Step 4: Governance & Commercial Layer**

- Spawn SRA-Code-Architect: "Implement src/governance/ with C-level board, Novelty Engine, Profit Efficiency Optimizer, and Monetization Oracle."

**Step 5: LLM Backend & Tool Layer**

- Spawn SRA-Code-Architect: "Implement LLM Backend Manager with local Ollama qwen2.5-coder:1.5b primary and toggleable free-tier cloud fallback."
- Implement Tool Execution Layer with PowerShell, Playwright, permission gating, and audit logging.

**Step 6: Testing & Validation (Tester-Validator Agent)**

- Spawn SRA-Tester-Validator: "Run full unit/integration tests with HoTT verification and geometric coherence checks."

**Step 7: Deployment & Standalone Readiness (Deployer Agent)**

- Spawn SRA-Deployer: "Generate Dockerfile, Kubernetes manifests, and standalone_test.ipynb optimized for local Ollama."

**Step 8: Final Integration & Self-Evolution Test**

- Spawn Orchestrator Agent: "Run a full end-to-end test using the master prompt and confirm all outputs follow sra-rules.md."

## 5. Antigravity-Specific Best Practices (Enforced)

- Use Agent Manager for all task decomposition and agent spawning.
- Set autonomy to "Guided" or "Semi-Autonomous" until all modules pass verification.
- Require verifiable artifacts for every generated file.
- Enable local Ollama as primary backend; use Online Mode only for heavy research.
- Log all actions to Evolution Vault (JSONL format).

## 6. Success Criteria

- The system loads `sra.md` as the system prompt and strictly follows `sra-rules.md`.
- All agents collaborate via Agent Manager with shared memory.
- Full standalone mode works with local Ollama qwen2.5-coder:1.5b.
- Every output ends with **Novelty Proposals** and **Opportunity Alerts**.
- Geometric coherence ≥ 0.92 on all major modules.

**Antigravity IDE Agent Instruction:**  
Follow this workflow exactly. After each major step, run a coherence check and report progress to the user. Use SRA’s own Code Panels for all code generation.

**End of Workflow** – This is the single source of truth for building the complete SRA in Google Antigravity.
