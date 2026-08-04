# Changelog

All notable changes to this project will be documented here.

This project uses Conventional Commits and may use GitHub Releases for published versions.

## Unreleased

### Added

- `pm-pdlc-conductor`: a new local skill (`skills/pm-pdlc-conductor/SKILL.md`, registered as a `source: "local"` optional pack in `manifest.yaml`) that guides the user acting as PM through the Triple Diamond product development lifecycle (Discover → Define → Develop → Deliver → Measure → Iterate). It auto-triggers on product/PM-shaped prompts, recommends and invokes the installed `pm-skills` pack at the right phase, tracks per-phase transition criteria in a local `_pm-pdlc/<initiative>/state.md`, and hands off multi-step execution to the existing `pm-workflow-orchestrator` agent rather than re-implementing it. Install/remove like any other skill: `mykit install pm-pdlc-conductor` / `mykit remove pm-pdlc-conductor`.
