---
name: datool
description: Use Datool MCP, CLI and SDK to investigate AI workflows, integrate managed prompts, and discover available operations and project permissions.
---

# Datool

Prefer connected Datool MCP tools. CLI workflows require `@datool/cli >=0.2.0`; check `datool --version`, then `datool doctor --json` before diagnosing a missing command or failed connection. Upgrade older installations with `npm install --save-dev @datool/cli@^0.2.0` in the target project. Inspect the current contract with `datool agent tools` or `datool agent tools <operation>`. Execute any operation with `datool agent call <operation> --input @input.json`. The equivalent MCP discovery tool is `describe_agent_operations`.

For agents/CI, supply DATOOL_BASE_URL, DATOOL_PROJECT_ID and DATOOL_API_KEY through the environment or an uncommitted project env file. For interactive use, `datool auth login --datool <host>` opens browser organization/project selection and saves tokens in the OS credential store. API keys take precedence. The CLI loads project-root `.env`, then `.env.local`; shell values win. `--env-file <path>` replaces those files; `--no-env` disables loading. Normal `npx datool`/`bunx datool` uses Node; direct Bun execution requires `bun --no-env-file <datool.js> ...`. Keep credentials out of commits, command arguments and reports. Doctor distinguishes incompatible servers, invalid credentials (401), and missing permissions (403, including traces:read).

MCP tokens are bound to a project and consented scopes. Missing tools can mean insufficient consent; an unavailable operation can also mean the installed CLI or deployed server predates these foundations. Inspect discovery and configuration before claiming that a capability is absent. Use returned IDs and schemas, not guessed endpoints.

For published prompt fetching, rendering, invocation-scoped overrides and connected prompt experiments, read [managed prompts](references/prompts.md). Confirm installed SDK and deployed server support before using the native API.

Read the focused skill matching the work:

- [datool-traces](../datool-traces/SKILL.md): investigate failures, latency and session behavior using recorded evidence.
- [datool-scorers](../datool-scorers/SKILL.md): develop, preview and version JavaScript or LLM scorers.
- [datool-datasets](../datool-datasets/SKILL.md): curate cases, perform atomic edits and freeze runnable snapshots.
- [datool-evaluations](../datool-evaluations/SKILL.md): execute apps, re-score frozen evidence, compare runs and gate CI.
- [datool-analytics](../datool-analytics/SKILL.md): query semantic metrics, preview dashboards, resolve links and export bounded data.

For a regression investigation, connect the relevant workflows: inspect representative traces, define the failure criterion, curate cases, freeze dataset/scorer versions, execute the evaluation, then compare and gate it. Preserve the user's chosen scope and existing authorization for app execution and model costs.

Record the project, resource IDs, versions, inspected population and evidence limitations. A completed run means execution finished; quality requires the gate and case-level evidence. Source code, local tests and production behavior are distinct evidence.
