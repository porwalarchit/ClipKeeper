#!/usr/bin/env python3
"""
ClipKeeper v2 — Clipboard History Manager for Ubuntu
Built with PyQt5 (pip-installable, no sudo needed).
Stores clipboard items, persists across reboots.
"""

import sys
import json
import os
import time
import hashlib
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSystemTrayIcon, QAbstractItemView,
    QDialog, QSpinBox, QFrame,
)
from PyQt5.QtCore import (
    Qt, QTimer, QSize, pyqtSignal, QObject, QRect, QPoint, QEvent,
    QByteArray, QBuffer, QIODevice,
)
from PyQt5.QtGui import (
    QIcon, QColor, QPixmap, QPainter, QBrush, QCursor, QPen, QPainterPath
)

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_DIR    = os.path.expanduser('~/.config/clipkeeper')
HISTORY_FILE  = os.path.join(CONFIG_DIR, 'history.json')
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'settings.json')
IMAGES_DIR    = os.path.join(CONFIG_DIR, 'images')
ROW_HEIGHT       = 64
ACTION_BTN_WIDTH = 32


# ── Settings ──────────────────────────────────────────────────────────────────
class Settings:
    DEFAULTS = {
        'theme':         'dark',
        'font_size':     10,
        'max_items':     100,
        'max_pinned':    10,
        'panel_width':   35,   # percent of screen width  (25–60)
        'panel_height':  70,   # percent of screen height (50–100)
        'show_metadata': False,
        'word_wrap':     False,
    }

    def __init__(self):
        self._data = dict(self.DEFAULTS)
        self._load()

    # Valid ranges for numeric settings (used to clamp loaded values)
    _RANGES = {
        'panel_width':  (25, 60),
        'panel_height': (50, 100),
        'font_size':    (8, 24),
        'max_items':    (10, 1000),
        'max_pinned':   (1, 50),
    }

    def _load(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if k in self.DEFAULTS:
                            default = self.DEFAULTS[k]
                            if isinstance(default, bool):
                                self._data[k] = bool(v)
                            else:
                                coerced = type(default)(v)
                                if k in self._RANGES:
                                    lo, hi = self._RANGES[k]
                                    coerced = max(lo, min(hi, coerced))
                                self._data[k] = coerced
        except Exception:
            pass

    def save(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f'[ClipKeeper] settings save error: {e}', file=sys.stderr)

    @property
    def theme(self):         return self._data['theme']
    @property
    def font_size(self):     return self._data['font_size']
    @property
    def max_items(self):     return self._data['max_items']
    @property
    def max_pinned(self):    return self._data['max_pinned']
    @property
    def panel_width(self):   return self._data['panel_width']
    @property
    def panel_height(self):  return self._data['panel_height']
    @property
    def show_metadata(self): return self._data['show_metadata']
    @property
    def word_wrap(self):     return self._data['word_wrap']

    def apply(self, **kwargs):
        """Update one or more settings and persist."""
        for k, v in kwargs.items():
            if k in self.DEFAULTS:
                default = self.DEFAULTS[k]
                self._data[k] = bool(v) if isinstance(default, bool) else type(default)(v)
        self.save()


settings = Settings()


# ── Stylesheet ────────────────────────────────────────────────────────────────
def build_stylesheet(theme: str, font_size: int) -> str:
    """Return a complete QSS string for the given theme and preview font size."""
    if theme == 'light':
        c = {
            # Warm parchment base — comfortable, non-glaring
            'bg':            '#f5f0eb',
            'surface':       '#ede7e0',
            'surface2':      '#f0ebe4',
            'border':        '#d6cec5',
            'border2':       '#ddd8d0',
            'accent':        '#4169e1',
            'accent_hover':  '#2952cc',
            'text':          '#1a1a1a',
            'text_dim':      '#9b9188',
            'text_muted':    '#b8b0a7',
            'meta':          '#a09890',
            'select_bg':     '#d8e1fc',
            'copy_btn_bg':   '#ede7e0',
            'copy_btn_bdr':  '#c8c0b5',
            'pin_gold':      '#9a6e0a',
            'pin_gold_lit':  '#c08815',
            'pin_bg':        '#f7eddc',
            'pin_bdr':       '#e0d0a0',
            'pin_bg_act':    '#f0e0b5',
            'clear_color':   '#c0392b',
            'clear_bdr':     '#e8c5c0',
            'clear_bg_hv':   '#f8e8e6',
            'quit_color':    '#706860',
            'quit_bdr':      '#c8c0b5',
            'quit_bg_hv':    '#ede7e0',
            'status_bg':     '#ede7e0',
            'status_color':  '#9b9188',
            'status_bdr':    '#d6cec5',
            'scroll_bg':     '#ede7e0',
            'scroll_handle': '#c0b8ad',
            'scroll_hover':  '#4169e1',
            'pinned_bg':     '#eee8e0',
            'section_title': '#8a5c08',
            'section_meta':  '#9b9188',
            'idx_color':     '#c8c0b5',
            'dialog_bg':     '#f5f0eb',
            'spin_bg':       '#f0ebe4',
            'spin_bdr':      '#c8c0b5',
            'spin_up_bg':    '#e5dfd8',
            'sep_color':     '#d6cec5',
            'theme_btn_bg':  '#ede7e0',
            'theme_btn_clr': '#706860',
            'settings_lbl':  '#1a1a1a',
        }
    else:  # dark
        c = {
            # Near-black base — high contrast, industry standard
            'bg':            '#111111',
            'surface':       '#1a1a1a',
            'surface2':      '#222222',
            'border':        '#2d2d2d',
            'border2':       '#1a1a1a',
            'accent':        '#60a5fa',
            'accent_hover':  '#93c5fd',
            'text':          '#e5e5e5',
            'text_dim':      '#525252',
            'text_muted':    '#404040',
            'meta':          '#525252',
            'select_bg':     '#1d3148',
            'copy_btn_bg':   '#1a1a1a',
            'copy_btn_bdr':  '#2d2d2d',
            'pin_gold':      '#e3b341',
            'pin_gold_lit':  '#ffd76b',
            'pin_bg':        'transparent',
            'pin_bdr':       '#3a321a',
            'pin_bg_act':    '#2a2010',
            'clear_color':   '#f87171',
            'clear_bdr':     '#3d2020',
            'clear_bg_hv':   '#2a1414',
            'quit_color':    '#737373',
            'quit_bdr':      '#2d2d2d',
            'quit_bg_hv':    '#1a1a1a',
            'status_bg':     '#0a0a0a',
            'status_color':  '#4d4d4d',
            'status_bdr':    '#1a1a1a',
            'scroll_bg':     '#111111',
            'scroll_handle': '#2d2d2d',
            'scroll_hover':  '#60a5fa',
            'pinned_bg':     '#0d0d0d',
            'section_title': '#e3b341',
            'section_meta':  '#525252',
            'idx_color':     '#2d2d2d',
            'dialog_bg':     '#111111',
            'spin_bg':       '#1a1a1a',
            'spin_bdr':      '#2d2d2d',
            'spin_up_bg':    '#2d2d2d',
            'sep_color':     '#2d2d2d',
            'theme_btn_bg':  '#1a1a1a',
            'theme_btn_clr': '#737373',
            'settings_lbl':  '#e5e5e5',
        }

    return f"""
QMainWindow, QWidget#root {{
    background-color: {c['bg']};
}}

/* Header */
QWidget#header {{
    background-color: {c['surface']};
    border-bottom: 1px solid {c['border']};
}}
QLabel#title {{
    color: {c['accent']};
    font-size: 14px;
    font-weight: bold;
    font-family: 'Courier New', monospace;
    letter-spacing: 2px;
    padding: 0 4px;
}}
QLabel#count {{
    color: {c['text_dim']};
    font-size: 10px;
    font-family: 'Courier New', monospace;
}}

/* Search bar */
QWidget#searchbar {{
    background-color: {c['bg']};
    border-bottom: 1px solid {c['border2']};
}}
QLineEdit#search {{
    background-color: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 12px;
    font-family: 'Courier New', monospace;
    selection-background-color: {c['select_bg']};
}}
QLineEdit#search:focus {{
    border-color: {c['accent']};
    background-color: {c['surface2']};
}}

/* List */
QListWidget {{
    background-color: {c['bg']};
    border: none;
    outline: 0;
    font-family: 'Courier New', monospace;
}}
QListWidget::item {{
    border-bottom: 1px solid {c['surface']};
    padding: 0px;
    color: {c['text']};
}}
QListWidget::item:hover {{
    background-color: {c['surface']};
}}
QListWidget::item:selected {{
    background-color: {c['select_bg']};
    border-left: 3px solid {c['accent']};
    color: {c['text']};
}}

/* Scrollbar */
QScrollBar:vertical {{
    background: {c['scroll_bg']};
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {c['scroll_handle']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['scroll_hover']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* Buttons */
QPushButton#copy_btn {{
    background-color: {c['copy_btn_bg']};
    color: {c['accent']};
    border: 1px solid {c['copy_btn_bdr']};
    border-radius: 4px;
    padding: 0px;
    min-width: 32px;
}}
QPushButton#copy_btn:hover {{
    background-color: {c['accent']};
    color: {c['bg']};
    border-color: {c['accent']};
}}
QPushButton#pin_btn {{
    background-color: {c['pin_bg']};
    color: {c['pin_gold']};
    border: 1px solid {c['pin_bdr']};
    border-radius: 4px;
    padding: 0px;
    min-width: 32px;
}}
QPushButton#pin_btn:hover {{
    background-color: {c['pin_bg_act']};
    border-color: {c['pin_gold']};
}}
QPushButton#pin_btn[pinned="true"] {{
    background-color: {c['pin_bg_act']};
    color: {c['pin_gold_lit']};
    border-color: {c['pin_gold_lit']};
}}
QPushButton#clear_btn {{
    background-color: transparent;
    color: {c['clear_color']};
    border: 1px solid {c['clear_bdr']};
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 10px;
    font-family: 'Courier New', monospace;
}}
QPushButton#clear_btn:hover {{
    background-color: {c['clear_bg_hv']};
    border-color: {c['clear_color']};
}}
QPushButton#quit_btn {{
    background-color: transparent;
    color: {c['quit_color']};
    border: 1px solid {c['quit_bdr']};
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 10px;
    font-family: 'Courier New', monospace;
}}
QPushButton#quit_btn:hover {{
    background-color: {c['quit_bg_hv']};
    color: {c['text']};
    border-color: {c['accent']};
}}
QPushButton#settings_btn {{
    background-color: transparent;
    color: {c['accent']};
    border: 1px solid {c['copy_btn_bdr']};
    border-radius: 5px;
    padding: 4px 10px;
    font-size: 20px;
    font-family: 'Courier New', monospace;
}}
QPushButton#settings_btn:hover {{
    background-color: {c['copy_btn_bg']};
    border-color: {c['accent']};
}}

/* Status bar */
QLabel#status {{
    background-color: {c['status_bg']};
    color: {c['status_color']};
    font-size: 10px;
    font-family: 'Courier New', monospace;
    padding: 5px 12px;
    border-top: 1px solid {c['status_bdr']};
}}

/* Row labels */
QLabel#idx {{
    color: {c['idx_color']};
    font-size: 9px;
    font-family: 'Courier New', monospace;
    min-width: 26px;
    padding-left: 4px;
}}
QLabel#preview {{
    color: {c['text']};
    font-size: {font_size}pt;
    font-family: 'Courier New', monospace;
}}
QLabel#meta {{
    color: {c['meta']};
    font-size: 9px;
    font-family: 'Courier New', monospace;
}}

/* Pinned section */
QWidget#pinned_section {{
    background-color: {c['pinned_bg']};
    border-bottom: 1px solid {c['border2']};
}}
QLabel#section_title {{
    color: {c['section_title']};
    font-size: 10px;
    font-weight: bold;
    font-family: 'Courier New', monospace;
    letter-spacing: 1px;
}}
QLabel#section_meta {{
    color: {c['section_meta']};
    font-size: 9px;
    font-family: 'Courier New', monospace;
}}

/* Settings dialog */
QDialog {{
    background-color: {c['dialog_bg']};
}}
QLabel#settings_label {{
    color: {c['settings_lbl']};
    font-size: 12px;
    font-family: 'Courier New', monospace;
}}
QLabel#settings_section {{
    color: {c['accent']};
    font-size: 10px;
    font-weight: bold;
    font-family: 'Courier New', monospace;
    letter-spacing: 1px;
}}
QSpinBox {{
    background-color: {c['spin_bg']};
    color: {c['text']};
    border: 1px solid {c['spin_bdr']};
    border-radius: 4px;
    padding: 4px 8px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    min-width: 80px;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {c['spin_up_bg']};
    border: none;
    width: 16px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {c['accent']};
}}
QFrame#separator {{
    color: {c['sep_color']};
    background-color: {c['sep_color']};
    border: none;
    max-height: 1px;
}}
QPushButton#theme_btn {{
    background-color: {c['theme_btn_bg']};
    color: {c['theme_btn_clr']};
    border: 1px solid {c['copy_btn_bdr']};
    border-radius: 4px;
    padding: 6px 20px;
    font-size: 11px;
    font-family: 'Courier New', monospace;
    min-width: 70px;
}}
QPushButton#theme_btn:checked {{
    background-color: {c['accent']};
    color: {c['bg']};
    border-color: {c['accent']};
}}
QPushButton#theme_btn:hover:!checked {{
    border-color: {c['accent']};
    color: {c['text']};
}}
QPushButton#primary_btn {{
    background-color: {c['accent']};
    color: {c['bg']};
    border: 1px solid {c['accent']};
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 10px;
    font-family: 'Courier New', monospace;
}}
QPushButton#primary_btn:hover {{
    background-color: {c['accent_hover']};
    border-color: {c['accent_hover']};
}}
"""


# ── Tray icon generator ───────────────────────────────────────────────────────
def make_tray_icon():
    accent = '#60a5fa' if settings.theme == 'dark' else '#4169e1'
    bg     = '#111111' if settings.theme == 'dark' else '#f5f0eb'
    px = QPixmap(22, 22)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(QColor(accent)))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(3, 5, 16, 15, 2, 2)
    p.setBrush(QBrush(QColor(bg)))
    p.drawRoundedRect(7, 3, 8, 5, 2, 2)
    p.setBrush(QBrush(QColor(accent)))
    p.drawRect(8, 4, 6, 3)
    p.setBrush(QBrush(QColor(bg)))
    p.drawRect(6, 10, 10, 2)
    p.drawRect(6, 14, 10, 2)
    p.end()
    return QIcon(px)


