# LLM providers (draft)

## Azure OpenAI (custom deployments)

Use deployment **names**, not raw model IDs:

| Env | Meaning |
|-----|---------|
| `AZURE_OPENAI_API_KEY` | Key |
| `AZURE_OPENAI_ENDPOINT` | Resource endpoint |
| `AZURE_OPENAI_API_VERSION` | API version |
| `AZURE_OPENAI_DEPLOYMENT` | Chat / reasoning deployment |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Optional embeddings |

Factory: `cogito_mill.llm.build_azure_chat()`.

## GLM

Treat GLM as OpenAI-compatible HTTP:

| Env | Meaning |
|-----|---------|
| `GLM_API_KEY` | Key |
| `GLM_BASE_URL` | Provider base URL |
| `GLM_MODEL` | Model id (e.g. `glm-4.5`) |

Factory: `cogito_mill.llm.build_glm_chat()`.

## Cloud Secrets

Cursor Cloud agents should receive the same variables via the Cloud Agents Secrets UI — never commit real values.

## Open decisions

- Which roles use Azure vs GLM (cost / quality / latency split)
- Temperature and max-token budgets per stage
- Whether embeddings are required for verification
