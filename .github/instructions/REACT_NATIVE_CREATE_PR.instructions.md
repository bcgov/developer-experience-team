---
description: "Use when: preparing a pull request for a React Native upgrade after user testing and approval, reviewing upgrade evidence, or publishing approved upgrade changes."
applyTo: "DevExMobileTestApp/**"
---

# React Native Upgrade - Create Pull Request

Use after the [full upgrade workflow](REACT_NATIVE_UPGRADE.instructions.md).
This phase reviews and publishes approved work; it does not assume changes are
already staged, committed, or fully validated.

## Confirm readiness and scope

- Obtain explicit user approval after their iOS and Android testing and diff
  review. If native builds or runtime checks remain unverified, explain the
  blockers and ask whether to proceed with a draft instead of claiming readiness.
- Inspect the current branch, status, staged/unstaged diffs, and existing commits.
  Confirm the intended head and base branches; do not assume branch names.
- Review the complete upgrade diff against the chosen base's merge-base. Include
  related native migrations, toolchain declarations, lockfiles, documentation,
  and [mobile CI changes](../workflows/build-mobile-app.yaml), not just npm packages.
- Preserve unrelated edits and staging. Exclude secrets, machine-specific paths,
  generated reports, and build caches. Never stash, revert, or stage everything
  merely to obtain a clean tree.

## Review validation evidence

- Use actual results from the upgrade and subsequent testing. Rerun affected
  checks if later changes invalidate that evidence.
- Distinguish TypeScript/lint/Jest, native unit tests, native builds, launch,
  cold-start/UI interaction, and relevant release builds. Report test counts
  where available; `NO-SOURCE` does not mean tests passed.
- For CI changes, check runtime/toolchain alignment, dependency installation,
  workflow validation, and preserved signing/upload behavior. Local commands
  and static checks are not proof of hosted CI success.
- Record each relevant check as passed, failed, blocked, or not run. Disclose
  remaining upstream warnings, compatibility constraints, and environment limits.
  Do not pre-fill successful checklists or claim no regressions without evidence.

## Prepare commits and PR description

- If approved upgrade changes are uncommitted, ask the user to commit them or
  explicitly authorize scoped staging and commits. Do not silently omit pending
  upgrade work from the PR; unrelated uncommitted work need not block publication.
- Keep commits reviewable and follow repository conventions. Do not amend,
  squash, rebase, or force-push without explicit permission.
- Derive the title and description from the actual diff and validation evidence.
  Include only applicable sections:
  - Summary and actual before/after dependency and toolchain versions.
  - Native source/configuration migrations and reasons for compatibility choices.
  - Local/CI alignment, setup requirements, and documentation changes.
  - Testing evidence, platform/device coverage, and build artifacts.
  - Remaining warnings, blockers, behavior changes, and checks not performed.
- Do not invent changed dependencies, automatic native migrations, requirements,
  or successful results. Keep temporary PR-body files outside the repository.

## Publish approved work

- Confirm permission to push the intended branch and create the PR. Prefer
  GitHub CLI; check for an existing PR before opening a duplicate.
- Use the confirmed head/base, an evidence-based description, and draft status
  when agreed. Apply only relevant existing labels.
- If conflicts or remote divergence block publication, report the issue and
  agree on a resolution rather than automatically rewriting history.
- Verify the PR's URL, head/base, and included changes. Report hosted checks as
  observed, pending, or not run; opening the PR does not establish merge readiness.

## References

- [GitHub CLI PR creation](https://cli.github.com/manual/gh_pr_create)
- [GitHub pull requests](https://docs.github.com/en/pull-requests)