def make_pin_button_icon(pinned=False):
    import math
    px = QPixmap(16, 16)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    color = QColor('#ffd76b' if pinned else '#e3b341')
    p.setPen(QPen(color, 1.0))
    p.setBrush(QBrush(color) if pinned else Qt.NoBrush)

    cx, cy = 8.0, 7.5
    R, r = 6.5, 2.7
    path = QPainterPath()
    for i in range(5):
        outer_a = math.radians(-90 + i * 72)
        inner_a = math.radians(-90 + 36 + i * 72)
        ox, oy = cx + R * math.cos(outer_a), cy + R * math.sin(outer_a)
        ix, iy = cx + r * math.cos(inner_a), cy + r * math.sin(inner_a)
        if i == 0:
            path.moveTo(ox, oy)
        else:
            path.lineTo(ox, oy)
        path.lineTo(ix, iy)
    path.closeSubpath()
    p.drawPath(path)
    p.end()
    return QIcon(px)


def make_copy_button_icon():
    accent = '#60a5fa' if settings.theme == 'dark' else '#4169e1'
    px = QPixmap(16, 16)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor(accent))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(5, 3, 7, 8, 1, 1)
    p.drawRoundedRect(3, 5, 7, 8, 1, 1)
    p.end()
    return QIcon(px)


