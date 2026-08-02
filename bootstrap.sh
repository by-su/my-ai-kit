#!/usr/bin/env bash
set -e

echo "🚀 Bootstrapping my-ai-kit environment..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MYKIT_BIN="$SCRIPT_DIR/bin/mykit"

chmod +x "$MYKIT_BIN"

# Automatically add PATH to ~/.zshrc or ~/.bashrc if not present
PATH_LINE="export PATH=\"$SCRIPT_DIR/bin:\$PATH\""

if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q "my-ai-kit/bin" "$HOME/.zshrc"; then
        echo "" >> "$HOME/.zshrc"
        echo "# my-ai-kit CLI PATH" >> "$HOME/.zshrc"
        echo "$PATH_LINE" >> "$HOME/.zshrc"
        echo "✓ Appended PATH to ~/.zshrc"
    fi
fi

if [ -f "$HOME/.bashrc" ]; then
    if ! grep -q "my-ai-kit/bin" "$HOME/.bashrc"; then
        echo "" >> "$HOME/.bashrc"
        echo "# my-ai-kit CLI PATH" >> "$HOME/.bashrc"
        echo "$PATH_LINE" >> "$HOME/.bashrc"
        echo "✓ Appended PATH to ~/.bashrc"
    fi
fi

# Deploy global AGENTS.md (Karpathy guidelines) across targets
echo "📋 Deploying global AGENTS.md (Karpathy guidelines)..."
mkdir -p ~/.claude
mkdir -p ~/.gemini/antigravity-cli
mkdir -p ~/.codex

cp "$SCRIPT_DIR/AGENTS.md" ~/.claude/CLAUDE.md
cp "$SCRIPT_DIR/AGENTS.md" ~/.gemini/antigravity-cli/AGENTS.md
cp "$SCRIPT_DIR/AGENTS.md" ~/.codex/instructions.md
cp "$SCRIPT_DIR/AGENTS.md" ~/.codex/AGENTS.md

echo "✓ Global Karpathy guidelines deployed to ~/.claude, ~/.gemini, ~/.codex"

# Run initial sync
"$MYKIT_BIN" sync

echo ""
echo "🎉 Setup complete! Run 'source ~/.zshrc' to use 'mykit' anywhere."
