---
name: datool-evaluations
description: Run Datool evaluations, replay connected apps, re-score frozen evidence, compare cases and enforce CI quality gates with reproducible versions.
---

# Run and gate Datool evaluations

CLI prerequisite: `@datool/cli >=0.2.0`. Run `datool --version` and `datool doctor --json` first. Use browser login (`datool auth login`) or the API-key configuration described in the [Datool setup skill](../datool/SKILL.md).

Use connected MCP or CLI with DATOOL_BASE_URL, DATOOL_PROJECT_ID and DATOOL_API_KEY in the environment. Inspect the live schema with `datool agent tools start_eval_run`. Reads, comparisons and gates require evals:read. Starting requires evals:write, evals:read, traces:read, datasets:read and scorers:read.

Choose the execution mode from the user's task:

- Existing evidence: start_eval_run with traceIds, or a dataset whose items have sourceTraceId.
- Fresh dataset execution: discover the app with list_apps/get_app (apps:read), verify its input schema and availability, then use mode connected, an observed appId and datasetId. Both outbound local bridges and registered HTTP webhooks use this path. Adapt [assets/connected-run.json](assets/connected-run.json); normally omit version pins to resolve latest, then inspect the recorded versions. Provide evaluatorIds for a new selection; a parent/source run can supply its scorer selection. App-default scorers are not inherited.
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

Poll get_eval_run to a terminal state; follow nextCursor to inspect all targets/results. A completed status means execution finished, not that quality passed. compare_eval_runs uses nextOffset. Record the actual resolved versions used, run ID, case count and evidence origin.

Run reads and comparisons return exact frozen inputs/outputs and results without full spans by default. Use `get_eval_target` with `{id: runId, targetId: row.id}` for one case's saved evidence and scorer spans; the CLI equivalent is `evals target`. Older CLI versions can use `agent call get_eval_target --input` with that JSON. Explicit `includeEvidence: true` (`--include-evidence` for get, compare or export) embeds full evidence. Batches shrink automatically to fit 8 MiB, so always follow the returned nextCursor/nextOffset even when the page has fewer rows than requested. Waits remain lightweight.

When iterating on a judge, save its new version, then start a new request with sourceRunId and explicit evaluatorVersionIds. This uses the original frozen evidence and expected outputs without another app call. Use the same scorer IDs and immutable versions for automatic quality baseline gates. Changing a rubric creates a new scorer version: compare it explicitly as a judge change and recalibrate. When testing an app change, execute the frozen dataset again and compare those runs. Re-scoring alone cannot test changed app behavior.

Adapt [assets/gate.json](assets/gate.json) to the user's quality thresholds. gate_eval_run aggregates the entire run. Defaults reject incomplete, empty, missing, skipped/unclassified and technically failed results; minPassRate defaults to 1 and minScore to 0. Define scorer thresholds or passed classifications. allowUnscored does not make a wholly unclassified run pass. Baseline gates require comparable scorer and case populations, inputs and expected outputs; mean-score regression is not a significance test.

CLI exit codes are 0 for command success, 1 for usage/request failure, 2 for a failed gate, and 3 for a wait timeout. Preserve the gate's exit code in CI. A wait alone is insufficient to gate quality.

Runs execute in the persistent server process. Use cancel_eval_run to stop scheduling and fence late judgments. Use recover_eval_run after a lease expires or a terminal runtime failure to reuse successful evidence and judgments; it never redispatches uncertain app calls. Cancelled runs require an explicit new run. A CLI wait timeout stops waiting, not execution; continue with evals wait/get using the same run ID. Limits are 10,000 targets, 100,000 results and 8 MiB of initial evidence; split larger work into explicitly bounded runs. Connection and scorer payload limits also apply, so passing the run-level size check does not establish that every case can execute.

## Disciplined improvement loop

Use existing runs as iteration history, not a separately maintained experiment definition. Discover current `start_eval_run`, `get_eval_run`, `compare_eval_runs`, `recover_eval_run` and `cancel_eval_run` schemas before relying on newer fields. Recovery and iteration fields require a server that exposes them; if absent, report the compatibility gap and use supported existing primitives. Cancellation requires evals:read and evals:write. Recovery additionally requires traces:read, datasets:read, scorers:read and apps:read.

1. Retrieve every failed/error result using `get_eval_run` and its cursors. Inspect each candidate defect's frozen evidence with `get_eval_target`; read the judge's reasoning and exact scorer revision. Runtime failures and incomplete delivery are execution problems, not evidence of a product defect.
2. Verify each judge claim against the source. Mark unsupported claims, missing evidence and incorrect references separately. Keep AI-authored findings labelled AI; never convert an agent opinion into human verification by changing metadata.
3. Group verified defects by shared cause, retaining the run, target, source span and scorer references. Explanations and a small working table are sufficient; do not infer structured factual findings from prose automatically.
4. Change one cause at a time. For application/prompt/model changes, start with `parentRunId`; it reuses frozen cases and references, executes the app again and records resolved versions plus `metadata.configurationChanges`. Latest published prompts and active scorer versions are the default. Select `useRecordedVersions: true` to hold the recorded judges and prompt versions constant, then override only the prompt/model under test. For judge changes, use `sourceRunId`; the saved outputs and references stay fixed and the app never executes. For latest prompts with unchanged judges, copy the prior run's `evaluatorVersionIds` and omit useRecordedVersions. Optional individual pins also work.
5. Compare via the existing `compare_eval_runs`, following `nextOffset`. Its `configurationChanges` separates extractor settings from judge revisions; rows retain actual inputs and references. A change in judges means score movement cannot be attributed only to the application. Baseline gates require identical scorer IDs AND version IDs, inputs and expected outputs; viewing a comparison remains allowed.
6. Re-run the verified regression cases first, then the untouched evaluation cases with the same references and judges. Report regressions, remaining defects and denominators. Improvement on selected cases does not establish production accuracy.
7. Propose reference corrections separately through the existing review workflow. Record proposed value, source evidence, reason, run/target IDs and authenticated review provenance. Do not edit expectedOutput while measuring an application change. After the authorized review, update the existing dataset case with its current expectedVersionId (preserve case ID and input), retain the review link in metadata and create a new dataset snapshot. Compare it explicitly as a reference change; old runs remain frozen. See the [dataset workflow](../datool-datasets/SKILL.md) and [AI-labelled reviews](../datool/references/reviews.md).

Calibration is an ordinary dataset plus declared expected judgments and an evaluation. Include known passes, known failures, missing-evidence examples and disagreements between criteria. Store declarations in dataset metadata or the accompanying review notes and compare them with actual judgments. A negative control correctly rejected by a judge is a calibration success, even though its quality score is low. Do not use the ordinary all-pass quality gate as a calibration-agreement gate. Report false passes, false failures, missing evidence and runtime errors separately. Recalibrate after changing a judge revision; agreement with AI-labelled expectations is not independent human validation.

A case exposes its execution stage and error in ordinary run reads. `invoking` means the app call was dispatched; `awaiting_delivery` means its output is saved but trace evidence is still arriving; `scoring` means the judges are running. Recovery preserves completed judgments (including legitimate quality failures), retries missing/error judgments and rechecks evidence delivery without rerunning a completed app. It dispatches only provably queued calls against the recorded app definition, blocks ambiguous completion and rejects a live worker. Cancel fences later judgment writes; an already dispatched app may finish. A wait timeout stops waiting only. Inspect run/target stages before choosing recovery, re-scoring or an explicit fresh application run.
