---
name: datool-scorers
description: Create, test and revise Datool JavaScript or LLM scorers against real traces, including immutable versions and revision conflict handling.
---

# Develop Datool scorers

CLI prerequisite: `@datool/cli >=0.2.0`. Run `datool --version` and `datool doctor --json` first. Use browser login (`datool auth login`) or the API-key configuration described in the [Datool setup skill](../datool/SKILL.md).

Use connected MCP or CLI with DATOOL_BASE_URL, DATOOL_PROJECT_ID and DATOOL_API_KEY in the environment. Inspect schemas with `datool agent tools <operation>`. Read configuration/versions with scorers:read; saving needs scorers:write. test_scorer currently requires scorers:read, scorers:write, traces:read and datasets:read, even without optional dataset context.

Define what passes and which evidence is required before choosing the scorer. For an exact JSON criterion, adapt [assets/exact-json.json](assets/exact-json.json), a create_scorer input that compares objects independently of key order while preserving array order. It is an example criterion, not a calibrated quality judge.

```sh
datool scorers get scorer-id
datool scorers versions scorer-id
datool scorers version scorer-id --version-id immutable-version-id
datool scorers create --input @exact-json.json
datool scorers test --input @preview.json
datool scorers update scorer-id --expected-revision 2 --input @updated-scorer.json
```

The MCP equivalents are get_scorer, list_scorer_versions, get_scorer_version, create_scorer, test_scorer and update_scorer. Version lists page with nextCursor. Both create and update wrap the complete configuration in scorer; update additionally requires id and expectedRevision. On conflict, reload and reconcile instead of blindly increasing the revision.

A saved preview input is:

```json
{
  "scorerId": "scorer-id",
  "versionId": "immutable-version-id",
  "traceId": "trace-id",
  "datasetId": "dataset-id",
  "datasetItemId": "item-id",
  "datasetVersionId": "snapshot-id"
}
```

For inline previews, replace scorerId/versionId with scorer. Dataset context requires both datasetId and datasetItemId; datasetVersionId selects frozen expected outputs. Without it the preview uses the current item. The scorer executes against actual trace evidence and returns persisted: false. LLM previews can call a provider and incur cost within the user's authorized work.

Select requiredEvidence as invocation, internal or complete according to the criterion; missing required evidence must not become an automatic pass. Return a passed classification or configure a numeric threshold. Keep allowSkip intentional because gates reject skipped results by default.

Preview known passing, failing and missing-context cases. Keep a held-out evaluation set when assessing judge quality; successful execution or agreement with another model is not human validation. Record immutable version IDs so later evaluations reproduce the tested scorer.

## Calibration and iteration

Use the [evaluation improvement loop](../datool-evaluations/SKILL.md). Calibration uses ordinary dataset cases, declared expected judgments and saved evaluations. Known negative controls should be rejected; do not demand that every calibration case pass a quality gate. Verify claims against source evidence, separate false passes/false failures from runtime errors and retain reference provenance. After changing a judge, re-score the same outputs via sourceRunId and inspect configurationChanges. Baseline quality gates require the exact same judge versions. Latest is the normal selection; explicit pins are for reproducibility or controlled comparisons.
