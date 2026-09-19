---
name: datool-datasets
description: Curate Datool evaluation cases, import or edit dataset items atomically, and create immutable snapshots for reproducible runs.
---

# Curate Datool datasets

Use `@datool/cli >=0.3.0` for the current convenience commands; older agent clients can use generic `agent call` on a compatible server. Run `datool --version` and `datool doctor --json` first. See the [Datool setup skill](../datool/SKILL.md) for authentication, capability discovery and permissions.

Use connected MCP or CLI with DATOOL_BASE_URL, DATOOL_PROJECT_ID and DATOOL_API_KEY in the environment. Discover schemas with `datool agent tools <operation>`. Reads require datasets:read; edits need datasets:write, and snapshot creation requires both.

```sh
datool datasets list --filter support
datool datasets items dataset-id --limit 50
datool datasets bulk dataset-id --input @bulk-create.json
datool datasets snapshot dataset-id --label release-42
datool datasets snapshots dataset-id
datool datasets version dataset-id --version-id snapshot-id --limit 50
```

These map to list_datasets, list_dataset_items, bulk_dataset_items, create_dataset_snapshot, list_dataset_snapshots and get_dataset_snapshot. Dataset list filter is text search over name and description; item and snapshot pages use nextCursor, not a trace-style filter.

Adapt [assets/bulk-create.json](assets/bulk-create.json) for an initial bulk import. Set each case's input explicitly and leave expectedOutput null unless a reference has been reviewed. Retain sourceTraceId when promoting production evidence; trace-mode evaluation requires existing source traces, while connected mode executes the app on case inputs.

For a connected app, inspect its input/output schemas with list_apps/get_app before curating cases. Dataset input is the raw app input object, not run_app's operation wrapper or the webhook transport envelope. Agent inputs include a messages array. Both local bridges and HTTP apps use the same dataset format; the transport adds any envelope. expectedOutput is the reference for scoring and is not sent as app input.

A bulk request contains datasetId plus create, update and/or delete. CLI accepts the dataset ID positionally. Updates use {id, patch}; deletes are item IDs. The total is 1–100 changes, applied atomically. Use each existing item once in a batch. expectedHash from a prior bulk response or snapshot guards against intervening changes. If a batch fails, inspect the reason and revise it; no partial progress should be assumed. Evaluation history may prevent deleting a referenced live item.

Freeze a snapshot before a reproducible run and record its id as datasetVersionId plus contentHash. Snapshots retain input, expected output, metadata and source references after live-item edits/deletions. Identical content returns the existing snapshot and original label. Updated servers store snapshot cases separately, allowing more than 8 MiB of aggregate captured source evidence while keeping each response page bounded to 8 MiB; follow nextCursor. Older servers cap the entire snapshot at 8 MiB. If that blocks full evidence, report the server compatibility gap instead of silently stripping provenance. Legacy trace evidence is captured when the evaluation starts; span-backed cases already retain immutable selected evidence from promotion.

CLI file synchronization uses a different document: {format: 1, kind: "dataset", key, items: [{key, input, expectedOutput, metadata}]}. Do not feed a bulk-operation input to datasets push. Pull an existing resource first to establish project-bound sync state; omitted push items are retained. Use --replace only when replacing the intended current resource after resolving its conflict.

Report imported/updated/deleted counts and snapshot identity. Separate reviewed labels, automatically generated expectations and unreviewed cases when describing evaluation coverage.

For agent findings and ratings, use the [AI-labelled review workflow](../datool/references/reviews.md). API-key and OAuth reviews retain authenticated provenance and separate AI completion counts. A completed AI review is not human-verified ground truth and does not update dataset expected outputs.

## Production span to evaluation workflow

1. Select representative production invocations and inspect exact span input/output, timestamps and model/prompt attributes. A parent trace with null output may still contain several useful invocations. Do not reconstruct inputs by guessing variables from arbitrary prompt prose.
2. Use `promote_spans` (`datool datasets promote dataset-id --input @promotion.json`) to preview exact `{traceId, spanId}` selections, then save with `preview: false` and the returned `expectedEvidenceHash`. Up to 100 promotions are atomic. `sourceSpanId` is a native case field; two spans in one trace remain separate cases. Selected descendants are captured, excluding siblings and scorer-execution subtrees, without creating production traces. Limits: 1 MiB/1,000 spans per invocation and 8 MiB per batch.
3. Keep `observedOutput` as an unreviewed observation. `expectedOutput` defaults to null. Set a reviewed reference explicitly or deliberately request `copyObservedOutput: true`; copying does not establish correctness. `mappedInput` explicitly supplies structured app variables while `sourceSpanEvidence.input` retains the capture. Scorers see captured invocation input/output; connected runs send the case's mapped input to the app and validate its schema.
4. Freeze with `create_dataset_snapshot`; record datasetVersionId/contentHash. Span-backed snapshots retain captured evidence from promotion; legacy trace-backed snapshots freeze source references, and their trace evidence is frozen when the evaluation starts.
5. Define independent criteria. Structure/citation validity, grounding, coverage and annotation fidelity must not silently substitute for each other.
6. Use `check_scorer_runtime` for configuration only. Explicitly use `probe_scorer_runtime` with up to 3 selected scorers, optional version pins, and one representative traceId plus optional spanId/dataset context to verify actual execution. Probes may incur model/sandbox usage and retain execution spans. Configuration alone proves neither authentication/connectivity nor successful execution. Calibrate known pass, fail, missing-evidence and criterion-disagreement examples before scaling.
7. When asked to run an evaluation, create a named, visible `start_eval_run` promptly and return its URL and the resolved scorer versions. Preliminary previews should be small and communicated. Multi-case calibration belongs in a named saved calibration run. `test_scorer` is a preview: no evaluation run or score result is saved, but recorded-trace execution spans are retained.
8. Prefer native CLI `evals wait` and `evals export run-id --out results.ndjson`. With MCP, pace get_eval_run polling and page through every result. Completed execution is separate from quality passing. Infrastructure failures have null scores and are not valid low quality judgments. A persistent provider/sandbox failure blocks later requests to that runtime within the run; inspect diagnostics, request ID and Retry-After. HTTP 429 alone does not mean out of credits.
9. After judge/rubric/provider/model changes, recalibrate and create a new run using `sourceRunId` with new explicit evaluatorVersionIds. This re-scores the same frozen evidence and references even after live source changes.
10. After changing the extractor, prompt, or application model, execute the connected app again on the frozen dataset. Re-scoring old outputs does not test a changed application. Keep development/calibration cases separate from untouched evaluation cases. Purposively selected regressions and agreement with old observations are not production accuracy.

## Reviewed reference corrections

Keep proposed corrections separate from application changes. Use the existing [AI-labelled review workflow](../datool/references/reviews.md) to retain the proposed value, reason, source evidence and run/target IDs. Agent-authored reviews remain AI-labelled; a metadata label is not human verification. After authorized review, discover update_dataset_item and update expectedOutput on the existing case with expectedVersionId, preserve its input and identity, attach the review reference in metadata and create a new immutable snapshot. Do not feed expected answers to the application or silently backfill old run evidence. See the [disciplined improvement loop](../datool-evaluations/SKILL.md).
