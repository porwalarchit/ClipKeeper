import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap

from .constants import IMAGES_DIR, ROW_HEIGHT, ACTION_BTN_WIDTH
from .settings import settings
from .icons import make_pin_button_icon, make_copy_button_icon


class RowWidget(QWidget):
    copy_requested = pyqtSignal(dict)
    pin_requested  = pyqtSignal(dict)

    def __init__(self, entry: dict, index: int, show_index=True, parent=None):
        super().__init__(parent)
        self.entry = entry
        self._build(index)

    def _build(self, idx):
        h = QHBoxLayout(self)
        h.setContentsMargins(8, 6, 8, 6)
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
        v.addStretch(1)

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

        v.addStretch(1)
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
            wrap_w = max(200, self.width() - 2 * ACTION_BTN_WIDTH - 3 * 6)
            rect = fm.boundingRect(
                0, 0, wrap_w, 100000,
                Qt.TextWordWrap | Qt.AlignLeft,
                preview_text,
            )
            row_h = max(ROW_HEIGHT, rect.height() + 32)
        else:
            row_h = ROW_HEIGHT
        self.setFixedHeight(row_h)
