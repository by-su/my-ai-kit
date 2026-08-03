# Security Policy

my-ai-kit modifies local AI agent configuration, MCP configuration, shell startup files, and skill symlinks. Treat all changes as local environment changes with security impact.

## What Bootstrap May Touch

Depending on selected flags, `./bootstrap.sh` may read or write:

- `~/.zshrc`
- `~/.bashrc`
- `~/.claude/CLAUDE.md`
- `~/.gemini/antigravity-cli/AGENTS.md`
- `~/.codex/instructions.md`
- `~/.codex/AGENTS.md`
- `~/.agent-skills/state.json`
- MCP config files for Claude, Gemini/Antigravity, and Codex

Use `./bootstrap.sh --dry-run` to inspect planned actions before applying them.

## Reporting a Vulnerability

Please open a private security advisory on GitHub if available. If not, open an issue with minimal reproduction details and avoid posting secrets, tokens, or private configuration.

## Secrets

Do not commit `.env` files, API keys, MCP tokens, or generated local state files. Use `.env.example` for documented variable names only.
