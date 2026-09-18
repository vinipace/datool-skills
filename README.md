# Datool skills

Agent skills for investigating AI traces, building scorers, curating datasets, running evaluations and querying Datool analytics.

## Install

Install the complete pack into a project:

```sh
npx skills add vinpac/datool-skills --skill '*'
```

Target an agent explicitly:

```sh
npx skills add vinpac/datool-skills --skill '*' --agent codex
npx skills add vinpac/datool-skills --skill '*' --agent claude-code
npx skills add vinpac/datool-skills --skill '*' --agent cursor
```

Add `--global` to install across projects. The [skills installer](https://github.com/vercel-labs/skills) supports these options and additional agents.

List the available skills before installing:

```sh
npx skills add vinpac/datool-skills --list
```

Install an individual workflow with `--skill datool-traces`, for example. Install all six when using the general `datool` router, which links to the focused workflows.

## Included skills

| Skill | Purpose |
| --- | --- |
| [datool](skills/datool/SKILL.md) | Discover operations, integrate managed prompts and combine workflows |
| [datool-traces](skills/datool-traces/SKILL.md) | Investigate traces, spans, sessions and scores |
| [datool-scorers](skills/datool-scorers/SKILL.md) | Develop, preview and version scorers |
| [datool-datasets](skills/datool-datasets/SKILL.md) | Curate cases, edit items atomically and freeze snapshots |
| [datool-evaluations](skills/datool-evaluations/SKILL.md) | Execute apps, re-score evidence, compare runs and gate CI |
| [datool-analytics](skills/datool-analytics/SKILL.md) | Query metrics, preview dashboards, resolve links and export data |

Seven JSON starters accompany the focused skills. Replace their example resource IDs, request keys, thresholds and dates before executing them.

## Connect to Datool

Skills contain instructions and examples. They require an existing Datool deployment and either an authenticated MCP connection or a compatible Datool CLI.

For MCP, connect your agent to your deployment's `/api/mcp` endpoint and complete its OAuth project selection and permission consent. Use `describe_agent_operations` to inspect available operations.

For CLI access, install `@datool/cli >=0.2.0` and configure:

```sh
npm install --save-dev @datool/cli@^0.2.0
export DATOOL_BASE_URL=https://your-datool-host
export DATOOL_PROJECT_ID=your-project-id
# Set DATOOL_API_KEY through your environment or secret manager.
npx datool --version
npx datool doctor --json
npx datool agent tools
datool agent tools start_eval_run
```

For interactive use, `npx datool auth login --datool <host>` opens browser organization/project selection and stores credentials in the OS credential store. Agents and CI can continue using API-key environment variables. The CLI loads project-root `.env`, then `.env.local`; shell variables win. `--env-file <path>` replaces the automatic files, and `--no-env` opts out. Keep credential files out of version control. Normal `npx datool` and `bunx datool` use Node; direct Bun execution requires `bun --no-env-file <datool.js> ...`.

Version 0.1.0 does not include the advertised agent commands. This pack requires the CLI's `agent` commands and the server's `POST /api/agent/:operation` API. If discovery is unavailable, use a deployment/CLI release containing the agent foundations before following these workflows. Doctor and CLI OAuth require server CLI protocol 1. Doctor distinguishes an old server from invalid credentials (401) and valid credentials with insufficient permissions (403). A missing MCP tool can also mean the token lacks the necessary consented scopes.

A completed evaluation reports technical execution; use its quality gate to determine whether it passes. Connected app runs and LLM scorers can incur costs. Each skill documents its permissions, pagination, limits and reproducibility requirements.

For the native prompt SDK and connected prompt experiments, read [managed prompts](skills/datool/references/prompts.md). Standalone fetching needs SDK support and `prompts:read`; connected experiments also need a compatible bridge or HTTP adapter, a server advertising `promptOverrides`, and the evaluation/trace permissions listed in the reference. Base CLI command support alone does not establish native prompt support.

## Use

For example, ask your agent:

- "Use $datool-traces to investigate the errors in the last 24 hours."
- "Use $datool-datasets to freeze these regression cases as a snapshot."
- "Use $datool-evaluations to compare this candidate run against its baseline."

CLI credentials, MCP configuration and application data are not included in this pack.

## Validate and maintain

```sh
node scripts/validate.mjs
node scripts/test-cli-distribution.mjs 0.2.0
```

The validation workflow checks pack structure, local references, JSON assets and installer discovery. It also installs the exact published npm CLI in a clean directory and exercises agent discovery, trace reads, env precedence and diagnostics under Node and Bun against a local HTTP fixture. It does not use workspace CLI source, run your application, or call LLM providers.

Keep complete skill folders together when updating them so examples and links remain available. Check command and permission changes against the compatible Datool server before publishing updates.

## License

[Apache License 2.0](LICENSE).
