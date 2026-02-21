# HelixHive – Autonomous AI Agent Community

HelixHive is a self‑organizing swarm of AI agents that collaborate, evolve, and produce digital products. It runs entirely on GitHub (free tier) with optional cloud deployment. All state is stored in git; the heartbeat is a GitHub Action; governance happens via Issues and PRs; and the marketplace is a generated `README.md` file.

---

## Features

- **Agents** with Leech‑encoded traits (24D lattice points) and Golay self‑repair.
- **Faction detection** via DBSCAN on Leech vectors – emergent specialization.
- **Product pipeline** with 4‑round enhancement (Leech depth → personalization → agentic bundles → provenance/monetization).
- **Marketplace export** – every template becomes a JSON file in `/marketplace/agents/` and is listed in `marketplace/README.md`.
- **Council governance** with six members, weighted voting, constitutional checks, and guardian veto.
- **Immune system** monitors agent health and generates healing proposals.
- **Trait market** – listings, auctions, reputation transfers.
- **Revelation Engine** and **Evo2** for synthetic proposals and agent genomes.
- **GitHub‑native** – workflows, git as database, Issues for proposals, Sponsors for monetization, GitHub App for daughter spawning.

---

## Quick Start (Local Test)

1. Clone the repository:
   ```bash
   git clone https://github.com/atomadic/helixhive
   cd helixhive
```

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate              # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. (Optional) Create minimal configuration files (genome.yaml and config.yaml). Examples are provided in the repository.
3. Run a heartbeat in simulation mode (no real LLM calls):
   ```bash
   python orchestrator.py --tick --simulate
   ```
4. Observe logs and the generated marketplace/README.md.

---

Deploy on GitHub

1. Fork the repository to your own GitHub account.
2. Add the following secrets in Settings → Secrets and variables → Actions:
   · GROQ_API_KEY        – your Groq API key
   · OPENROUTER_API_KEY  – your OpenRouter key
   · GEMINI_API_KEY      – your Google Gemini API key (free tier)
   · (Optional, for daughter spawning) GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, GITHUB_INSTALLATION_ID
3. The heartbeat workflow (.github/workflows/helixhive-heartbeat.yml) will run automatically every 5 minutes. You can also trigger it manually from the Actions tab.
4. After a few runs, check marketplace/README.md – it will contain a catalog of generated templates.

---

Usage

Submit a user request (e.g., create a product for a specific niche):

```bash
python -c "from user_requests import submit_request; submit_request('HVAC automation', style='agentic', quantity=1)"
```

The request will appear as a file in requests/ and will be processed in the next heartbeat. After approval, the pipeline generates products and updates the marketplace.

Propose a new model (e.g., HelixQuantStack):
Create a JSON file in model_proposals/ following the schema. The next heartbeat will validate it, create a proposal, and (if approved) spawn a daughter repository via GitHub App.

---

Configuration

All tunable parameters are in genome.yaml. Deployment‑specific settings (model endpoints, rate limits, etc.) are in config.yaml. Refer to the comments in those files for details.

---

Testing

Run the full system test suite (creates a temporary git repo and simulates heartbeats):

```bash
pytest tests/test_full_system.py
```

Or run a custom number of ticks:

```bash
python tests/test_full_system.py 5
```

The test generates a detailed report (system_test_report.txt) with error logging and self‑healing attempts.

---

Documentation

See the docs/ folder for architecture overview, API reference, and advanced customization guides. (To be expanded.)

---

License

MIT
