---
name: datool-datasets
description: Curate Datool evaluation cases, import or edit dataset items atomically, and create immutable snapshots for reproducible runs.
---

# Curate Datool datasets

CLI prerequisite: `@datool/cli >=0.2.0`. Run `datool --version` and `datool doctor --json` first. Use browser login (`datool auth login`) or the API-key configuration described in the [Datool setup skill](../datool/SKILL.md).

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

Adapt [assets/bulk-create.json](assets/bulk-create.json) for an initial bulk import. Set each case's input and intended expectedOutput explicitly. Retain sourceTraceId when promoting production evidence; trace-mode evaluation requires existing source traces, while connected mode executes the app on case inputs.

A bulk request contains datasetId plus create, update and/or delete. CLI accepts the dataset ID positionally. Updates use {id, patch}; deletes are item IDs. The total is 1–100 changes, applied atomically. Use each existing item once in a batch. expectedHash from a prior bulk response or snapshot guards against intervening changes. If a batch fails, inspect the reason and revise it; no partial progress should be assumed. Evaluation history may prevent deleting a referenced live item.

Freeze a snapshot before a reproducible run and record its id as datasetVersionId plus contentHash. Snapshots retain input, expected output, metadata and source references after live-item edits/deletions. Identical content returns the existing snapshot and original label. The content cap is 8 MiB. Source trace evidence is captured when the evaluation starts; snapshot creation alone does not freeze that evidence.

CLI file synchronization uses a different document: {format: 1, kind: "dataset", key, items: [{key, input, expectedOutput, metadata}]}. Do not feed a bulk-operation input to datasets push. Pull an existing resource first to establish project-bound sync state; omitted push items are retained. Use --replace only when replacing the intended current resource after resolving its conflict.

Report imported/updated/deleted counts and snapshot identity. Separate reviewed labels, automatically generated expectations and unreviewed cases when describing evaluation coverage.