# ── Row widget ────────────────────────────────────────────────────────────────
class RowWidget(QWidget):
    copy_requested = pyqtSignal(dict)
    pin_requested  = pyqtSignal(dict)

    def __init__(self, entry: dict, index: int, show_index=True, parent=None):
        super().__init__(parent)
        self.entry = entry
        self._build(index)

    def _build(self, idx):
        h = QHBoxLayout(self)
        h.setContentsMargins(8, 8, 8, 8)
        h.setSpacing(6)

        pin_btn = QPushButton()
        pin_btn.setObjectName('pin_btn')
        pin_btn.setProperty('pinned', 'true' if self.entry.get('pinned') else 'false')
        pin_btn.setIcon(make_pin_button_icon(self.entry.get('pinned')))
        pin_btn.setIconSize(QSize(16, 16))
        pin_btn.setToolTip('Unpin item' if self.entry.get('pinned') else 'Pin item')
        pin_btn.setFixedSize(ACTION_BTN_WIDTH, 28)
        pin_btn.setFocusPolicy(Qt.NoFocus)
        pin_btn.setCursor(Qt.PointingHandCursor)
        pin_btn.clicked.connect(lambda: self.pin_requested.emit(self.entry))
        h.addWidget(pin_btn, alignment=Qt.AlignVCenter)

        v = QVBoxLayout()
        v.setSpacing(3)
        v.setContentsMargins(0, 0, 0, 0)

        if self.entry.get('type') == 'image':
            thumb_lbl = QLabel()
            thumb_lbl.setObjectName('preview')
            img_path = os.path.join(IMAGES_DIR, self.entry.get('image_file', ''))
            px = QPixmap(img_path)
            if not px.isNull():
                px = px.scaled(160, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumb_lbl.setPixmap(px)
            else:
                thumb_lbl.setText('[image not found]')
            v.addWidget(thumb_lbl)

            try:
                dt = datetime.fromisoformat(self.entry['timestamp'])
                ts = dt.strftime('%d %b %Y  %H:%M')
            except Exception:
                ts = '—'
            w = self.entry.get('width', '?')
            ht = self.entry.get('height', '?')
            meta_lbl = QLabel(f'{ts}  ·  {w} × {ht} px')
            meta_lbl.setObjectName('meta')
            meta_lbl.setVisible(settings.show_metadata)
            v.addWidget(meta_lbl)
        else:
            if settings.word_wrap:
                preview_text = self.entry['text'].replace('\t', '    ')
            else:
                preview_text = self.entry['text'][:180].replace('\n', '  ↵  ').replace('\t', '  →  ')
            preview_lbl = QLabel(preview_text)
            preview_lbl.setObjectName('preview')
            preview_lbl.setWordWrap(settings.word_wrap)
            preview_lbl.setMaximumWidth(430)
            font = preview_lbl.font()
            font.setPointSize(settings.font_size)
            preview_lbl.setFont(font)
            v.addWidget(preview_lbl)

            try:
                dt = datetime.fromisoformat(self.entry['timestamp'])
                ts = dt.strftime('%d %b %Y  %H:%M')
            except Exception:
                ts = '—'
            chars = len(self.entry['text'])
            lines = self.entry['text'].count('\n') + 1
            line_str = f'  ·  {lines} lines' if lines > 1 else ''
            meta_lbl = QLabel(f'{ts}  ·  {chars} chars{line_str}')
            meta_lbl.setObjectName('meta')
            meta_lbl.setVisible(settings.show_metadata)
            v.addWidget(meta_lbl)

        h.addLayout(v, stretch=1)

        btn = QPushButton()
        btn.setObjectName('copy_btn')
        btn.setIcon(make_copy_button_icon())
        btn.setIconSize(QSize(14, 14))
        btn.setToolTip('Copy item')
        btn.setFixedSize(ACTION_BTN_WIDTH, 28)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.copy_requested.emit(self.entry))
        h.addWidget(btn, alignment=Qt.AlignVCenter)

        if settings.word_wrap and self.entry.get('type') != 'image':
            fm = preview_lbl.fontMetrics()
            rect = fm.boundingRect(
                0, 0, 430, 100000,
                Qt.TextWordWrap | Qt.AlignLeft,
                preview_text,
            )
            row_h = max(ROW_HEIGHT, rect.height() + 32)
        else:
            row_h = ROW_HEIGHT
        self.setFixedHeight(row_h)


