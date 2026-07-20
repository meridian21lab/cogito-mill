# Cogito Mill engineering specifications

The Long Story Short MVP design was accepted after evidence gathering and a design grill.
These documents are the implementation source of truth.

| Doc | Status | Purpose |
|-----|--------|---------|
| [../vision.md](../vision.md) | accepted | Product thesis, data contract, MVP boundary |
| [01-architecture.md](01-architecture.md) | accepted | Domain modules, solver, agents, graph, artifacts |
| [02-agent-flow.md](02-agent-flow.md) | accepted | Agent stages, implementation phases, gates, and deferred roadmap |

Implement in the sequence defined by `02-agent-flow.md`. Provider policy and settled
architectural decisions live in `01-architecture.md`; changes to its invariants require an ADR
under `docs/domain/`.

Cloud setup is operational guidance rather than architecture. It lives in `AGENTS.md`,
`.cursor/rules/project.mdc`, `.cursor/environment.json`, `.cursor/Dockerfile`, and
`scripts/cloud-install.sh`.

External literature keepers from `/research-scout` land under [`docs/literature/`](../literature/).
