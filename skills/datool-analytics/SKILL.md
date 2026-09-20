---
name: datool-analytics
description: Query Datool semantic metrics, inspect dashboard and saved-view results, resolve resource links and export paginated traces, datasets or evaluation data.
---

# Query and export Datool data

Use the configured Datool connection. See [connection and discovery](../datool/SKILL.md#connection-and-discovery) when setting up access or checking a required capability.

Metrics need metrics:read; dashboard previews also need dashboards:read. Saved-view data requires views:read, traces:read and evals:read.

```sh
datool metrics metadata
datool metrics query --input @trace-count.json
datool dashboards preview dashboard-id
datool views data saved-view-id --offset 0 --limit 50
datool traces resolve trace-id
datool datasets resolve support/cases
datool traces export --filter 'status = "errored"' --max-rows 10000 --out errors.ndjson
datool datasets export dataset-id --out items.ndjson
datool evals export run-id --out results.ndjson
```

Discover get_metrics_metadata before constructing query_metrics or batch_metrics inputs. Adapt the date window in [assets/trace-count.json](assets/trace-count.json). Queries use {query: ...}; batches use {queries: [...]} with 1–40 queries. Use catalog members and semantic filters, not SQL. Record the reporting window/timezone, quality fields and execution limits before presenting aggregates as complete.

preview_dashboard executes stored widget queries in order on a shared semantic snapshot; get_dashboard reads configuration only. Batch results also share a snapshot. Saved-view rows use nextOffset. Saved selector views and custom eval-run display views are different resource types; use get_saved_view_data for the former.

Use resolve_* operations to obtain canonical workspace URLs. IDs take precedence; supported name lookups are exact and ambiguity fails. Scorers also resolve by slug; dashboards resolve by ID. A returned linkKind of collection explicitly means the URL opens a collection, so do not invent a detail route.

## Export completeness and limits

Exports stream NDJSON pages into an atomic output file. Dataset IDs export items; evaluation run IDs export target rows with nested results, saved reasonings and errors. Without an ID these commands export collection summaries. Check the stderr manifest for `complete: true` and `nextCursor: null` before claiming all requested rows were exported. `complete: false` with a nextCursor is a bounded partial export, even when the command exits successfully. Resume with `--cursor` into a new file using the same selection and options; preserve each manifest and combine the parts when assessing coverage.

The default row cap is 10,000; `--max-rows` accepts up to 100,000. Exceeding the 256 MiB byte cap fails the export without publishing its temporary file. Reduce the requested rows per part, then follow continuation cursors. When full spans are unnecessary, compact rows plus selected target reads can reduce export size. Existing files require an intentional `--replace`.

A successful export command is not proof of complete coverage. Live pagination observes a changing collection, not a database-wide immutable snapshot. Use dataset snapshots for frozen cases and report any partial pages or query caps. Keep unknown measures distinct from zero and distinguish technical run completion from evaluation quality in reports.
