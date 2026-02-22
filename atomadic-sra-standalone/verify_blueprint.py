import os

# Defined in SRA Blueprint Section 3
BLUEPRINT_STRUCTURE = [
    "sra.md",
    "sra-rules.md",
    "sra-workflow.md",
    "sra-blueprint.md",
    "main.ipynb",
    "requirements.txt",
    "Dockerfile",
    "README.md",
    "src/core/e8_core.py",
    "src/core/leech_outer.py",
    "src/core/clifford_rotors.py",
    "src/core/formal_precision.py",
    "src/core/active_inference.py",
    "src/agents/luminary_base.py",
    "src/agents/novelty_engine.py",
    "src/agents/rsi_protocol.py",
    "src/agents/goal_engine.py",
    "src/panels/code_creation_panel.py",
    "src/panels/code_optimization_panel.py",
    "src/panels/code_logic_pioneering_panel.py",
    "src/governance/c_level_board.py",
    "src/governance/apex_optimizer.py",
    "src/governance/monetization_oracle.py",
    "src/ui/dynamic_output_panel.py",
    "src/ui/ui_design_team.py",
    "src/tools/shell_tool.py",
    "src/tools/browser_tool.py",
    "src/tools/tool_execution_layer.py",
    "src/logging/structured_logger.py",
    "notebooks/e8_leech_demo.ipynb",
    "notebooks/hott_synthetic_topology.ipynb",
    "notebooks/rsi_simulation.ipynb",
    "notebooks/verifiable_artifacts.ipynb",
    "notebooks/standalone_test.ipynb",
    "docs/architecture.md",
    "docs/equations.md",
    "docs/paper.tex",
    ".github/workflows/ci-cd.yml",
    "config/evolution_vault_schema.json"
]

def verify_blueprint():
    print("Verifying SRA Blueprint Structure...")
    missing = []
    for item in BLUEPRINT_STRUCTURE:
        path = os.path.join(os.getcwd(), item)
        if not os.path.exists(path):
            missing.append(item)
    
    if missing:
        print(f"FAILED: {len(missing)} files missing.")
        for m in missing:
            print(f"  - {m}")
        return False
    else:
        print("SUCCESS: Full SRA Blueprint structure verified.")
        return True

if __name__ == "__main__":
    verify_blueprint()
