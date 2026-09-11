---
name: datool
description: Use Datool MCP or CLI for cross-workflow AI debugging and evaluation, or discover available operations and project permissions.
---

# Datool

Prefer connected Datool MCP tools. For CLI access, set DATOOL_BASE_URL, DATOOL_PROJECT_ID and DATOOL_API_KEY in the environment; keep credentials out of files and reports. Inspect the current contract with `datool agent tools` or `datool agent tools <operation>`. Execute any operation with `datool agent call <operation> --input @input.json`. The equivalent MCP discovery tool is `describe_agent_operations`.

MCP tokens are bound to a project and consented scopes. Missing tools can mean insufficient consent; an unavailable operation can also mean the installed CLI or deployed server predates these foundations. Inspect discovery and configuration before claiming that a capability is absent. Use returned IDs and schemas, not guessed endpoints.

Read the focused skill matching the work:

- [datool-traces](../datool-traces/SKILL.md): investigate failures, latency and session behavior using recorded evidence.
- [datool-scorers](../datool-scorers/SKILL.md): develop, preview and version JavaScript or LLM scorers.
- [datool-datasets](../datool-datasets/SKILL.md): curate cases, perform atomic edits and freeze runnable snapshots.
- [datool-evaluations](../datool-evaluations/SKILL.md): execute apps, re-score frozen evidence, compare runs and gate CI.
- [datool-analytics](../datool-analytics/SKILL.md): query semantic metrics, preview dashboards, resolve links and export bounded data.

For a regression investigation, connect the relevant workflows: inspect representative traces, define the failure criterion, curate cases, freeze dataset/scorer versions, execute the evaluation, then compare and gate it. Preserve the user's chosen scope and existing authorization for app execution and model costs.

Record the project, resource IDs, versions, inspected population and evidence limitations. A completed run means execution finished; quality requires the gate and case-level evidence. Source code, local tests and production behavior are distinct evidence.
