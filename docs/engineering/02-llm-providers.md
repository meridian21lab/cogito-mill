# LLM providers (draft)

## Azure OpenAI (role-specific deployments)

One Azure OpenAI **resource**, multiple **deployments** mapped to mill roles.
Use deployment **names**, not raw model IDs.

| Env | Meaning |
|-----|---------|
| `AZURE_OPENAI_API_KEY` | Key |
| `AZURE_OPENAI_ENDPOINT` | Resource root only, e.g. `https://<resource>.openai.azure.com/` (no `/openai/...` path or query) |
| `AZURE_OPENAI_API_VERSION` | API version |
| `AZURE_OPENAI_WRITER_DEPLOYMENT` | Cheaper / less capable — story generation |
| `AZURE_OPENAI_JUDGE_DEPLOYMENT` | Stronger — verification / critique |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Optional embeddings |

Example mapping (Sweden Central lab resource):

| Role | Deployment | Model |
|------|------------|-------|
| writer | `gpt-5.6-luna-stories` | gpt-5.6-luna |
| judge | `gpt-5.6-terra-stories` | gpt-5.6-terra |

Factories:

```python
from cogito_mill.llm import build_azure_chat

writer = build_azure_chat(role="writer")
judge = build_azure_chat(role="judge")
```

## GLM

Treat GLM as OpenAI-compatible HTTP, with the same writer/judge split:

| Env | Meaning |
|-----|---------|
| `GLM_API_KEY` | Z.AI API key |
| `GLM_BASE_URL` | Coding Plan: `https://api.z.ai/api/coding/paas/v4/` (general `/paas/v4/` is separate prepaid balance) |
| `GLM_WRITER_DEPLOYMENT` | Model id for story generation (e.g. `glm-5.1`) |
| `GLM_JUDGE_DEPLOYMENT` | Model id for critique (e.g. `glm-5.2`) |

```python
from cogito_mill.llm import build_glm_chat

writer = build_glm_chat(role="writer")
judge = build_glm_chat(role="judge")
```

Factory: `cogito_mill.llm.build_glm_chat()`.

## Cloud Secrets

Cursor Cloud agents should receive the same variables via the Cloud Agents Secrets UI — never commit real values.

## Open decisions

- Whether any stages still use GLM vs Azure (cost / quality / latency)
- Temperature and max-token budgets per role
- Whether embeddings are required for verification
