# Source Control

Status: active guidance, 2026-08-13

This repository is now the canonical source for the Finance bounded context.
The current baseline is committed on `main` and tracked in GitHub.

## Branching

- `main` is the integration branch.
- Use short-lived feature branches for all new work.
- Prefer branch names of the form `feature/<area>-<short-description>`.
- Keep experimental or spike work off `main` until it is ready to review.

## Commit Messages

- Use clear, imperative commit messages.
- Prefer `type(scope): summary` when it fits naturally.
- Keep each commit focused on one intent: one feature, one fix, or one doc
  update.

## Release Tags

The first release tag should be cut from a clean `main` after the repository is
ready for external consumption.

- Suggested initial tag: `v0.1.0`
- Tag only after the baseline is validated and ready to be referenced.
- Use later tags to mark stable milestones, not every merge.

## Coordination Rules

- Do not commit secrets, credentials, or environment-specific values.
- Keep runtime configuration in environment variables or deployment manifests.
- Document architecture or contract changes in `docs/` alongside code changes.
- Use pull requests or reviewed merges for changes that affect contracts,
  runtime wiring, or persistence.

