# Changelog

All notable changes to this project will be documented here.

This project uses Conventional Commits and may use GitHub Releases for published versions.

## Unreleased

### Added

- `pm-pdlc-conductor`: a new local skill (`skills/pm-pdlc-conductor/SKILL.md`, registered as a `source: "local"` optional pack in `manifest.yaml`) that guides the user acting as PM through the Triple Diamond product development lifecycle (Discover → Define → Develop → Deliver → Measure → Iterate). It auto-triggers on product/PM-shaped prompts, recommends and invokes the installed `pm-skills` pack at the right phase, tracks per-phase transition criteria in a local `_pm-pdlc/<initiative>/state.md`, and hands off multi-step execution to the existing `pm-workflow-orchestrator` agent rather than re-implementing it. Install/remove like any other skill: `mykit install pm-pdlc-conductor` / `mykit remove pm-pdlc-conductor`.
- Profiles can now auto-enable optional skills: a profile (template in `manifest.yaml`'s `profiles:` or a custom profile saved via `mykit profile edit`/`setup`) may declare `enable_optionals: [<skill-name>, ...]`. Running `mykit profile use <name>` now globally enables those optional skills as part of the switch (`enable_optionals_for_profile()` in `bin/mykit`), instead of profile selection only affecting the `ecc-suite`/`mengto-skills` keyword pruning as before. Added a `pm` template profile (`include: [planning, product, research]`, `enable_optionals: [pm-skills, pm-pdlc-conductor]`) so `mykit profile use pm` turns both on globally in one step. `mykit profile list` now shows a profile's `Auto-enable` skills alongside its `Stacks` line.
- `mykit setup`/`mykit profile edit` now has a dedicated wizard step ("Auto-enable these skills whenever this profile is selected") to pick a profile's `enable_optionals` interactively, instead of requiring a manual `manifest.yaml`/`state.json` edit.

### Fixed

- `mykit completion install`'s zsh/bash tab-completion for `install`/`remove`/`prefetch` listed a stale, partially hand-maintained set of optional skill names (including a `db-helper` entry that no longer exists in `manifest.yaml`, and missing several real packs like `posthog`, `coolify`, `pm-skills`). `src/completion.py` now derives this list from `manifest.yaml`'s `optional:` entries at generation time (`get_optional_skill_names()`), and the checked-in `completions/_mykit` / `completions/mykit.bash` have been regenerated to match.
