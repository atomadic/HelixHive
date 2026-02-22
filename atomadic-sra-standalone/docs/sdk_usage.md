# White-Label SDK Usage Guide (v3.8.0.0)

The SRA Revelation Engine can be integrated into external agentic swarms using the SRA White-Label SDK.

## Manifestation

The SDK requires a URI to a live SRA server and a valid `X-API-KEY`.

```python
from src.sdk.sra_client import SRAClient

# Initialize Client
client = SRAClient(
    base_url="http://localhost:8000",
    api_key="SRA_SOVEREIGN_2026"
)

# Trigger Revelation Cycle
query = "Latest trends in Vancouver AI hardware 2026"
result = client.research(query)

# Parse Helical Output
tau = result['coherence']
print(f"Resonance achieved: {tau}")

for epiphany in result['epiphanies']:
    print(f"EPIPHANY: {epiphany['id']}")
    for rev in epiphany['revelations']:
        print(f" - [{rev['emotionalTag']}] {rev['content']}")
```

## Production Security

For production deployments, set the `SRA_API_KEY` environment variable on the server and use the same key in the `SRAClient` constructor.

## revelation-engine Summary

- **Endpoint**: `/api/research`
- **Auth**: `X-API-KEY` header
- **Schema**: RevelationOutput (JSON)
