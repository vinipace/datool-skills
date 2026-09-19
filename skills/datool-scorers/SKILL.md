---
name: datool-scorers
description: Create, test and revise Datool JavaScript, Python or LLM scorers against real traces, including immutable versions and revision conflict handling.
---

# Develop Datool scorers

Use `@datool/cli >=0.3.0` for the current convenience commands; older agent clients can use generic `agent call` on a compatible server. Run `datool --version` and `datool doctor --json` first. See the [Datool setup skill](../datool/SKILL.md) for authentication, capability discovery and permissions.

Use connected MCP or CLI with DATOOL_BASE_URL, DATOOL_PROJECT_ID and DATOOL_API_KEY in the environment. Inspect schemas with `datool agent tools <operation>`. Read configuration/versions with scorers:read; saving needs scorers:write. test_scorer currently requires scorers:read, scorers:write, traces:read and datasets:read, even without optional dataset context.

Define what passes and which evidence is required before choosing the scorer. For an exact JSON criterion, adapt [assets/exact-json.json](assets/exact-json.json), a create_scorer input that compares objects independently of key order while preserving array order. It is an example criterion, not a calibrated quality judge.

## Runtime and configuration

JavaScript and Python scorers use the project's configured sandbox providers, including previews and evaluations. JavaScript defines `function evaluate({ trace, datasetItem })`; Python defines `def evaluate(trace, dataset_item=None)` and receives dictionaries. Return a finite `score` between 0 and 1 and optionally `passed` and `reason`. Use `reason`, not `reasoning`, in the code's return value. Keep code self-contained; JavaScript does not accept module imports, exports or TypeScript syntax, and project modules are not mounted in the sandbox. The serialized code/trace/dataset payload is capped at 1 MiB. A saved scorer does not prove its sandbox is configured or reachable.

For a new LLM scorer, choose an available project provider/model explicitly: Gateway chat models use `provider: "vercel-ai-gateway"` with a creator/model ID; native evaluation models use a supported Gateway or `typesafe-ai` model with `modelType: "evaluation"`. Configure `messages` with system/user roles, and `choices` with unique labels and unique numeric scores. Configure `threshold` to classify numeric scores. Omitting `provider` retains the legacy server OpenAI path; it does not automatically select the project Gateway key. AI and sandbox provider credentials are configured in Project settings; MCP/CLI do not currently configure them.

Templates support `{{trace}}`, `{{input}}`, `{{output}}`, `{{expected}}`, `{{metadata}}`, `{{datasetItem}}` and nested selectors. Missing nested fields produce errors; select narrow fields instead of interpolating an entire large trace. `chainOfThought` requests an evidence-based assessment before the choice. For vision, use up to four `imagePaths` selectors such as `output.image.url`, without template braces; values must be HTTPS image URLs or supported base64 image data URLs. Use a model that supports the evidence and structured output format, then validate a real preview.

## Preview and version

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

For inline configurations, replace scorerId/versionId with scorer; traceId is still required. Dataset context requires both datasetId and datasetItemId; datasetVersionId selects frozen expected outputs. Without it the preview uses the current item. The scorer executes against recorded trace evidence and returns persisted: false, meaning no score result is saved. It does record a scorer execution span, which is excluded from future scoring evidence. LLM and hosted sandbox previews can incur provider usage within the user's authorized work.

Span-backed cases run with the selected invocation subtree; legacy trace cases use their available trace evidence; requiredEvidence is no longer a scorer configuration field. Handle missing evidence in the criterion so it does not become an automatic pass. Return a passed classification or configure a numeric threshold. Execution errors produce null scores and must remain distinguishable from a valid zero. Keep LLM allowSkip intentional because gates reject skipped results by default.

Preview known passing, failing and missing-context cases. Keep a held-out evaluation set when assessing judge quality; successful execution or agreement with another model is not human validation. Record immutable version IDs so later evaluations reproduce the tested scorer.

The UI also supports custom input/output samples through a separate preview endpoint; the shared test_scorer operation does not accept those samples or a trace-ID array. Preview multiple recorded cases with separate calls, or use a version-pinned evaluation for a larger population. To capture fresh evidence, use [run_app](../datool/references/apps.md) and read its returned trace before testing. For a changed judge against identical saved evidence, follow the [re-scoring flow](../datool-evaluations/SKILL.md).

## Runtime readiness

`check_scorer_runtime` is read-only configuration inspection for up to 10 scorer IDs; it does not call providers. `probe_scorer_runtime` explicitly executes up to 3 on one representative `traceId`, optionally `spanId` and dataset context. Both accept `evaluatorVersionIds`. Probe needs scorers:read, scorers:write, traces:read and datasets:read, may incur usage, and retains execution spans without a saved evaluation. Dataset context requires both datasetId and datasetItemId. Discover these operations before use; generic CLI `agent call` works when a convenience alias is absent.

Use the [production span workflow](../datool-datasets/SKILL.md#production-span-to-evaluation-workflow) to capture cases. A runtime error has a null score; distinguish it from a legitimate failing judgment. After a persistent runtime failure, inspect diagnostics and provider request IDs before scaling. HTTP 429 alone does not establish an exhausted balance.

## Judge calibration

Use the included [brand-extraction calibration fixtures](assets/brand-extraction-calibration.json). The application repository also has [a calibration checker](https://github.com/vinpac/datool/blob/main/scripts/check-scorer-calibration.ts). Each synthetic fixture declares expected judgments independently. For the loading-placeholder fixture, known-brand context supplies no answer evidence: grounding rejects all emitted unsupported entities even with `isTextMentioned=false` or `mentionCount=0`; coverage passes because there are no supported brands omitted. Input validity separately fails. Missing response evidence produces skip for grounding and coverage under this explicit rubric. Do not generalize these choices to every extraction task.

Compare every criterion's observed judgment with its expected judgment; a runnable judge may still fail calibration. Native evaluation models map provider choices to configured numeric scores and may expose confidence/probabilities when returned. They do not currently return explanations; do not fabricate one or describe confidence as a calibrated probability of correctness. Changing the provider/model invalidates prior calibration evidence.

## Calibration and iteration

Use the [evaluation improvement loop](../datool-evaluations/SKILL.md). Calibration uses ordinary dataset cases, declared expected judgments and saved evaluations. Known negative controls should be rejected; do not demand that every calibration case pass a quality gate. Verify claims against source evidence, separate false passes/false failures from runtime errors and retain reference provenance. After changing a judge, re-score the same outputs via sourceRunId and inspect configurationChanges. For an application baseline, verify the exact same judge versions even if an older server gate only checks scorer IDs. Latest is the normal selection; explicit pins are for reproducibility or controlled comparisons.
