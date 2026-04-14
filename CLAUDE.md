# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ClipKeeper v2 is a Linux desktop clipboard history manager with a system tray interface, built with Python 3 and PyQt5.

## Commands

**Install (sets up venv at `~/.local/share/clipkeeper/venv`):**
```bash
./install.sh
```

**Run:**
```bash
clipkeeper          # open UI panel
clipkeeper --daemon # run as background daemon
```

**Uninstall:**
```bash
./uninstall.sh
```

There is no test suite.

## Architecture

The entire application lives in a single file: [clipkeeper.py](clipkeeper.py) (~900 lines). This is intentional — single-file layout simplifies installation and portability.

### Main classes

**`ClipboardManager`** (line ~640) — Core controller. Owns the clipboard monitoring loop (event signal + 800ms polling fallback for X11 selection clipboard), JSON persistence, system tray setup, and creates the window on demand. Handles both text and image ingestion.

**`ClipboardWindow`** (line ~410) — `QMainWindow` subclass. Frameless window that auto-hides on focus loss. Manages search/filtering, the pinned section, and the scrollable history list. Calls `refresh()` to rebuild the list whenever history changes.

**`RowWidget`** (line ~289) — Custom `QWidget` for a single clipboard entry. For text entries: pin button, text preview (180 chars, multiline escaping), meta info (timestamp/char/line count), copy button. For image entries: pin button, scaled thumbnail (160×44), meta info (timestamp/dimensions), copy button. Emits `copy_requested` and `pin_requested` signals.

### Data flow

```
X11 clipboard change
    → ClipboardManager._on_clipboard_change()
        → image on clipboard?
            → _ingest_image(pixmap)
                → MD5 hash for dedup + guard check
                → PNG saved to ~/.config/clipkeeper/images/
                → history.json updated
                → ClipboardWindow.refresh() called
        → text on clipboard?
            → _ingest(text)
                → deduplication + guard check
                → history.json updated
                → ClipboardWindow.refresh() called
                    → RowWidget instances rebuilt
```

### Key design details

- **Capture guard:** After the user copies an entry, a 0.6s guard prevents the app from immediately re-ingesting what it just wrote to clipboard. Text uses `_capture_guard_text`; images use `_capture_guard_image_hash`.
- **Image storage:** Copied images are saved as PNG files in `~/.config/clipkeeper/images/`. The filename encodes a timestamp and MD5 hash. Entries whose file is missing are silently dropped on load. "Clear All" deletes the PNG files too.
- **Image deduplication:** Images are deduplicated by MD5 hash of their PNG bytes, so copying the same image twice produces only one history entry.
- **Pinning:** Max 10 pinned items; pinned entries have a `pinned_at` timestamp and are sorted reverse-chronologically in their own section. Works for both text and image entries.
- **Search:** Filters text entries in real time. Image entries are shown when the search bar is empty and hidden when a query is active (no text to match against).
- **Icons are procedurally generated** (no external image assets) — see `make_tray_icon()`, `make_pin_button_icon()`, `make_copy_button_icon()` around line 224.
- **Stylesheet** at the top of the file (~line 35) defines the entire dark blue theme (`#0d0f18` background, `#6b8cff` accent).

### History entry schema

**Text entry:**
```json
{
  "text": "...",
  "timestamp": "2026-04-13T17:00:00.123456",
  "pinned": false,
  "pinned_at": null
}
```

**Image entry:**
```json
{
  "type": "image",
  "image_file": "img_20260414_170000_123456_abcdef01234567.png",
  "image_hash": "abcdef01234567",
  "timestamp": "2026-04-14T17:00:00.123456",
  "pinned": false,
  "pinned_at": null,
  "width": 1920,
  "height": 1080
}
```

`history.json` stored at `~/.config/clipkeeper/history.json`. Max 100 entries.
Image PNGs stored at `~/.config/clipkeeper/images/`.
