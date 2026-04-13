#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  ClipKeeper v2 — Installer (NO sudo required)
#  Uses a local Python venv. All dependencies stay inside ~/.local/share/clipkeeper/venv
# ─────────────────────────────────────────────────────────────────────────────
set -e

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[ClipKeeper]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }

echo -e "\n${BOLD}  ╔══════════════════════════════╗"
echo -e "  ║   ClipKeeper v2  Installer  ║"
echo -e "  ║   (no sudo required)        ║"
echo -e "  ╚══════════════════════════════╝${NC}\n"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/clipkeeper"
VENV_DIR="$INSTALL_DIR/venv"
BIN_PATH="$HOME/.local/bin/clipkeeper"
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/clipkeeper.desktop"
APP_DESKTOP="$HOME/.local/share/applications/clipkeeper.desktop"

# ── 1. Python 3 check ─────────────────────────────────────────────────────────
info "Checking Python 3..."
python3 --version &>/dev/null || { echo "Python 3 not found!"; exit 1; }
success "$(python3 --version)"

# ── 2. venv module check ──────────────────────────────────────────────────────
info "Checking venv module..."
python3 -m venv --help &>/dev/null || {
    warn "venv module not found. Trying to install without sudo..."
    # venv is built-in from Python 3.3+; if missing, it's a distro packaging issue
    echo "Please run: sudo apt install python3-venv"
    exit 1
}
success "venv module OK"

# ── 3. Create install dir + copy files ────────────────────────────────────────
info "Setting up install directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/clipkeeper.py"   "$INSTALL_DIR/clipkeeper.py"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt"
chmod +x "$INSTALL_DIR/clipkeeper.py"
success "Files copied."

# ── 4. Create venv ────────────────────────────────────────────────────────────
info "Creating Python virtual environment at $VENV_DIR ..."
python3 -m venv "$VENV_DIR"
success "venv created."

# ── 5. Install dependencies into venv ─────────────────────────────────────────
info "Installing dependencies (PyQt5) into venv — this may take 1-2 minutes..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --quiet
success "Dependencies installed inside venv (system is untouched)."

# ── 6. Create launcher script ─────────────────────────────────────────────────
mkdir -p "$HOME/.local/bin"
cat > "$BIN_PATH" << LAUNCHER
#!/usr/bin/env bash
# ClipKeeper launcher — uses local venv
exec "$VENV_DIR/bin/python" "$INSTALL_DIR/clipkeeper.py" "\$@"
LAUNCHER
# Expand variables now (don't use single quotes for the heredoc)
# Rewrite with actual expanded paths:
cat > "$BIN_PATH" << EOF
#!/usr/bin/env bash
exec "${VENV_DIR}/bin/python" "${INSTALL_DIR}/clipkeeper.py" "\$@"
EOF
chmod +x "$BIN_PATH"
success "Launcher created: $BIN_PATH"

# ── 7. Add ~/.local/bin to PATH if needed ─────────────────────────────────────
for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [[ -f "$rc" ]] && ! grep -q '\.local/bin' "$rc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
        info "Added ~/.local/bin to PATH in $rc"
    fi
done

# ── 8. Autostart + desktop entry ──────────────────────────────────────────────
mkdir -p "$AUTOSTART_DIR" "$(dirname "$APP_DESKTOP")"

DESKTOP_CONTENT="[Desktop Entry]
Type=Application
Name=ClipKeeper
Comment=Clipboard History Manager
Exec=${BIN_PATH} --daemon
Icon=edit-paste
Terminal=false
Categories=Utility;
Keywords=clipboard;copy;paste;history;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"
echo "$DESKTOP_CONTENT" > "$AUTOSTART_FILE"
echo "$DESKTOP_CONTENT" > "$APP_DESKTOP"
success "Autostart enabled — ClipKeeper will launch on every login."

# ── 9. Kill existing instance, launch fresh ───────────────────────────────────
pkill -f clipkeeper.py 2>/dev/null || true
sleep 0.3

info "Launching ClipKeeper..."
nohup "$BIN_PATH" --daemon &>/dev/null &
disown

echo ""
echo -e "${GREEN}${BOLD}  ✓  ClipKeeper v2 installed and running!${NC}"
echo ""
echo -e "  ${CYAN}Location:${NC}   $INSTALL_DIR"
echo -e "  ${CYAN}Venv:${NC}       $VENV_DIR"
echo -e "  ${CYAN}History:${NC}    ~/.config/clipkeeper/history.json"
echo -e "  ${CYAN}Autostart:${NC}  enabled"
echo ""
echo -e "  ${CYAN}Commands:${NC}"
echo -e "    Open Panel:  ${BOLD}clipkeeper${NC}"
echo -e "    Run Daemon:  ${BOLD}clipkeeper --daemon${NC}"
echo -e "    Uninstall:   ${BOLD}./uninstall.sh${NC}"
echo ""
echo -e "  ${YELLOW}Tip:${NC} Set a keyboard shortcut in"
echo -e "       Settings → Keyboard → Custom Shortcuts"
echo -e "       Command: ${BOLD}${BIN_PATH}${NC}"
echo ""
