<div align="center">

# ⚙️ Cogito Mill

### Generating long-form reasoning data that tests understanding—not recall

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/package_manager-uv-DE5FE9)](https://docs.astral.sh/uv/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-1C3C3C)](https://www.langchain.com/langgraph)
[![Status](https://img.shields.io/badge/status-MVP_in_development-orange)](docs/engineering/02-agent-flow.md)

**Cogito Mill is an agentic pipeline for constructing, proving, writing, and validating
synthetic narrative deduction datasets.**

[Vision](docs/vision.md) ·
[Architecture](docs/engineering/01-architecture.md) ·
[Agent flow](docs/engineering/02-agent-flow.md) ·
[Hugging Face](https://huggingface.co/ksopyla/datasets)

</div>

---

## 🧩 The problem

Language models can produce answers that sound carefully reasoned while relying on a familiar
surface pattern. A famous riddle, common benchmark template, suggestive occupation, or expected
story ending may trigger a memorized answer before the model has reconstructed what the prompt
actually says.

This creates an **illusion of understanding**:

- the final answer looks plausible;
- the explanation is polished;
- the cited facts sound relevant;
- but a reordered clue or one changed premise breaks the result.

Final-answer accuracy alone cannot tell us whether the model followed the evidence, used a
shortcut, guessed correctly, or wrote a post-hoc rationale. Long contexts make this worse:
important facts are dispersed among events, aliases, time constraints, causal mechanisms, and
plausible red herrings.

Cogito Mill is being built to generate data where the intended answer is not merely plausible.
It is **provably entailed by the disclosed evidence**.

## 📖 Long Story Short

The first dataset produced by the mill is **Long Story Short**: fully synthetic narrative
mysteries and riddles designed for approximately **4K–32K+ token contexts**, with the eventual
distribution weighted toward longer stories.

Each problem can combine:

- 🔗 **Relational reasoning** — identity, aliases, roles, cardinality, and constraints;
- 🕰️ **Temporal reasoning** — order, duration, overlap, and relative time;
- ⚙️ **Causal reasoning** — preconditions, effects, inhibitors, and interventions;
- 🔄 **Counterfactual reasoning** — what changes when an event does not occur;
- ❌ **Falsification** — the smallest evidence set that rules out a hypothesis;
- 🧭 **Evidence grounding** — which exact sentences support every deduction.

Stories may use detective, domestic, workplace, expedition, historical, or explicitly defined
speculative settings. They remain self-contained: deduction-critical facts cannot depend on
unstated trivia or cultural assumptions.

## 💡 What makes the data different?

| Principle | Why it matters |
|-----------|----------------|
| **Formal world first** | Every story starts as a typed world model, not unconstrained prose. |
| **Visible-theory uniqueness** | The answer must be unique from what the reader can see—not merely unique in hidden generator state. |
| **Deterministic verification** | Z3 and causal simulation decide consistency, entailment, and interventions; an LLM does not certify its own work. |
| **Structured successful trace** | Gold steps identify evidence, prior steps, inference type, and canonical conclusion. |
| **Minimal falsifier** | A model must show exactly what defeats a supplied hypothesis. |
| **Blind criticism** | Separate critic roles inspect the rendered story without relying on the writer's private rationale. |
| **Full provenance** | Prompts, model roles, repairs, validation reports, seeds, and rejected attempts remain inspectable. |

The later benchmark will add matched variants:

1. **same logic, different surface** — the answer should remain stable;
2. **similar surface, changed logic** — the answer should change.

Together, these tests are intended to separate robust evidence tracking from template matching.

## 🏗️ How the mill works

```mermaid
flowchart LR
    Recipe[GenerationRecipe] --> Planner[ConceptPlanner]
    Planner --> Critic[ConceptCritic]
    Critic -->|"repair, max 2"| Planner
    Critic --> Formalizer[WorldFormalizer]
    Formalizer --> Solver[Z3AndCausalSolver]
    Solver --> Evidence[EvidencePlanner]
    Evidence --> Writer[OutlineAndSceneWriter]
    Writer --> StoryCritic[BlindStoryCritic]
    StoryCritic --> Questions[QuestionBundle]
    Questions --> Validator[FinalValidator]
    Validator --> Artifact[VersionedArtifact]
```

The pipeline uses an explicit
[LangGraph `StateGraph`](docs/engineering/01-architecture.md). Agent nodes create or render
typed artifacts; deterministic nodes enforce the hard gates. A failed stage receives bounded,
structured repair feedback and is then rejected or quarantined rather than silently accepted.

Each run chooses one provider family:

- **Azure OpenAI** writer and judge deployments; or
- **GLM** writer and judge models.

Provider families are compared across runs, not mixed inside one item.

## 📦 Anatomy of an accepted item

An accepted item contains:

```text
sentence-addressable story
├── canonical final answer
├── supported intermediate conclusions
├── ordered typed deduction steps
│   ├── source sentence IDs
│   ├── prior-step IDs
│   ├── inference type
│   └── canonical conclusion
├── causal counterfactual
├── minimal hypothesis falsifier
└── generation and validation provenance
```

The gold trace is extracted from solver dependencies and only then verbalized. A convincing
free-form chain of thought is not accepted as proof.

## 🚧 Project status

Cogito Mill is currently an **early MVP under active development**.

- [x] Product and dataset contract
- [x] Agent architecture and implementation flow
- [x] Azure OpenAI and GLM provider factories
- [x] Local and Cursor Cloud development environment
- [x] Typed domain schemas and fixture world
- [x] Z3 relational/temporal compiler and causal simulator (pilot)
- [x] Explicit LangGraph planner/critic/formalizer/storyteller/verification flow
- [x] 150-item baseline packs plus live-agent calibration pack (`pilot_v2.jsonl`)
- [x] Narration/diversity gates and blind Luna hardness evaluation
- [ ] Controlled variant families
- [ ] Hugging Face public/gated release (blocked on write-capable `HF_TOKEN`)
- [ ] Full LLM-authored worlds at novel length

### Pilot CLI

Canonical launchers (mandatory protocol:
`.agents/skills/dataset-quality/ASSESSMENT-PROTOCOL.md`):

```bash
scripts/generate-dataset.sh \
  --n 12 --config <new-candidate> --agent-mode live --output-root <clean-root>
scripts/evaluate-dataset.sh \
  --local-dir <clean-root>/packed/<new-candidate>.jsonl \
  --config <new-candidate> --label <experiment-id>
```

Equivalent direct CLI:

```bash
uv run cogito-mill generate-batch \
  --n 12 --difficulty very_hard --agent-mode live
uv run cogito-mill publish --dry-run --input data/processed --config pilot_v2
uv run cogito-mill assess --local-dir data/packed/pilot_v2.jsonl
uv run cogito-mill evaluate \
  --local-dir data/packed/pilot_v2.jsonl --solver-provider azure --main-only
```

Thin Hub schema columns include `id`, `story`, `question`, `gold_answer`,
`questions`, `n_hops`, `setting_family`, `difficulty_bucket`, and `template_id`
(`schemas/reasoning-item.schema.json` — freeze during routine quality iterations).

The immediate milestone remains inspectable verification; the pilot slice adds batch
generation plus a Luna hardness gate (target ≤30% exact-answer accuracy).

## 🚀 Quick start

### Local development

Requirements:

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- provider credentials only for live generation

```bash
git clone https://github.com/meridian21lab/cogito-mill.git
cd cogito-mill

uv sync
cp .env.example .env  # add only the providers you intend to call

uv run pytest tests/unit -q
uv run ruff check src tests
uv run cogito-mill
```

Use `uv` for every dependency and Python command. Do not create a separate virtual environment
with `python -m venv`.

### ☁️ Cursor Cloud

The repository contains a reproducible cloud environment:

```text
.cursor/Dockerfile
    ↓
.cursor/environment.json
    ↓
scripts/cloud-install.sh
    ↓
uv sync --frozen --all-groups
```

Add required `AZURE_OPENAI_*`, `GLM_*`, and later `HF_TOKEN` values through **Cursor Cloud
Secrets**—never commit them. Launch the cloud agent from a branch containing the latest
environment configuration.

After boot:

```bash
uv run pytest tests/unit -q
uv run ruff check src tests
```

See [`AGENTS.md`](AGENTS.md) for operational instructions.

## 🗂️ Repository map

| Path | Purpose |
|------|---------|
| [`src/cogito_mill/`](src/cogito_mill/) | Application, providers, agents, solver, pipelines |
| [`tests/`](tests/) | Unit, integration, and end-to-end test pyramid |
| [`schemas/`](schemas/) | Dataset interchange schemas |
| [`docs/vision.md`](docs/vision.md) | Product thesis and settled data contract |
| [`docs/engineering/`](docs/engineering/) | Architecture and executable agent flow |
| [`docs/literature/`](docs/literature/) | Citable research notes selected for retention |
| [`.agents/skills/`](.agents/skills/) | Project engineering and framework skills |
| [`.cursor/`](.cursor/) | Cloud environment, agent definitions, plans, and rules |
| [`data/`](data/) | Git-ignored raw, interim, and processed run artifacts |

## 🧪 Development checks

```bash
# Fast deterministic tests
uv run pytest tests/unit -q

# Graph/provider integration tests
uv run pytest tests/integration -q

# Full local quality gate
uv run pytest tests/unit tests/integration tests/e2e
uv run ruff check src tests
uv run mypy
```

Live provider tests are opt-in and require secrets. Default tests must remain offline and
deterministic.

## 🔬 Research foundations

The design draws on work in synthetic multi-step reasoning, detective QA, shortcut learning,
counterfactual reasoning, and process supervision, including
[MuSR](https://arxiv.org/abs/2310.16049),
[DetectiveQA](https://arxiv.org/abs/2409.02465),
[BRAINTEASER](https://aclanthology.org/2023.emnlp-main.885/),
[Shortcut Suite](https://aclanthology.org/2024.emnlp-main.679/), and
[PRM800K](https://arxiv.org/abs/2305.20050).

These projects inform the methodology; their stories are not copied into the dataset.

## 🤝 Development workflow

- `main` — stable and release-ready;
- `dev` — shared integration branch;
- feature branches — branch from `dev` and open pull requests back into `dev`.

Before proposing a change, read [`AGENTS.md`](AGENTS.md), the
[architecture](docs/engineering/01-architecture.md), and the
[agent flow](docs/engineering/02-agent-flow.md).

---

<div align="center">

Built by [Meridian21Lab](https://github.com/meridian21lab) ·
Datasets planned under [Hugging Face `@ksopyla`](https://huggingface.co/ksopyla/datasets)

</div>
