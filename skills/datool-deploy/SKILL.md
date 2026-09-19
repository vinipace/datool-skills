---
name: datool-deploy
description: Manually release the Datool server to Dokku on Netcup. Use for deploying a committed revision, reusing a verified CI image, or building and testing an image locally when CI cannot deploy. Covers image import, migrations, web and worker verification, and release recovery; not playground app connections or npm package publishing.
---

# Datool deployment

Deploy the exact image that passed verification. Build off the production server, import through `disk:load-image`, then prove the intended revision is running and serving real requests.

## Establish the release

1. Resolve the user's intended revision to a full commit SHA in `vinpac/datool`. If they request current `main`, fetch it first. Inspect tracked, untracked and deleted files; preserve unrelated edits. A request to deploy current code does not silently include unrelated uncommitted work. Resolve an ambiguous release target before deploying it.
2. Read the selected revision's `.github/workflows/deploy.yml`, `Dockerfile`, `scripts/test-docker.sh`, `docs/dokku.md`, and `ops/dokku-deploy/README.md`. These define the current tests and import protocol; reconcile changes against this skill before use.
3. Confirm the target, SSH access, existing release and disk capacity. Record the previous source image. Check whether another deployment is active; serialize manual releases with CI and other operators. For migration changes, establish a recent recoverable database backup and consider schema compatibility before release.
4. Honor existing deployment authorization. A request to create this skill or explain deployment alone does not authorize a production release. Do not ask again when the user has already authorized the chosen target and release.

## Target and access

This is the maintainer workflow for Vinicius's deployment. Baseline from the September 18, 2026 migration; confirm against current configuration:

| Setting | Value |
| --- | --- |
| Source | `vinpac/datool` |
| Production | `https://datool.vinipace.com` |
| Netcup host | `62.83.32.238`, Linux AMD64 |
| Dokku app | `datool` |
| Formation | One `web` and one `worker` |
| Data services | Postgres `datool-db`, Redis `datool-redis` |
| Maintainer SSH | `vinicius`, followed by interactive `su -` for Dokku administration |
| CI SSH | `datool-deploy`, restricted forced command |

Use the maintainer's existing key and pinned host key. On macOS, `-o UseKeychain=yes` can unlock the existing key. Never disable host-key verification, copy a password from conversation history into a command, or print private keys/config secrets. Handle an interactive password through an appropriate secure prompt. If privileged access is unavailable, finish image preparation and ask only for the missing access.

The CI private key is stored in GitHub secrets, not available through `gh secret`. A temporary migration copy was removed. Use the restricted account only if a usable, authorized key is actually available; this workflow does not require creating keys or broadening permissions. Root SSH and SSH password authentication were disabled during setup.

The old `91.107.238.205` host is retired for Datool and still hosts other services. Do not deploy there based on an old Git remote.

## Prepare and deploy

Read [the manual runbook](references/manual-release.md) and follow the applicable image-source path:

- **Verified CI artifact:** Inspect the run's commit and successful `verify` job, then download `production-image`. A failed deployment job does not invalidate a successful verification job. Confirm the artifact belongs to the selected commit and run; artifacts currently expire after one day.
- **Local fallback:** Build the selected commit in an isolated checkout, targeting `linux/amd64`, run the workflow's infrastructure, image and disposable-service tests, then export that same image. A build or HTTP response alone is insufficient verification.

Validate the bundle with [verify_artifact.py](scripts/verify_artifact.py). It checks exact metadata filenames, checksums, commit/run identity, tag format and the 8 GiB declared-size limit. It does not authenticate the source or prove tests passed. Confirm provenance separately, and inspect the loaded image's revision label and architecture.

Import with `disk:load-image datool IMAGE IMAGE_BYTES`. This preserves the installed capacity checks, release-image retention and Dokku migration path. Do not substitute a production source build, direct Git push or a raw import that bypasses this wrapper. Keep production configuration, databases, Redis and `/app/.data` intact during an ordinary release. Never run the disposable test seeding workflow against production.

## Prove and report

- Inspect release output for both application and CMS migrations. Confirm `git:report --git-source-image` matches the chosen image, and both web and worker are running.
- Check the seven public routes in the runbook. For end-to-end evidence, use an authorized account/project to verify login and submit a uniquely identifiable synthetic trace through the real ingestion route, then read its persisted result after worker processing. Record what was exercised; HTTP 200 is only a smoke check.
- Report source SHA, image reference, local or CI verification, deployment result, public behavior, and any remaining access or verification gaps separately. Do not call local success a production release.
- Keep the previous successful image and release evidence. Delete only temporary files/credentials created for this run when no longer needed. On failure, follow the runbook's recovery guidance before retrying or rolling back.

This skill deploys the server. CI repair, npm publication, backup scheduling, logging-provider setup and server retirement are separate work unless requested.
