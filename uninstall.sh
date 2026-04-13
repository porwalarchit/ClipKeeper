#!/usr/bin/env bash
# ClipKeeper v2 — Uninstaller
echo "[ClipKeeper] Stopping running instance..."
pkill -f clipkeeper.py 2>/dev/null || true

echo "[ClipKeeper] Removing installed files..."
rm -rf "$HOME/.local/share/clipkeeper"
rm -f  "$HOME/.local/bin/clipkeeper"
rm -f  "$HOME/.config/autostart/clipkeeper.desktop"
rm -f  "$HOME/.local/share/applications/clipkeeper.desktop"

echo ""
echo "[✓] ClipKeeper uninstalled. Venv and app files removed."
echo "    History preserved at: ~/.config/clipkeeper/history.json"
echo "    To also delete history: rm -rf ~/.config/clipkeeper"