# ── Confirm Dialog ────────────────────────────────────────────────────────────
class ConfirmDialog(QDialog):
    """A themed confirmation dialog that appears centered over its parent."""
    def __init__(self, title, body, parent=None):
        super().__init__(parent)
        self.setWindowTitle('ClipKeeper')
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setFixedWidth(320)
        self._accepted = False
        self._build(title, body)
        self.setStyleSheet(build_stylesheet(settings.theme, settings.font_size))

    def _build(self, title, body):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QWidget()
        header.setObjectName('header')
        header.setFixedHeight(46)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        lbl = QLabel(title)
        lbl.setObjectName('title')
        hl.addWidget(lbl)
        layout.addWidget(header)

        # Body
        body_widget = QWidget()
        body_widget.setObjectName('root')
        bl = QVBoxLayout(body_widget)
        bl.setSpacing(16)
        bl.setContentsMargins(20, 20, 20, 20)

        msg = QLabel(body)
        msg.setObjectName('settings_label')
        msg.setWordWrap(True)
        bl.addWidget(msg)

        sep = QFrame()
        sep.setObjectName('separator')
        sep.setFrameShape(QFrame.HLine)
        bl.addWidget(sep)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        no_btn = QPushButton('No')
        no_btn.setObjectName('quit_btn')
        no_btn.setFixedSize(90, 32)
        no_btn.setFocusPolicy(Qt.NoFocus)
        no_btn.setCursor(Qt.PointingHandCursor)
        no_btn.clicked.connect(self.reject)
        btn_row.addWidget(no_btn)

        yes_btn = QPushButton('Yes')
        yes_btn.setObjectName('clear_btn')
        yes_btn.setFixedSize(90, 32)
        yes_btn.setFocusPolicy(Qt.NoFocus)
        yes_btn.setCursor(Qt.PointingHandCursor)
        yes_btn.clicked.connect(self._on_yes)
        btn_row.addWidget(yes_btn)

        bl.addLayout(btn_row)
        layout.addWidget(body_widget)

    def _on_yes(self):
        self._accepted = True
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        # Center over parent window
        parent = self.parent()
        if parent:
            pg = parent.frameGeometry()
            self.move(
                pg.x() + (pg.width() - self.width()) // 2,
                pg.y() + (pg.height() - self.height()) // 2,
            )


