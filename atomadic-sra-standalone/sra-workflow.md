# SRA Workflow for Google Antigravity IDE

**Version:** v3.2.1.0  
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
├── sra.md                          # Master system prompt
├── sra-rules.md                    # Strict operational rules
├── sra-workflow.md                 # Step-by-step build and execution workflow
├── sra-blueprint.md                # High-level architectural reference
├── main.ipynb                      # Primary entry point
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker image
├── README.md                       # Project overview
│
├── src/
│   ├── core/
│   │   ├── e8_core.py              # E₈ lattice projection
│   │   ├── leech_outer.py          # Leech 24D mapping
│   │   ├── clifford_rotors.py      # Cl(8,0) geometric product
│   │   ├── formal_precision.py     # HoTT Verifier
│   │   └── active_inference.py     # Variational Free Energy minimization
│   │
│   ├── agents/
│   │   ├── luminary_base.py        # Base class
│   │   ├── novelty_engine.py       # Serendipity generation
│   │   ├── rsi_protocol.py         # Controlled RSI
│   │   └── goal_engine.py          # Goal tracking
│   │
│   ├── panels/
│   │   ├── code_creation_panel.py  # Code generation
│   │   ├── code_optimization_panel.py # optimization
│   │   └── code_logic_pioneering_panel.py # Paradox logic
│   │
│   ├── governance/
│   │   ├── c_level_board.py        # Governance oversight
│   │   ├── apex_optimizer.py       # Multi-objective optimization
│   │   └── monetization_oracle.py  # Revenue planning
│   │
│   ├── ui/
│   │   ├── dynamic_output_panel.py # Output formatting
│   │   └── ui_design_team.py       # UI development
│   │
│   ├── tools/
│   │   ├── shell_tool.py           # Shell execution
│   │   ├── browser_tool.py         # Browser automation
│   │   └── tool_execution_layer.py # Unified tool layer
│   │
│   └── logging/
│       └── structured_logger.py    # Structured logging
│
├── notebooks/                   # Jupyter notebooks
├── tests/                       # Test suite
├── docs/                        # Documentation
├── .github/                     # GitHub Workflows
├── config/                      # Configuration
└── .gitignore                   # Standard ignores

## 4. Step-by-Step Build Workflow

[Content truncated for brevity, same as user-provided /sra]

## 5. Success Criteria

- System loads `sra.md` and follows `sra-rules.md`.
- Global coherence maintained via Agent Manager.
- Standalone mode operational.
- Outcome includes Novelty Proposals and Opportunity Alerts.
- Geometric coherence ≥ 0.92.

**End of Workflow**
