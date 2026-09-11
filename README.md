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
| [datool](skills/datool/SKILL.md) | Discover operations and combine workflows |
| [datool-traces](skills/datool-traces/SKILL.md) | Investigate traces, spans, sessions and scores |
| [datool-scorers](skills/datool-scorers/SKILL.md) | Develop, preview and version scorers |
| [datool-datasets](skills/datool-datasets/SKILL.md) | Curate cases, edit items atomically and freeze snapshots |
| [datool-evaluations](skills/datool-evaluations/SKILL.md) | Execute apps, re-score evidence, compare runs and gate CI |
| [datool-analytics](skills/datool-analytics/SKILL.md) | Query metrics, preview dashboards, resolve links and export data |

Six JSON starters accompany the focused skills. Replace their example resource IDs, request keys, thresholds and dates before executing them.

## Connect to Datool

Skills contain instructions and examples. They require an existing Datool deployment and either an authenticated MCP connection or a compatible Datool CLI.

For MCP, connect your agent to your deployment's `/api/mcp` endpoint and complete its OAuth project selection and permission consent. Use `describe_agent_operations` to inspect available operations.

For CLI access, install the Datool CLI provided for your deployment and configure:

```sh
export DATOOL_BASE_URL=https://your-datool-host
export DATOOL_PROJECT_ID=your-project-id
# Set DATOOL_API_KEY through your environment or secret manager.
datool agent tools
datool agent tools start_eval_run
```

This pack requires the CLI's `agent` commands and the server's `POST /api/agent/:operation` API. If discovery is unavailable, use a deployment/CLI release containing the agent foundations before following these workflows. A missing MCP tool can also mean the token lacks the necessary consented scopes.

A completed evaluation reports technical execution; use its quality gate to determine whether it passes. Connected app runs and LLM scorers can incur costs. Each skill documents its permissions, pagination, limits and reproducibility requirements.

## Use

For example, ask your agent:

- "Use $datool-traces to investigate the errors in the last 24 hours."
- "Use $datool-datasets to freeze these regression cases as a snapshot."
- "Use $datool-evaluations to compare this candidate run against its baseline."

CLI credentials, MCP configuration and application data are not included in this pack.

## Validate and maintain

```sh
node scripts/validate.mjs
```

The validation workflow checks pack structure, local references, JSON assets and skill discovery through the installer. It does not run your application or call LLM providers.

Keep complete skill folders together when updating them so examples and links remain available. Check command and permission changes against the compatible Datool server before publishing updates.

## License

[Apache License 2.0](LICENSE).