# ── Settings Dialog ───────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle('ClipKeeper — Settings')
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.setFixedWidth(420)

        # Snapshot for cancel
        self._orig = dict(settings._data)

        self._build()
        self.setStyleSheet(build_stylesheet(settings.theme, settings.font_size))

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QWidget()
        header.setObjectName('header')
        header.setFixedHeight(46)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        title = QLabel('[ SETTINGS ]')
        title.setObjectName('title')
        hl.addWidget(title)
        layout.addWidget(header)

        # ── Body ──────────────────────────────────────────────────────────────
        body = QWidget()
        body.setObjectName('root')
        bl = QVBoxLayout(body)
        bl.setSpacing(14)
        bl.setContentsMargins(20, 20, 20, 20)

        # Theme
        bl.addWidget(self._section_label('APPEARANCE'))
        bl.addLayout(self._row(
            'Theme',
            self._theme_toggle(),
        ))

        bl.addWidget(self._section_label('CONTENT'))
        bl.addLayout(self._row(
            'Font size of copied items',
            self._spin('font_size', 8, 24, ' pt'),
        ))
        bl.addLayout(self._row(
            'Max history items',
            self._spin('max_items', 10, 1000),
        ))
        bl.addLayout(self._row(
            'Max pinned items',
            self._spin('max_pinned', 1, 50),
        ))
        bl.addLayout(self._row(
            'Show item metadata',
            self._metadata_toggle(),
        ))
        bl.addLayout(self._row(
            'Word wrap text items',
            self._wordwrap_toggle(),
        ))

        bl.addWidget(self._section_label('LAYOUT'))
        bl.addLayout(self._row(
            'Panel width',
            self._spin('panel_width', 25, 60, ' %'),
        ))
        bl.addLayout(self._row(
            'Panel height',
            self._spin('panel_height', 50, 100, ' %'),
        ))

        # Separator
        sep = QFrame()
        sep.setObjectName('separator')
        sep.setFrameShape(QFrame.HLine)
        bl.addSpacing(4)
        bl.addWidget(sep)
        bl.addSpacing(4)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        cancel_btn = QPushButton('Cancel')
        cancel_btn.setObjectName('quit_btn')
        cancel_btn.setFixedSize(120, 32)
        cancel_btn.setFocusPolicy(Qt.NoFocus)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self._cancel)
        btn_row.addWidget(cancel_btn)

        apply_btn = QPushButton('Apply')
        apply_btn.setObjectName('primary_btn')
        apply_btn.setFixedSize(120, 32)
        apply_btn.setFocusPolicy(Qt.NoFocus)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.clicked.connect(self._apply_and_close)
        btn_row.addWidget(apply_btn)

        bl.addLayout(btn_row)
        layout.addWidget(body)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName('settings_section')
        return lbl

    def _row(self, label_text, widget):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = QLabel(label_text)
        lbl.setObjectName('settings_label')
        row.addWidget(lbl, stretch=1)
        row.addWidget(widget)
        return row

    def _spin(self, key, min_val, max_val, suffix=''):
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(settings._data[key])
        if suffix:
            spin.setSuffix(suffix)
        spin.setFocusPolicy(Qt.StrongFocus)
        spin.valueChanged.connect(lambda v, k=key: self._on_spin_changed(k, v))
        setattr(self, f'_spin_{key}', spin)
        return spin

    def _theme_toggle(self):
        container = QWidget()
        container.setObjectName('root')
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)

        self._light_btn = QPushButton('Light')
        self._light_btn.setObjectName('theme_btn')
        self._light_btn.setCheckable(True)
        self._light_btn.setChecked(settings.theme == 'light')
        self._light_btn.setFocusPolicy(Qt.NoFocus)
        self._light_btn.setCursor(Qt.PointingHandCursor)

        self._dark_btn = QPushButton('Dark')
        self._dark_btn.setObjectName('theme_btn')
        self._dark_btn.setCheckable(True)
        self._dark_btn.setChecked(settings.theme == 'dark')
        self._dark_btn.setFocusPolicy(Qt.NoFocus)
        self._dark_btn.setCursor(Qt.PointingHandCursor)

        self._light_btn.clicked.connect(lambda: self._set_theme('light'))
        self._dark_btn.clicked.connect(lambda: self._set_theme('dark'))

        row.addWidget(self._light_btn)
        row.addWidget(self._dark_btn)
        return container

    def _metadata_toggle(self):
        container = QWidget()
        container.setObjectName('root')
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)

        self._meta_show_btn = QPushButton('Show')
        self._meta_show_btn.setObjectName('theme_btn')
        self._meta_show_btn.setCheckable(True)
        self._meta_show_btn.setChecked(settings.show_metadata)
        self._meta_show_btn.setFocusPolicy(Qt.NoFocus)
        self._meta_show_btn.setCursor(Qt.PointingHandCursor)

        self._meta_hide_btn = QPushButton('Hide')
        self._meta_hide_btn.setObjectName('theme_btn')
        self._meta_hide_btn.setCheckable(True)
        self._meta_hide_btn.setChecked(not settings.show_metadata)
        self._meta_hide_btn.setFocusPolicy(Qt.NoFocus)
        self._meta_hide_btn.setCursor(Qt.PointingHandCursor)

        self._meta_show_btn.clicked.connect(lambda: self._set_metadata(True))
        self._meta_hide_btn.clicked.connect(lambda: self._set_metadata(False))

        row.addWidget(self._meta_show_btn)
        row.addWidget(self._meta_hide_btn)
        return container

    def _wordwrap_toggle(self):
        container = QWidget()
        container.setObjectName('root')
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)

        self._wrap_on_btn = QPushButton('On')
        self._wrap_on_btn.setObjectName('theme_btn')
        self._wrap_on_btn.setCheckable(True)
        self._wrap_on_btn.setChecked(settings.word_wrap)
        self._wrap_on_btn.setFocusPolicy(Qt.NoFocus)
        self._wrap_on_btn.setCursor(Qt.PointingHandCursor)

        self._wrap_off_btn = QPushButton('Off')
        self._wrap_off_btn.setObjectName('theme_btn')
        self._wrap_off_btn.setCheckable(True)
        self._wrap_off_btn.setChecked(not settings.word_wrap)
        self._wrap_off_btn.setFocusPolicy(Qt.NoFocus)
        self._wrap_off_btn.setCursor(Qt.PointingHandCursor)

        self._wrap_on_btn.clicked.connect(lambda: self._set_wordwrap(True))
        self._wrap_off_btn.clicked.connect(lambda: self._set_wordwrap(False))

        row.addWidget(self._wrap_on_btn)
        row.addWidget(self._wrap_off_btn)
        return container

    # ── Live apply ────────────────────────────────────────────────────────────
    def _set_theme(self, theme):
        self._light_btn.setChecked(theme == 'light')
        self._dark_btn.setChecked(theme == 'dark')
        settings._data['theme'] = theme
        self._apply_stylesheet()

    def _set_metadata(self, show):
        self._meta_show_btn.setChecked(show)
        self._meta_hide_btn.setChecked(not show)
        settings._data['show_metadata'] = show

    def _set_wordwrap(self, wrap):
        self._wrap_on_btn.setChecked(wrap)
        self._wrap_off_btn.setChecked(not wrap)
        settings._data['word_wrap'] = wrap

    def _on_spin_changed(self, key, value):
        settings._data[key] = value
        if key == 'font_size':
            self._apply_stylesheet()
        # panel_width, panel_height, max_items, max_pinned are applied on Apply & Close
        # so the list doesn't jump around while the user is typing

    def _apply_stylesheet(self):
        qss = build_stylesheet(settings.theme, settings.font_size)
        QApplication.instance().setStyleSheet(qss)
        self.setStyleSheet(qss)
        if self.manager.window:
            self.manager.window.setStyleSheet(qss)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _apply_and_close(self):
        settings.save()
        self._apply_stylesheet()
        if self.manager.window:
            self.manager._position_window()
            self.manager.window.refresh()
        self.accept()

    def _cancel(self):
        # Restore all settings to snapshot
        settings._data.update(self._orig)
        self._apply_stylesheet()
        self.reject()


