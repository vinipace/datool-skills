---
name: datool
description: Use Datool MCP, CLI and SDK to connect apps, integrate managed prompts, debug AI workflows, submit AI-labelled reviews, and route evaluation work.
---

# Datool

Prefer connected Datool MCP tools. App commands and outbound `connect` require `@datool/cli >=0.3.0` and a server supporting app connections; existing trace/scorer/dataset/evaluation commands require at least 0.2.0. Check `datool --version`, then `datool doctor --json` before diagnosing a missing command or failed connection. Inspect the current server contract with `datool agent tools` or `datool agent tools <operation>`. Execute a catalog operation with `datool agent call <operation> --input @input.json`. The equivalent MCP discovery tool is `describe_agent_operations`. A version in the repository does not establish that the package is published, installed or deployed.

For agents/CI, supply DATOOL_BASE_URL, DATOOL_PROJECT_ID and DATOOL_API_KEY through the environment or an uncommitted project env file. For interactive use, `datool auth login --datool <host>` opens browser organization/project selection and saves tokens in the OS credential store. API keys take precedence. The CLI loads project-root `.env`, then `.env.local`; shell values win. `--env-file <path>` replaces those files; `--no-env` disables loading. Normal `npx datool`/`bunx datool` uses Node; direct Bun execution requires `bun --no-env-file <datool.js> ...`. Keep credentials out of commits, command arguments and reports. Doctor distinguishes incompatible servers, invalid credentials (401), and missing permissions (403, including traces:read).

MCP tokens are bound to a project and consented scopes. Discovery lists operation contracts; it does not prove the current credential can execute them. Missing tools can mean insufficient consent, while an unknown operation can mean the deployed server predates it. Doctor checks compatibility, authentication and a minimal trace read; it does not check every evaluation scope, app or provider. Use returned IDs and schemas, then verify the operations needed for the user's flow.

For local development, `datool connect --watch` reloads source/import edits in fresh processes and resyncs schemas after active calls and result delivery finish; watching is opt-in and HTTP registrations are unchanged. Check installed CLI help for support.

For playground apps, local-to-hosted connections and HTTP webhook registration, read [app connections](references/apps.md). The shared operations include list_apps, get_app, register_app and run_app. AI/sandbox provider setup and custom-sample scorer previews still use separate UI surfaces; managed prompt operations are not in the shared catalog. Inspect discovery before assuming a newer server has closed these gaps.

For evidence review and findings, read [AI-labelled reviews](references/reviews.md). API-key and OAuth agents can submit notes, scores and annotations with trusted server attribution; completion is not human verification.

For published prompt fetching, rendering, invocation-scoped overrides and connected prompt experiments, read [managed prompts](references/prompts.md). Confirm installed SDK and deployed server support before using the native API.

Read the focused skill matching the work:

- [datool-traces](../datool-traces/SKILL.md): investigate failures, latency and session behavior using recorded evidence.
- [datool-scorers](../datool-scorers/SKILL.md): develop, preview and version JavaScript, Python or LLM scorers.
- [datool-datasets](../datool-datasets/SKILL.md): curate cases, perform atomic edits and freeze runnable snapshots.
- [datool-evaluations](../datool-evaluations/SKILL.md): execute apps, re-score frozen evidence, compare runs and gate CI.
- [datool-analytics](../datool-analytics/SKILL.md): query semantic metrics, preview dashboards, resolve links and export bounded data.
- [datool-deploy](../datool-deploy/SKILL.md): manually release the Datool server to Netcup through Dokku and verify the deployed image, web and worker. This maintainer workflow uses SSH and Docker rather than the product MCP/CLI.

For a regression investigation, connect the relevant workflows: inspect representative traces, define the failure criterion, curate cases, freeze dataset/scorer versions, execute the evaluation, then compare and gate it. Preserve the user's chosen scope and existing authorization for app execution and model costs.

Record the project, resource IDs, versions, inspected population and evidence limitations. A completed run means execution finished; quality requires the gate and case-level evidence. Source code, local tests and production behavior are distinct evidence.

For production invocation evaluation, follow the [span-to-case workflow](../datool-datasets/SKILL.md#production-span-to-evaluation-workflow). Use native span promotion, explicit references, runtime readiness and calibration, then return a saved evaluation URL promptly. Preview is not a saved evaluation.
