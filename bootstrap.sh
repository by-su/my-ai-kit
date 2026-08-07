#!/usr/bin/env bash
set -e

DRY_RUN=0
NON_INTERACTIVE=0
SETUP_PATH=1
SETUP_AGENT_INSTRUCTIONS=1

for arg in "$@"; do
    case "$arg" in
        --dry-run)
            DRY_RUN=1
            ;;
        --non-interactive)
            NON_INTERACTIVE=1
            ;;
        --no-path)
            SETUP_PATH=0
            ;;
        --no-agent-instructions)
            SETUP_AGENT_INSTRUCTIONS=0
            ;;
        -h|--help)
            echo "Usage: ./bootstrap.sh [--dry-run] [--non-interactive] [--no-path] [--no-agent-instructions]"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Usage: ./bootstrap.sh [--dry-run] [--non-interactive] [--no-path] [--no-agent-instructions]"
            exit 1
            ;;
    esac
done

run_cmd() {
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "[dry-run] $*"
    else
        "$@"
    fi
}

append_line() {
    target="$1"
    line="$2"
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "[dry-run] append to $target: $line"
    else
        echo "$line" >> "$target"
    fi
}

echo "🚀 Bootstrapping my-ai-kit environment..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MYKIT_BIN="$SCRIPT_DIR/bin/mykit"

run_cmd chmod +x "$MYKIT_BIN"

# Automatically add PATH to ~/.zshrc or ~/.bashrc if not present
PATH_LINE="export PATH=\"$SCRIPT_DIR/bin:\$PATH\""

if [ "$SETUP_PATH" -eq 1 ]; then
    [ -f "$HOME/.zshrc" ] || run_cmd touch "$HOME/.zshrc"
    if ! grep -q "my-ai-kit/bin" "$HOME/.zshrc"; then
        append_line "$HOME/.zshrc" ""
        append_line "$HOME/.zshrc" "# my-ai-kit CLI PATH"
        append_line "$HOME/.zshrc" "$PATH_LINE"
        echo "✓ Appended PATH to ~/.zshrc"
    fi
fi

if [ "$SETUP_PATH" -eq 1 ] && [ -f "$HOME/.bashrc" ]; then
    if ! grep -q "my-ai-kit/bin" "$HOME/.bashrc"; then
        append_line "$HOME/.bashrc" ""
        append_line "$HOME/.bashrc" "# my-ai-kit CLI PATH"
        append_line "$HOME/.bashrc" "$PATH_LINE"
        echo "✓ Appended PATH to ~/.bashrc"
    fi
fi

# Run initial setup when attached to a terminal; keep automation non-interactive.
if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] $MYKIT_BIN setup|sync"
elif [ "$NON_INTERACTIVE" -eq 0 ] && [ -t 0 ]; then
    "$MYKIT_BIN" setup
else
    "$MYKIT_BIN" sync
fi

# Deploy after setup/sync so isolated profiles receive the instructions inside
# their active runtime roots.
if [ "$SETUP_AGENT_INSTRUCTIONS" -eq 1 ]; then
    echo "📋 Deploying global AGENTS.md (Karpathy guidelines)..."
    run_cmd mkdir -p "$HOME/.claude"
    run_cmd mkdir -p "$HOME/.gemini/antigravity-cli"
    run_cmd mkdir -p "$HOME/.codex"
    run_cmd cp "$SCRIPT_DIR/AGENTS.md" "$HOME/.claude/CLAUDE.md"
    run_cmd cp "$SCRIPT_DIR/AGENTS.md" "$HOME/.gemini/antigravity-cli/AGENTS.md"
    run_cmd cp "$SCRIPT_DIR/AGENTS.md" "$HOME/.codex/instructions.md"
    run_cmd cp "$SCRIPT_DIR/AGENTS.md" "$HOME/.codex/AGENTS.md"
    echo "✓ Global Karpathy guidelines deployed to active profile runtime"

    # Re-apply the preferred summary language now that the instruction files above
    # exist (mykit setup|sync ran earlier, before these files were deployed).
    run_cmd "$MYKIT_BIN" language sync
fi

echo ""
echo "🎉 Setup complete! Run 'source ~/.zshrc' to use 'mykit' anywhere."