# ── Main Window ───────────────────────────────────────────────────────────────
class ClipboardWindow(QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle('ClipKeeper')
        self.setWindowIcon(make_tray_icon())
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)
        self.setMinimumSize(300, 300)
        self.resize(400, 600)
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._reset_status)
        self._hide_guard_until = 0.0
        self._modal_open = False      # True while any child dialog is visible
        self._build_ui()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        root.setObjectName('root')
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._header())
        layout.addWidget(self._searchbar())
        layout.addWidget(self._pinned_section())
        layout.addWidget(self._list_area(), stretch=1)
        layout.addWidget(self._statusbar())

    def _header(self):
        w = QWidget()
        w.setObjectName('header')
        w.setFixedHeight(50)
        h = QHBoxLayout(w)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(8)

        title = QLabel('[ CLIPBOARD ]')
        title.setObjectName('title')
        h.addWidget(title)
        h.addStretch()

        self._count_lbl = QLabel()
        self._count_lbl.setObjectName('count')
        h.addWidget(self._count_lbl)

        settings_btn = QPushButton('⚙')
        settings_btn.setObjectName('settings_btn')
        settings_btn.setFixedSize(34, 34)
        settings_btn.setFocusPolicy(Qt.NoFocus)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setToolTip('Settings')
        settings_btn.clicked.connect(self.manager.open_settings)
        h.addWidget(settings_btn)
        return w

    def _searchbar(self):
        w = QWidget()
        w.setObjectName('searchbar')
        h = QHBoxLayout(w)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(10)

        self._search = QLineEdit()
        self._search.setObjectName('search')
        self._search.setPlaceholderText('  Search  /  type to filter…')
        self._search.textChanged.connect(self._filter)
        h.addWidget(self._search)

        clear_btn = QPushButton('Clear All')
        clear_btn.setObjectName('clear_btn')
        clear_btn.setFocusPolicy(Qt.NoFocus)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self.manager.confirm_clear)
        h.addWidget(clear_btn)

        quit_btn = QPushButton('Quit')
        quit_btn.setObjectName('quit_btn')
        quit_btn.setFocusPolicy(Qt.NoFocus)
        quit_btn.setCursor(Qt.PointingHandCursor)
        quit_btn.clicked.connect(self.manager.quit_app)
        h.addWidget(quit_btn)
        return w

    def _list_area(self):
        self._list = QListWidget()
        self._list.setObjectName('list')
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.itemActivated.connect(lambda item: self._copy(item.data(Qt.UserRole)))
        self._list.itemDoubleClicked.connect(lambda item: self._copy(item.data(Qt.UserRole)))
        return self._list

    def _pinned_section(self):
        section = QWidget()
        section.setObjectName('pinned_section')
        layout = QVBoxLayout(section)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self._pinned_title = QLabel('PINNED')
        self._pinned_title.setObjectName('section_title')
        header.addWidget(self._pinned_title)
        header.addStretch()

        self._pinned_meta = QLabel(f'0 / {settings.max_pinned}')
        self._pinned_meta.setObjectName('section_meta')
        header.addWidget(self._pinned_meta)
        layout.addLayout(header)

        self._pinned_list = QListWidget()
        self._pinned_list.setObjectName('list')
        self._pinned_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._pinned_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._pinned_list.setSelectionMode(QAbstractItemView.NoSelection)
        self._pinned_list.setMinimumHeight(0)
        self._pinned_list.setMaximumHeight((ROW_HEIGHT * 4) + 4)
        layout.addWidget(self._pinned_list)

        self._pinned_section_widget = section
        return section

    def _statusbar(self):
        self._status = QLabel('↵  click or double-click to copy  ·  history persists across reboots')
        self._status.setObjectName('status')
        return self._status

    # ── Refresh ───────────────────────────────────────────────────────────────
    def refresh(self):
        self._pinned_list.clear()
        self._list.clear()
        q = self._search.text().lower()
        pinned_entries = self.manager.filtered_pinned_entries(q)
        normal_entries = self.manager.filtered_history_entries(q)

        pinned_row_heights = []
        for i, entry in enumerate(pinned_entries):
            row_widget = RowWidget(entry, i, show_index=False)
            row_widget.copy_requested.connect(self._copy)
            row_widget.pin_requested.connect(self._toggle_pin)
            item = QListWidgetItem(self._pinned_list)
            item.setData(Qt.UserRole, entry)
            rh = row_widget.minimumHeight()
            item.setSizeHint(QSize(self._pinned_list.width(), rh))
            self._pinned_list.addItem(item)
            self._pinned_list.setItemWidget(item, row_widget)
            pinned_row_heights.append(rh)

        for i, entry in enumerate(normal_entries):
            row_widget = RowWidget(entry, i)
            row_widget.copy_requested.connect(self._copy)
            row_widget.pin_requested.connect(self._toggle_pin)
            item = QListWidgetItem(self._list)
            item.setData(Qt.UserRole, entry)
            item.setSizeHint(QSize(self._list.width(), row_widget.minimumHeight()))
            self._list.addItem(item)
            self._list.setItemWidget(item, row_widget)

        n = len(self.manager.history)
        self._count_lbl.setText(f'{n} / {settings.max_items}')
        pinned_total = len(self.manager.pinned_entries())
        visible_rows = min(len(pinned_entries), 4)
        self._pinned_meta.setText(f'{pinned_total} / {settings.max_pinned}')
        pinned_max_h = sum(pinned_row_heights[:4]) + 4 if visible_rows else 0
        self._pinned_list.setMaximumHeight(pinned_max_h)
        self._pinned_section_widget.setVisible(bool(pinned_total))

    def _filter(self, text):
        self.refresh()

    # ── Copy ──────────────────────────────────────────────────────────────────
    def _copy(self, entry):
        if not entry:
            return
        if entry.get('type') == 'image':
            self._copy_image(entry)
            return
        if not entry.get('text'):
            return
        self._hide_guard_until = time.monotonic() + 0.35
        self.manager.suspend_capture(entry['text'])
        QApplication.clipboard().setText(entry['text'])
        self.manager.last_text = entry['text']

        preview = entry['text'][:50].replace('\n', ' ')
        self._status.setText(f'✓  Copied:  {preview}…')
        self._status.setStyleSheet(
            'color: #4ade80; background-color: #091209; '
            'border-top: 1px solid #12141f; padding: 5px 12px; '
            'font-family: "Courier New", monospace; font-size: 10px;'
        )
        self._status_timer.start(2500)

    def _copy_image(self, entry):
        img_path = os.path.join(IMAGES_DIR, entry.get('image_file', ''))
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            self._show_status('Image file not found', success=False)
            return
        self._hide_guard_until = time.monotonic() + 0.35
        self.manager.suspend_capture_image(entry.get('image_hash', ''))
        QApplication.clipboard().setPixmap(pixmap)
        w = entry.get('width', '?')
        ht = entry.get('height', '?')
        self._show_status(f'✓  Copied image  ({w} × {ht} px)', success=True)

    def _reset_status(self):
        self._status.setText('↵  click or double-click to copy  ·  history persists across reboots')
        self._status.setStyleSheet('')

    def _show_status(self, text, success=False):
        color = '#4ade80' if success else '#e3b341'
        bg    = '#091209' if success else '#141108'
        self._status.setText(text)
        self._status.setStyleSheet(
            f'color: {color}; background-color: {bg}; border-top: 1px solid #12141f; '
            'padding: 5px 12px; font-family: "Courier New", monospace; font-size: 10px;'
        )
        self._status_timer.start(2500)

    def _toggle_pin(self, entry):
        self._hide_guard_until = time.monotonic() + 0.35
        pinned, message = self.manager.toggle_pin(entry)
        self.refresh()
        self._show_status(message, success=pinned)

    def closeEvent(self, event):
        if self.manager.quitting:
            event.accept()
        elif self.manager.daemon_mode:
            event.ignore()
            self.hide()
        else:
            event.accept()
            QTimer.singleShot(0, self.manager.app.quit)

    def event(self, event):
        if (
            event.type() == QEvent.WindowDeactivate
            and self.isVisible()
            and not self.manager.quitting
            and not self._modal_open
            and time.monotonic() >= self._hide_guard_until
            and not self.isAncestorOf(QApplication.focusWidget())
        ):
            if self.manager.daemon_mode:
                self.hide()
            else:
                self.close()
        return super().event(event)


# ── Clipboard Manager ─────────────────────────────────────────────────────────
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
                                continue  # skip entries whose file was deleted
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
        self.history = self.history[:settings.max_items]
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
        # Serialise to PNG bytes for hashing
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

        # Remove any previous entry with the same hash (dedup)
        self.history = [
            h for h in self.history
            if not (h.get('type') == 'image' and h.get('image_hash') == img_hash)
        ]
        self.history.insert(0, {
            'type':      'image',
            'image_file': filename,
            'image_hash': img_hash,
            'timestamp': datetime.now().isoformat(),
            'pinned':    False,
            'pinned_at': None,
            'width':     pixmap.width(),
            'height':    pixmap.height(),
        })
        self.history = self.history[:settings.max_items]
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
        # Image entries have no text to search — exclude them when a query is active
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
            # Short grace period so the window doesn't vanish the instant
            # focus returns to it after the dialog closes.
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


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    daemon_mode = '--daemon' in sys.argv[1:]
    QApplication.setQuitOnLastWindowClosed(False)

    app = QApplication(sys.argv)
    app.setApplicationName('ClipKeeper')
    app.setStyleSheet(build_stylesheet(settings.theme, settings.font_size))

    manager = ClipboardManager(app, daemon_mode=daemon_mode)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
