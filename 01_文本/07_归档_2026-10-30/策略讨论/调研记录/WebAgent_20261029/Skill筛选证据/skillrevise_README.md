# SkillRevise

[![arXiv](https://img.shields.io/badge/arXiv-2606.01139-b31b1b.svg)](https://arxiv.org/abs/2606.01139)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Official release for **SkillRevise: Improving LLM-Authored Agent Skills via Trace-Conditioned Skill Revision**.
Accepted to the Findings of EMNLP 2026.

SkillRevise improves cold-start agent skills by treating a skill as an execution-grounded artifact. Starting from an initial LLM-authored skill, it executes the task, diagnoses verifier-facing failures, retrieves reusable repair principles, revises the skill with execution anchors, re-executes the candidate, and returns the best observed skill under a utility gate.

![SkillRevise pipeline](docs/assets/skillrevise_pipeline.png)

## Highlights

- **Trace-conditioned skill revision.** SkillRevise revises imperfect skills from execution traces and verifier feedback instead of relying only on expert authoring, retrieval, or one-shot skill generation.
- **Three-part method.** The framework combines task-specific Diagnosis, reusable Principle Memory, and an anchored Revision Operator.
- **Utility-gated selection.** Each candidate skill is re-executed. The next search round follows the latest evaluated candidate, while the returned artifact is the highest-utility version observed within the budget.
- **Unified benchmark interface.** The release includes the task bundles and loaders for SkillsBench, SkillLearnBench-Random, and SWE-Skills-Bench-Hard. Executor/provider harnesses remain external.

## Main Results

The paper evaluates SkillRevise across three verifier-driven benchmarks and five executors. The table below highlights representative settings from the main results, together with the corresponding no-skill and one-shot Skill-Creator baselines for the same executor:

| Benchmark | Executor | No skill | Skill-Creator | SkillRevise maxrev3 |
| --- | --- | ---: | ---: | ---: |
| SkillsBench | GPT-5.5 | 31/86 | 34/86 | **53/86** |
| SkillLearnBench-Random | Opus-4.7 | 7/50 | 7/50 | **25/50** |
| SWE-Skills-Bench-Hard | Qwen-3.6-Plus | 22/70 | 24/70 | **35/70** |

Here, `maxrev3` means utility-selected best-observed performance with at most three revisions, not necessarily the terminal generated version. The reported protocol stops candidate generation after the first verifier success, then selects over the evaluated history.

The revised skills also show cross-model transfer behavior: fixed GPT-5.5-produced skills improve all four target executors on the 57-task GPT-5.5 source-success subset, while executor-specific revision remains strongest in every reported case.

## Repository Contents

- `skillrevise/`: Python package and CLI.
  - `core/`: task/result models, execution loop, runners, metrics, artifacts, and reporting.
  - `method/`: skill authoring, diagnosis, revision, skill parsing, and principle memory.
  - `benchmarks/`: SkillsBench loading, SkillLearnBench and SWE-Skills-Bench conversion, ALFWorld loading, verifier helpers, and task selection.
  - `llm/`: command-based LLM client and provider wrapper used by `skillrevise-llm`.
- `data/`: SkillsBench-style task inputs and manifests used by the main experiments.
- `scripts/`: benchmark export, task selection, and skill-audit helpers.
- `docs/`: method, benchmark, and running documentation.
- `tests/`: unit tests for the public package and scripts.

The complete Git repository/source release contains the benchmark snapshots,
documentation, scripts, and tests listed above. Python wheels and source
distributions are intentionally code-oriented and do not embed the roughly
gigabyte-scale `data/` tree; use a repository checkout or tagged source archive
for the released benchmark bundles.

## Quick Start

From a complete repository checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev,benchmarks]"
pytest
```

Run a one-task synthetic smoke check:

```bash
skillrevise data/skillsbench/skillsbench_tasks.json \
  --manifest-kind skillsbench \
  --workspace-root . \
  --mock \
  --baseline-only \
  --limit 1 \
  --output runs/baseline_smoke.json
```

`--mock` is a deterministic development adapter. It does not execute the benchmark and must not be used to report paper results. The CLI never selects it implicitly: every run must specify exactly one of `--mock` or `--harness-command`.

For a real run, supply an external agent harness that executes the task and emits the documented trace contract:

```bash
skillrevise data/skillsbench/skillsbench_tasks.json \
  --manifest-kind skillsbench \
  --workspace-root . \
  --harness-command "path/to/paper-compatible-harness" \
  --executor-id "<executor-model-and-harness-version>" \
  --artifacts-root runs/artifacts \
  --limit 1 \
  --author-mode llm-principle-bank \
  --diagnosis-mode heuristic \
  --revision-mode llm-principle-bank \
  --llm-command "python -m skillrevise.llm.command" \
  --principle-retrieval hybrid-rrf \
  --principle-embedding-model "qwen/qwen3-embedding-4b" \
  --principle-embedding-url "<OpenAI-compatible embeddings endpoint>" \
  --output runs/llm_run.json \
  --summary-output runs/llm_summary.json \
  --max-revisions 3 \
  --max-heldout 0 \
  --stop-on-success \
  --continue-after-non-improving-revision \
  --strict-llm
```

This command matches the controller-call accounting reported in the camera-ready
cost analysis: Diagnosis is constructed deterministically from execution and
verifier evidence, and each generated repair uses one logical LLM revision call.
Selecting `--diagnosis-mode llm` is supported as an optional configuration, but
adds a separate logical LLM call on every diagnosed round and is not the reported
cost profile. Provider retries and dense-embedding requests are separate from
these logical controller-call counts.

The bundled `skillrevise-llm` command reads prompts from stdin and writes completions to stdout. Configure provider credentials with environment variables such as:

```bash
export SKILL_REVISE_REVISION_LLM_PROVIDER=openai
export SKILL_REVISE_REVISION_LLM_MODEL="<model-name>"
export SKILL_REVISE_REVISION_LLM_API_KEY="<api-key>"
```

Authenticated embedding endpoints use the separate
`SKILL_REVISE_PRINCIPLE_EMBEDDING_API_KEY` environment variable. Keep both
credentials in environment or local configuration rather than command-line
arguments. When using an embedding cache instead of an endpoint, the cache must
be complete and use the same embedding model that generated it.

The public package provides an external-command adapter, task materialization, verification, and artifact accounting; it does not bundle the paper's provider-specific Codex or Claude Code launchers. Reproducing that protocol therefore requires a compatible `--harness-command`. The bundled verifier entrypoints follow Harbor's reward-file contract: their process exit code is not the task verdict. A compatible harness must execute that environment and return a validated self-verification receipt, or the caller must provide an independent `--verifier-command` whose exit code is authoritative. See [docs/reproducibility.md](docs/reproducibility.md).

The paper uses a fixed Principle Memory during evaluation. Memory absorption is opt-in through `--enable-principle-absorption`, uses an LLM abstraction in the paper-aligned protocol, and should run only on a separate calibration or post-evaluation split; omit that flag during held-out evaluation. The paper's hybrid-RRF retrieval also requires a configured embedding endpoint or a complete model-matched embedding cache. For a dependency-free synthetic smoke test, use `--principle-retrieval bm25`.

To build a bank and run your own experiments, use the complete
[absorb-and-evaluate example](examples/absorb_and_evaluate/README.md). It includes
toy calibration/evaluation tasks, an empty bank, an LLM executor, an independent
checker, and commands for saving and reusing a frozen bank. Replace those inputs
with your own tasks and environment adapter. Paper-run banks, splits, and
results are not required. `skillrevise-check-split` provides an optional read-only
membership check before evaluation.

## Benchmark Bundles

All three main benchmark bundles are already materialized in a SkillsBench-style layout and can be loaded with `--manifest-kind skillsbench`:

| Bundle | Tasks | Manifest |
| --- | ---: | --- |
| `data/skillsbench/` | 86 | `data/skillsbench/skillsbench_tasks.json` |
| `data/skilllearnbench/` | 50 | `data/skilllearnbench/skillsbench_tasks.json` |
| `data/swe-skills-bench/` | 70 | `data/swe-skills-bench/skillsbench_tasks.json` |

See [docs/benchmarks.md](docs/benchmarks.md) for bundle structure and loading details.

## Documentation

- [Overview](docs/overview.md)
- [Bundled Benchmarks](docs/benchmarks.md)
- [Running SkillRevise](docs/running.md)
- [Reproducibility Contract](docs/reproducibility.md)

## Citation

If you use SkillRevise in research, please cite the paper:

```bibtex
@inproceedings{liu2026skillrevise,
  title = {SkillRevise: Improving LLM-Authored Agent Skills via Trace-Conditioned Skill Revision},
  author = {Liu, Yuxuan and Su, Zhaochen and Xie, Lingyun and Zhang, Yuhao and Zong, Qing and Guo, Jiahe and Xie, Zhongwei and Ji, Yiyan and Yim, Yauwai and Luo, Hongyu and Ren, Xiyu and Ruan, Chenyu and Li, Haoran and Song, Yangqiu},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2026},
  year = {2026},
  url = {https://arxiv.org/abs/2606.01139}
}
```
