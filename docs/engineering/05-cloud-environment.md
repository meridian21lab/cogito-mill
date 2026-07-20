# Cloud development environment

How Cursor Cloud Agents boot and verify this repo.

## Files

| File | Role |
|------|------|
| `.cursor/Dockerfile` | Base VM image: curl/git/build tools + **uv** + Python 3.12 |
| `.cursor/environment.json` | Points at the Dockerfile; `install` runs `scripts/cloud-install.sh` |
| `scripts/cloud-install.sh` | Idempotent `uv sync --frozen --all-groups` + import smoke check |

Resolution order (Cursor): repo `.cursor/environment.json` → personal env → team env.

## First-time dashboard setup

1. Connect the GitHub repo to Cursor (account admin).
2. Open [Cloud Agents](https://cursor.com/dashboard/cloud-agents) → Environments for this repo.
3. Confirm the environment picks up `.cursor/environment.json` from the branch you launch from.
4. Add **Secrets** (same names as `.env.example`):

   - `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT`
   - `GLM_API_KEY`, `GLM_BASE_URL`, `GLM_MODEL`
   - `HF_TOKEN`, `HF_DATASET_NAMESPACE` (default `ksopyla`)

5. Optional: after a successful boot, save a **snapshot** in the dashboard so later agents start warmer.

## Launching an agent

- Desktop: agent input → **Cloud**, select this repo/branch
- Web: [cursor.com/agents](https://cursor.com/agents)
- Always launch from a branch that contains the latest `.cursor/environment.json` (cloud uses the commit it starts from)

## Smoke checks the agent should run

```bash
uv --version
uv run pytest tests/unit -q
uv run ruff check src tests
```

Provider/integration tests need the secrets above; skip them until secrets are set.

## Updating the environment

1. Edit Dockerfile / `scripts/cloud-install.sh` / `environment.json` on a branch.
2. Commit + push.
3. Start a new cloud agent **from that branch** to validate.
4. Merge when boot + `uv run pytest tests/unit` succeed.
