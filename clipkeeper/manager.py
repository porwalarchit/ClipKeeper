import sys
import os
import json
import time
import hashlib
from datetime import datetime

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from PyQt5.QtCore import (
    Qt, QTimer, QObject, QRect, QPoint, QSize, QByteArray, QBuffer, QIODevice,
)
from PyQt5.QtGui import QPixmap, QCursor

from .constants import CONFIG_DIR, HISTORY_FILE, IMAGES_DIR
from .settings import settings
from .stylesheet import build_stylesheet
from .icons import make_tray_icon
from .window import ClipboardWindow
from .dialogs import ConfirmDialog, SettingsDialog


class ClipboardManager(QObject):
    def __init__(self, app: QApplication, daemon_mode=False):
        super().__init__()
        self.app         = app
        self.daemon_mode = daemon_mode
        self.history     = self._load()
        self.last_text   = None
        self.window      = None
        self.quitting    = False
        self._capture_guard_text       = None
        self._capture_guard_image_hash = None
        self._capture_guard_until      = 0.0
        self._last_image_hash          = None

        os.makedirs(CONFIG_DIR, exist_ok=True)
        self._clipboard = app.clipboard()

        if self.daemon_mode:
            self._clipboard.dataChanged.connect(self._on_clipboard_change)
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._poll)
            self._timer.start(800)
            self._setup_tray()

        self.show_window()

    # ── Persistence ───────────────────────────────────────────────────────────
    def _load(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    history = []
                    for entry in raw:
                        if not isinstance(entry, dict):
                            continue
                        if entry.get('type') == 'image':
                            img_path = os.path.join(IMAGES_DIR, entry.get('image_file', ''))
                            if not os.path.exists(img_path):
                                continue
                            history.append({
                                'type':       'image',
                                'image_file': entry['image_file'],
                                'image_hash': entry.get('image_hash', ''),
                                'timestamp':  entry.get('timestamp', datetime.now().isoformat()),
                                'pinned':     bool(entry.get('pinned', False)),
                                'pinned_at':  entry.get('pinned_at'),
                                'width':      entry.get('width', 0),
                                'height':     entry.get('height', 0),
                            })
                        else:
                            if not entry.get('text'):
                                continue
                            history.append({
                                'text':      entry['text'],
                                'timestamp': entry.get('timestamp', datetime.now().isoformat()),
                                'pinned':    bool(entry.get('pinned', False)),
                                'pinned_at': entry.get('pinned_at'),
                            })
                    return history[:settings.max_items]
        except Exception:
            pass
        return []

    def _save(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'[ClipKeeper] save error: {e}', file=sys.stderr)

    # ── Clipboard capture ─────────────────────────────────────────────────────
    def _on_clipboard_change(self):
        img = self._clipboard.image()
        if not img.isNull():
            self._ingest_image(QPixmap.fromImage(img))
            return
        self._ingest(self._clipboard.text())

    def _poll(self):
        img = self._clipboard.image()
        if not img.isNull():
            self._ingest_image(QPixmap.fromImage(img))
            return
        self._ingest(self._clipboard.text())

    def _ingest(self, text):
        if not text or not text.strip():
            return
        if (
            self._capture_guard_text == text
            and time.monotonic() < self._capture_guard_until
        ):
            return
        if text == self.last_text:
            return
        self.last_text = text
        existing  = next((h for h in self.history if h.get('text') == text), None)
        pinned    = bool(existing and existing.get('pinned'))
        pinned_at = existing.get('pinned_at') if existing else None
        self.history = [h for h in self.history if h.get('text') != text]
        self.history.insert(0, {
            'text':      text,
            'timestamp': datetime.now().isoformat(),
            'pinned':    pinned,
            'pinned_at': pinned_at,
        })
        dropped = self.history[settings.max_items:]
        self.history = self.history[:settings.max_items]
        for entry in dropped:
            if entry.get('type') == 'image' and entry.get('image_file'):
                try:
                    os.remove(os.path.join(IMAGES_DIR, entry['image_file']))
                except OSError:
                    pass
        self._save()
        if self.window and self.window.isVisible():
            self.window.refresh()

    def suspend_capture(self, text, duration=0.6):
        self._capture_guard_text  = text
        self._capture_guard_until = time.monotonic() + duration

    def suspend_capture_image(self, img_hash, duration=0.6):
        self._capture_guard_image_hash = img_hash
        self._capture_guard_until      = time.monotonic() + duration

    def _ingest_image(self, pixmap):
        if pixmap.isNull():
            return
        ba  = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.WriteOnly)
        pixmap.save(buf, 'PNG')
        buf.close()
        img_hash = hashlib.md5(bytes(ba)).hexdigest()[:16]

        if self._last_image_hash == img_hash:
            return
        if (
            self._capture_guard_image_hash == img_hash
            and time.monotonic() < self._capture_guard_until
        ):
            return

        self._last_image_hash = img_hash

        os.makedirs(IMAGES_DIR, exist_ok=True)
        ts_str   = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:21]
        filename = f'img_{ts_str}_{img_hash}.png'
        pixmap.save(os.path.join(IMAGES_DIR, filename), 'PNG')

        self.history = [
            h for h in self.history
            if not (h.get('type') == 'image' and h.get('image_hash') == img_hash)
        ]
        self.history.insert(0, {
            'type':       'image',
            'image_file': filename,
            'image_hash': img_hash,
            'timestamp':  datetime.now().isoformat(),
            'pinned':     False,
            'pinned_at':  None,
            'width':      pixmap.width(),
            'height':     pixmap.height(),
        })
        dropped = self.history[settings.max_items:]
        self.history = self.history[:settings.max_items]
        for entry in dropped:
            if entry.get('type') == 'image' and entry.get('image_file'):
                try:
                    os.remove(os.path.join(IMAGES_DIR, entry['image_file']))
                except OSError:
                    pass
        self._save()
        if self.window and self.window.isVisible():
            self.window.refresh()

    def pinned_entries(self):
        return sorted(
            [e for e in self.history if e.get('pinned')],
            key=lambda e: e.get('pinned_at') or e.get('timestamp') or '',
            reverse=True,
        )[:settings.max_pinned]

    def filtered_pinned_entries(self, query):
        entries = self.pinned_entries()
        if not query:
            return entries
        return [e for e in entries
                if e.get('type') != 'image' and query in e.get('text', '').lower()]

    def filtered_history_entries(self, query):
        entries = [e for e in self.history if not e.get('pinned')]
        if not query:
            return entries
        return [e for e in entries
                if e.get('type') != 'image' and query in e.get('text', '').lower()]

    def toggle_pin(self, entry):
        if entry.get('type') == 'image':
            target = next(
                (item for item in self.history
                 if item.get('type') == 'image'
                 and item.get('image_hash') == entry.get('image_hash')),
                None,
            )
        else:
            target = next(
                (item for item in self.history if item.get('text') == entry.get('text')),
                None,
            )
        if target is None:
            return False, 'Entry not found'
        if target.get('pinned'):
            target['pinned']    = False
            target['pinned_at'] = None
            self._save()
            return False, 'Unpinned item'
        if len(self.pinned_entries()) >= settings.max_pinned:
            return False, f'Pinned list full ({settings.max_pinned} max)'
        target['pinned']    = True
        target['pinned_at'] = datetime.now().isoformat()
        self._save()
        return True, 'Pinned item to top section'

    # ── Tray ──────────────────────────────────────────────────────────────────
    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print('[ClipKeeper] No system tray — use the window directly.', file=sys.stderr)
            return
        self.tray = QSystemTrayIcon(make_tray_icon(), self)
        self.tray.setToolTip('ClipKeeper — Clipboard History')
        self.tray.activated.connect(self._handle_tray_activation)
        self.tray.show()

    def _handle_tray_activation(self, reason):
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
            QSystemTrayIcon.Unknown,
        ):
            self.show_window()

    def show_window(self):
        qss = build_stylesheet(settings.theme, settings.font_size)
        if self.window is None:
            self.window = ClipboardWindow(self)
            self.window.setStyleSheet(qss)
        self.reload_history()
        self._position_window()
        self.window._hide_guard_until = time.monotonic() + 0.8
        self.window.setWindowState(Qt.WindowNoState)
        self.window.show()
        self.window.refresh()
        self.window.raise_()
        self.window.activateWindow()
        self.window.setFocus()
        QTimer.singleShot(50, self.window._search.setFocus)

    def _position_window(self):
        if not self.window:
            return
        anchor    = self._tray_anchor_rect()
        screen    = QApplication.screenAt(anchor.center()) or QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        width  = max(300, int(available.width()  * settings.panel_width  / 100))
        height = max(300, int(available.height() * settings.panel_height / 100))
        x = available.right() - width + 1
        y = available.top()
        self.window.setMinimumSize(0, 0)
        self.window.setMaximumSize(16777215, 16777215)
        self.window.resize(width, height)
        self.window.setFixedSize(width, height)
        self.window.move(x, y)

    def _tray_anchor_rect(self):
        if hasattr(self, 'tray'):
            geometry = self.tray.geometry()
            if geometry and not geometry.isNull():
                return geometry
        pos = QCursor.pos()
        return QRect(pos - QPoint(1, 1), QSize(2, 2))

    # ── Settings ──────────────────────────────────────────────────────────────
    def open_settings(self):
        if self.window:
            self.window._modal_open = True
        dlg = SettingsDialog(self, parent=self.window)
        dlg.exec_()
        if self.window:
            self.window._modal_open = False
            self.window._hide_guard_until = time.monotonic() + 0.5

    # ── Actions ───────────────────────────────────────────────────────────────
    def confirm_clear(self):
        if self.window:
            self.window._modal_open = True
        dlg = ConfirmDialog(
            '[ CLEAR ALL ]',
            'Clear all clipboard history?\nThis cannot be undone.',
            parent=self.window,
        )
        dlg.exec_()
        if self.window:
            self.window._modal_open = False
            self.window._hide_guard_until = time.monotonic() + 0.5
        if dlg._accepted:
            self._delete_all_image_files()
            self.history = []
            self._save()
            if self.window:
                self.window.refresh()

    def _delete_all_image_files(self):
        """Remove every PNG in IMAGES_DIR that belongs to the current history."""
        for entry in self.history:
            if entry.get('type') == 'image' and entry.get('image_file'):
                path = os.path.join(IMAGES_DIR, entry['image_file'])
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass

    def quit_app(self):
        self.quitting = True
        if hasattr(self, 'tray'):
            self.tray.hide()
        if self.window:
            self.window.close()
        self.app.quit()

    def reload_history(self):
        self.history = self._load()


def main():
    daemon_mode = '--daemon' in sys.argv[1:]
    QApplication.setQuitOnLastWindowClosed(False)

    app = QApplication(sys.argv)
    app.setApplicationName('ClipKeeper')
    app.setStyleSheet(build_stylesheet(settings.theme, settings.font_size))

    manager = ClipboardManager(app, daemon_mode=daemon_mode)
    sys.exit(app.exec_())
