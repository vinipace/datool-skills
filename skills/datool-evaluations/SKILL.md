---
name: datool-evaluations
description: Run Datool evaluations, replay connected apps, re-score frozen evidence, compare cases and enforce CI quality gates with reproducible versions.
---

# Run and gate Datool evaluations

CLI prerequisite: `@datool/cli >=0.2.0`. Run `datool --version` and `datool doctor --json` first. Use browser login (`datool auth login`) or the API-key configuration described in the [Datool setup skill](../datool/SKILL.md).

Use connected MCP or CLI with DATOOL_BASE_URL, DATOOL_PROJECT_ID and DATOOL_API_KEY in the environment. Inspect the live schema with `datool agent tools start_eval_run`. Reads, comparisons and gates require evals:read. Starting requires evals:write, evals:read, traces:read, datasets:read and scorers:read.

Choose the execution mode from the user's task:

- Existing evidence: start_eval_run with traceIds, or a dataset whose items have sourceTraceId.
- Fresh app execution: use mode connected, an observed appId and datasetId. Adapt [assets/connected-run.json](assets/connected-run.json); pin datasetVersionId and evaluatorVersionIds.
- Judge changes on the same evidence: use sourceRunId and the chosen evaluators. Adapt [assets/rescore.json](assets/rescore.json). Do not combine sourceRunId with a new dataset, trace selector or connected mode. Re-scoring does not invoke the app again.

Use existing authorization for app calls and LLM judge costs. Keep one stable requestKey for a logical start; retry uncertain delivery with the same key and identical inputs. Changed inputs conflict. For a still-starting or interrupted request, inspect list_eval_runs using metadata.agentRequestKey before explicitly deciding whether to create a new request. Do not silently generate a new key to bypass a conflict.

```sh
datool evals run --input @connected-run.json --wait --timeout 300
datool evals wait run-id --timeout 300
datool evals get run-id --limit 50
datool agent call start_eval_run --input @rescore.json
datool evals compare --left-id baseline-id --right-id candidate-id --offset 0
datool agent call gate_eval_run --input @gate.json
```

Poll get_eval_run to a terminal state; follow nextCursor to inspect all targets/results. A completed status means execution finished, not that quality passed. compare_eval_runs uses nextOffset. Pin versions and record the actual versions used, run ID, case count and evidence origin.

Adapt [assets/gate.json](assets/gate.json) to the user's quality thresholds. gate_eval_run aggregates the entire run. Defaults reject incomplete, empty, missing, skipped/unclassified and technically failed results; minPassRate defaults to 1 and minScore to 0. Define scorer thresholds or passed classifications. allowUnscored does not make a wholly unclassified run pass. Baseline gates require comparable scorer and case populations, inputs and expected outputs; mean-score regression is not a significance test.

CLI exit codes are 0 for command success, 1 for usage/request failure, 2 for a failed gate, and 3 for a wait timeout. Preserve the gate's exit code in CI. A wait alone is insufficient to gate quality.

Runs currently execute in the persistent server process. Interrupted runs are marked failed on restart, with no automatic resume or cancellation workflow. Limits are 10,000 targets, 100,000 results and 8 MiB of initial evidence; split larger work into explicitly bounded runs.

## Native managed prompts

For connected SDK applications, use top-level `promptOverrides` keyed by
published slug, with optional `version` and `model`. Adapt
[the prompt override starter](assets/prompt-overrides-run.json) with observed IDs.
Keep managed prompt controls out of dataset inputs. Confirm installed SDK/bridge
support and the live `start_eval_run` schema. The SDK credential additionally
needs `prompts:read`, `evals:read` and `traces:write`; HTTP handlers must install
the scope with `withDatoolRequest`.

Datool snapshots all published defaults before execution, including lazy
discoveries. Inspect `metadata.promptConfig` and `Prompt: <slug>` spans for
baseline and actual resolutions. Use a new requestKey when overrides change.
Re-scoring rejects overrides and uses frozen evidence without prompt reads.
Read [managed prompts](../datool/references/prompts.md) for scope, precedence and
cache behavior.
