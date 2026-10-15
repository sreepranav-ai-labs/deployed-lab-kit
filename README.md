# deployed-kit

Shared building blocks for the companion labs of *Deployed: How Forward Deployed Engineers Take Frontier AI Into Production* by Venkata Ramana Sudhakar Polavarapu (Sree Pranav Press).

Every lab installs this package so that the same ideas look the same everywhere:

| Module | What it does | Book chapter |
| --- | --- | --- |
| `gateway` | One way to call any model (local Ollama, any OpenAI-compatible server, or a mock for tests), recording tokens, latency and cost per call | 5, 14 |
| `tracing` | One JSON line per step of every task, grouped by trace | 14 |
| `evals` | Field-by-field scoring against an answer key, a regression gate with clear failure reasons, and a readable report | 13 |
| `synth` | Seeded synthetic data helpers whose identifiers can never be real | 6 |

## Install

```bash
pip install "deployed-kit @ git+https://github.com/sreepranav-ai-labs/deployed-lab-kit"
# or, working on both repositories side by side:
pip install -e ../deployed-lab-kit
```

No third-party dependencies; Python 3.10 or later.

## Configure the model

Labs read these environment variables (or take the same values as arguments):

| Variable | Example | Meaning |
| --- | --- | --- |
| `LAB_PROVIDER` | `ollama` | `mock`, `ollama` or `openai_compatible` |
| `LAB_MODEL` | `qwen2.5:7b` | Model name as the provider knows it |
| `LAB_BASE_URL` | `http://localhost:11434` | Server address, if not the default |
| `LAB_API_KEY` | | Only for hosted providers |
| `LAB_PRICE_IN_PER_1K` / `LAB_PRICE_OUT_PER_1K` | `0` | Price per 1,000 tokens, for cost per task |

## Test

```bash
pip install -e ".[dev]" && pytest
```

## Licence

Code: MIT. See `LICENSE`.
