#!/usr/bin/env bash
set -e

echo "🚀 Bootstrapping my-ai-kit environment..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MYKIT_BIN="$SCRIPT_DIR/bin/mykit"

chmod +x "$MYKIT_BIN"

# Synchronize all core & optional skills to AI tool adapters
"$MYKIT_BIN" sync

echo ""
echo "✅ Setup complete! Add the following line to your ~/.zshrc or ~/.bashrc:"
echo "export PATH=\"$SCRIPT_DIR/bin:\$PATH\""
