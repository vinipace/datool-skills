# Manual Datool release

Use Bash for the local command blocks. Resolve variables from inspected state; commands containing replacement text are templates. Run each phase only after the previous phase succeeds. Do not run a deployment to test or demonstrate this skill.

Source contracts: [workflow](https://github.com/vinpac/datool/blob/main/.github/workflows/deploy.yml), [Dokku guide](https://github.com/vinpac/datool/blob/main/docs/dokku.md), [restricted access](https://github.com/vinpac/datool/blob/main/ops/dokku-deploy/README.md), [disk management](https://github.com/vinpac/datool/blob/main/ops/dokku-disk/maintenance.py). Read these at the selected commit, since `main` can advance.

## 1. Resolve the target

In the application checkout, inspect `git status --short`, the remote and current branch. Fetch the requested remote ref. The example selects current `origin/main`; replace it if the user selected a different committed revision.

```bash
set -euo pipefail
APP_REPO="$(git rev-parse --show-toplevel)"
git remote -v
git status --short
git fetch origin main
REV=origin/main
SHA="$(git rev-parse --verify "${REV}^{commit}")"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]]
WORK="$(mktemp -d "${TMPDIR:-/tmp}/datool-release.XXXXXX")"
BUNDLE="$WORK/bundle"
mkdir -m 700 "$BUNDLE"
git worktree add --detach "$WORK/source" "$SHA"
```

Record `APP_REPO`, `SHA`, `WORK` and `BUNDLE` if changing shells. Set `SKILL_DIR` to this installed skill's actual directory, not the application repository. Use the isolated source checkout to read the current release contract. Do not copy `.env`, `.data`, private keys, local dependency folders or unrelated untracked files into it.

Before deployment, inspect active workflow runs and coordinate with any operator already deploying. Avoid overlapping manual and CI releases:

```bash
gh run list --repo vinpac/datool --workflow deploy.yml --limit 10
```

## 2A. Reuse a verified CI image

Choose a run for the intended SHA on `main`. Inspect its workflow, branch, commit and job conclusions; require the **Verify production image** job to have succeeded. Do not require the deploy job to have succeeded when repairing a failed handoff. Do not use an artifact from an unrelated run just because its name matches.

```bash
# Set RUN to the inspected positive numeric run ID.
gh run view "$RUN" --repo vinpac/datool \
  --json headSha,headBranch,workflowName,status,conclusion,jobs,url
gh run download "$RUN" --repo vinpac/datool \
  --name production-image --dir "$BUNDLE"
python3 "$SKILL_DIR/scripts/verify_artifact.py" "$BUNDLE" \
  --commit "$SHA" --run "$RUN"
```

An expired/missing artifact requires a new verified build. If verification itself failed, inspect why; a local build is not permission to skip the failing test. On a rerun, the artifact may retain an earlier successful attempt number within the same run.

Load the verified archive into the local Docker daemon to inspect the actual image. This is local; do not upload it to production yet:

```bash
IMAGE="$(cat "$BUNDLE/image-ref.txt")"
docker image load < "$BUNDLE/image.tar.gz"
test "$(docker image inspect "$IMAGE" --format '{{.Os}}/{{.Architecture}}')" = linux/amd64
test "$(docker image inspect "$IMAGE" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "$SHA"
test "$(docker image inspect "$IMAGE" --format '{{.Size}}')" = "$(cat "$BUNDLE/image-size.txt")"
```

If those checks pass, continue to phase 3. The successful CI verification already tested this image; a full duplicate test run is unnecessary unless new evidence raises a concern.

## 2B. Build locally when CI cannot supply an image

Needs a working Docker daemon with Buildx and AMD64 support, Python 3, Git, gzip and a SHA-256 utility. On Apple Silicon, Docker must support AMD64 emulation. Image build and service tests can be slow; continue reporting meaningful progress. Do not move the build to the production host.

The manual release number below is a UTC epoch timestamp, **not a GitHub run ID**. The numeric suffix makes the image compatible with the restricted import grammar; record its manual origin separately.

```bash
cd "$WORK/source"
export DOCKER_DEFAULT_PLATFORM=linux/amd64
MANUAL_RELEASE="$(date -u +%s)"
IMAGE="datool-release:${SHA}-${MANUAL_RELEASE}-1"
export DATOOL_DOCKER_TEST_IMAGE="$IMAGE"

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'dokku_*_test.py'
docker buildx build --platform linux/amd64 --load \
  --label "org.opencontainers.image.revision=$SHA" --tag "$IMAGE" .

docker run --rm --network none --read-only --tmpfs /tmp:exec \
  --mount "type=bind,source=$PWD/tests,target=/app/tests,readonly" \
  --mount "type=bind,source=$PWD/.github,target=/app/.github,readonly" \
  --entrypoint bun "$IMAGE" test \
  tests/release-command.test.ts tests/deployment-image-handoff.test.ts tests/cms-seed-options.test.ts

DATOOL_DOCKER_SKIP_BUILD=1 bash scripts/test-docker.sh

test "$(docker image inspect "$IMAGE" --format '{{.Os}}/{{.Architecture}}')" = linux/amd64
test "$(docker image inspect "$IMAGE" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "$SHA"
docker image save "$IMAGE" | gzip -1 > "$BUNDLE/image.tar.gz"
printf '%s\n' "$IMAGE" > "$BUNDLE/image-ref.txt"
docker image inspect "$IMAGE" --format '{{.Size}}' > "$BUNDLE/image-size.txt"
(
  cd "$BUNDLE"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum image.tar.gz image-ref.txt image-size.txt > image.sha256
  else
    shasum -a 256 image.tar.gz image-ref.txt image-size.txt > image.sha256
  fi
)
python3 "$SKILL_DIR/scripts/verify_artifact.py" "$BUNDLE" --commit "$SHA"
```

This mirrors the September 2026 workflow; add or adjust checks when the selected revision's workflow changes. `scripts/test-docker.sh` creates disposable Postgres/Redis services and tests migrations, ingestion and persistence. Never point it at production. A failed test blocks release of that candidate. Export once after tests; rebuilding afterward produces an unverified image.

## 3. Transfer and release

Choose one access route. Both use the installed `disk:load-image` wrapper. Check space before uploading a large bundle; the maintainer route additionally needs room for the compressed archive on disk. Neither route grants broader privileges.

### Maintainer access

Use the existing pinned host key. Migration-time Ed25519 fingerprint: `SHA256:sOjAXQTEoN41s+F+mCFOYTdVOi38PNkJ9+qvTaeqqt0`. Treat it as a baseline, not permission to accept a changed key; verify a change through the Netcup console or another trusted channel.

```bash
SSH_OPTS=(-o StrictHostKeyChecking=yes -o ConnectTimeout=15 \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=4)
if [[ "$(uname -s)" == Darwin ]]; then SSH_OPTS+=(-o UseKeychain=yes); fi
ssh "${SSH_OPTS[@]}" vinicius@62.83.32.238 'df -h /'
```

If root checks or a fresh backup are needed, establish the interactive session first. Root SSH is disabled and the maintainer has no general sudo access; use `su -` inside the maintainer session. Retrieve a current password through the authorized secure mechanism, never a literal stored in this skill, a process argument or a log.

Upload into a private, per-release directory:

```bash
STAGING=".datool-deploy/${SHA}-$(date -u +%s)"
ssh "${SSH_OPTS[@]}" vinicius@62.83.32.238 "umask 077; mkdir -p '$STAGING'"
scp "${SSH_OPTS[@]}" \
  "$BUNDLE/image.tar.gz" "$BUNDLE/image-ref.txt" \
  "$BUNDLE/image-size.txt" "$BUNDLE/image.sha256" \
  "$SKILL_DIR/scripts/verify_artifact.py" \
  "vinicius@62.83.32.238:$STAGING/"
ssh -t "${SSH_OPTS[@]}" vinicius@62.83.32.238
```

Inside that remote session, run `su -`. Use the inspected maintainer home path and exact staging directory; local variables are **not** carried into this shell. Set `EXPECTED_SHA` from the release decision, independently of uploaded metadata. If using CI, also pass the independently inspected `--run` to the verifier.

```bash
set -euo pipefail
# Replace these two values with the recorded staging path and full SHA.
cd /home/vinicius/.datool-deploy/RELEASE_DIRECTORY
EXPECTED_SHA=FULL_COMMIT_SHA
python3 verify_artifact.py . --commit "$EXPECTED_SHA" > verified-artifact.json
IMAGE="$(python3 -c 'import json; print(json.load(open("verified-artifact.json"))["image"])')"
IMAGE_BYTES="$(python3 -c 'import json; print(json.load(open("verified-artifact.json"))["image_bytes"])')"
dokku git:report datool --git-source-image
dokku disk:status datool
dokku disk:load-image datool "$IMAGE" "$IMAGE_BYTES" < image.tar.gz 2>&1 | tee deployment.log
dokku git:report datool --git-source-image
dokku ps:report datool
test "$(dokku ps:report datool --running)" = true
test "$(dokku git:report datool --git-source-image)" = "$IMAGE"
```

Retain the previous source-image reference before import and inspect release output. `--running` alone is insufficient: require both `Status web 1: running` and `Status worker 1: running` in the report. Keep logs private and redact credentials before sharing.

### Restricted deployment key, when available

Use an authorized key file and known-hosts file already available through the user's credential workflow. GitHub secrets cannot be downloaded as plaintext. The account does not allow an interactive shell, SCP, `git:report`, arbitrary logs or other apps. Do not attempt to give it those permissions to complete a routine deployment.

```bash
python3 "$SKILL_DIR/scripts/verify_artifact.py" "$BUNDLE" --commit "$SHA"
IMAGE="$(cat "$BUNDLE/image-ref.txt")"
IMAGE_BYTES="$(cat "$BUNDLE/image-size.txt")"
DEPLOY_SSH=(-i "$DEPLOY_KEY" -o IdentitiesOnly=yes \
  -o "UserKnownHostsFile=$KNOWN_HOSTS" -o StrictHostKeyChecking=yes \
  -o ConnectTimeout=15 -o ServerAliveInterval=15 -o ServerAliveCountMax=4)
ssh "${DEPLOY_SSH[@]}" datool-deploy@62.83.32.238 disk:status datool
ssh "${DEPLOY_SSH[@]}" datool-deploy@62.83.32.238 \
  disk:load-image datool "$IMAGE" "$IMAGE_BYTES" < "$BUNDLE/image.tar.gz"
ssh "${DEPLOY_SSH[@]}" datool-deploy@62.83.32.238 ps:report datool
ssh "${DEPLOY_SSH[@]}" datool-deploy@62.83.32.238 ps:report datool --running
```

For a CI artifact, include `--run "$RUN"` in validation. Check both process statuses and `true` from `--running`. Use the import output and maintainer access for independent source-image confirmation; state the limitation if such access is unavailable. Remove only temporary key copies created for this release, never an existing user key.

## 4. Verify the public service

```bash
DATOOL_URL=https://datool.vinipace.com
for path in / /faq /faq.md /cms/api/cms-users/me /sign-in /docs /llms.txt; do
  curl --fail --silent --show-error --connect-timeout 10 --max-time 30 \
    --retry 6 --retry-all-errors --retry-delay 5 \
    "$DATOOL_URL$path" --output /dev/null
done
```

These are smoke checks. Then use an authorized account and test project to verify sign-in and a representative authenticated screen. Submit a synthetic trace with a unique release marker through the current SDK/ingestion contract. Read the persisted trace back after normal worker processing; acceptance by the ingestion endpoint alone is insufficient. Prefer an existing canary project and approved credentials. Do not expose customer payloads or create a seeded production admin. Clean up only the synthetic records created for this check when supported, otherwise record their marker and location.

If access prevents authenticated or persistence checks, report the exact checks that passed and the gap. Do not claim full end-to-end success.

## 5. Failure, recovery and cleanup

- **Image metadata, provenance, platform, tests or authentication fails:** stop before import; correct the cause and revalidate. Never bypass host checks or deployment guards.
- **Disk preflight refuses import:** inspect `disk:status` and the current `ops/dokku-disk` procedure. Preserve current/previous successful images and data volumes. Do not use broad Docker pruning or delete containerd directories.
- **Import reports “No changes detected”:** the installed disk wrapper must use a unique temporary Git-context marker for each image import (`git:load-image --build-dir`). Compare it with the selected source and installed version. Repair the wrapper only within authorized scope; do not fall back to building application source on production.
- **Release or migration fails:** inspect retained release output, current source image, process status and logs through maintainer access. Determine whether the old app is still serving before retrying. Do not reset Postgres/Redis, auto-seed CMS or blindly retry failed migrations.
- **Rollback:** first assess schema compatibility and post-release writes. A previous image alone cannot reverse a database migration. If compatible and authorized, re-import the retained verified previous image through the same wrapper and recheck web, worker and persistence. A database restore needs a concrete recovery plan covering new writes. Repointing DNS to the retired host is not a routine rollback.
- **Cleanup:** after collecting results, remove only this run's staging directory, temporary credentials and detached worktree (`git -C "$APP_REPO" worktree remove "$WORK/source"`). Preserve the bundle until a verified retained image/recovery path exists. Leave unrelated images, files and repositories alone.

Final report: source SHA and image, evidence source (CI run URL or local test result), migration outcome, process and public checks, end-to-end evidence, previous release reference, and remaining issues. A successful release does not by itself establish off-server backup coverage or repair CI billing/configuration.
