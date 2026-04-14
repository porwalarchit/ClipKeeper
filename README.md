# ClipKeeper v2

A lightweight clipboard history manager for Linux desktops with a system tray interface. Keeps a searchable history of everything you copy — **text and images** — persists across reboots, and supports pinning important entries.

---

## Requirements

- **OS:** Linux (Ubuntu / Debian-based distros recommended)
- **Python 3.6+** (usually pre-installed)
- **python3-venv** module
- A desktop environment with system tray support (GNOME, KDE, XFCE, etc.)

> No `sudo` required. All dependencies install into a local virtual environment.

---

## Installation

1. **Clone or download** this repository:

   ```bash
   git clone https://github.com/porwalarchit/ClipKeeper.git
   cd ClipKeeper
   ```

2. **Run the installer:**

   ```bash
   ./install.sh
   ```

   The installer will:
   - Create a virtual environment at `~/.local/share/clipkeeper/venv`
   - Install PyQt5 inside the venv (system is untouched)
   - Create a `clipkeeper` launcher at `~/.local/bin/clipkeeper`
   - Add an autostart entry so ClipKeeper launches on every login
   - Start the daemon immediately

   > If `~/.local/bin` is not yet in your `PATH`, the installer will add it to your shell config (`.bashrc` / `.zshrc`). Restart your terminal or run `source ~/.bashrc` afterwards.

3. **Verify it's running** — you should see a clipboard icon in your system tray.

---

## Usage

| Command               | Description                             |
| --------------------- | --------------------------------------- |
| `clipkeeper`          | Open the clipboard history panel        |
| `clipkeeper --daemon` | Start ClipKeeper as a background daemon |

### Panel features

- **Text history** — every text copy is captured and shown with a preview, character count, and timestamp
- **Image history** — copied images are captured and shown as thumbnails with pixel dimensions; clicking the copy button restores the image to your clipboard
- **Search** — type in the search bar to filter text entries in real time (image entries are shown when the search bar is empty)
- **Copy** — click the copy button on any entry to copy it back to clipboard
- **Pin** — click the pin button to keep an entry at the top (max 10 pinned items); works for both text and images
- **Settings** — click the ⚙ button to adjust theme, font size, history limit, and panel width
- **Auto-hide** — the panel closes automatically when it loses focus

### Tray icon menu

Right-click the system tray icon for quick access to:

- Open / hide the panel
- Settings
- Quit

---

## Data & Configuration

| Path                                 | Description                                    |
| ------------------------------------ | ---------------------------------------------- |
| `~/.config/clipkeeper/history.json`  | Clipboard history (max 100 entries by default) |
| `~/.config/clipkeeper/images/`       | Copied images stored as PNG files              |
| `~/.config/clipkeeper/settings.json` | User settings (theme, font size, limits, etc.) |

History and images are preserved on uninstall. To delete everything:

```bash
rm -rf ~/.config/clipkeeper
```

---

## Keyboard Shortcut Setup

ClipKeeper does not bind a global hotkey automatically. Follow the steps for your desktop environment below.

### GNOME (Ubuntu default)

1. Open **Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts**
2. Click the **+** button to add a new shortcut
3. Fill in:
   - **Name:** `ClipKeeper`
   - **Command:** `clipkeeper`
   - **Shortcut:** press your desired key combo (e.g. `Super + V` or `Ctrl + Alt + V`)
4. Click **Add**

---

## Uninstall

```bash
./uninstall.sh
```

This removes the app, venv, launcher, and autostart entry. Your clipboard history at `~/.config/clipkeeper/history.json` is kept.

---

## Troubleshooting

**Panel doesn't appear / no tray icon**

- Make sure a system tray is available. On GNOME, install the [AppIndicator extension](https://extensions.gnome.org/extension/615/appindicator-support/).
- Check if the daemon is running: `pgrep -f clipkeeper.py`
- Start it manually: `clipkeeper --daemon`

**`clipkeeper` command not found after install**

- Restart your terminal, or run: `source ~/.bashrc`
- Check that `~/.local/bin` is in your PATH: `echo $PATH`

**PyQt5 installation fails**

- Make sure `python3-venv` is installed:
  ```bash
  sudo apt install python3-venv python3-dev
  ```

**Clipboard not capturing on Wayland**

- ClipKeeper uses X11 clipboard APIs. On Wayland sessions, run with XWayland compatibility or switch to an X11 session.
