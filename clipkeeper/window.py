import os
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, QTimer, QSize, QEvent

from .constants import IMAGES_DIR, ROW_HEIGHT
from .settings import settings
from .icons import make_tray_icon
from .widgets import RowWidget


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
        self._modal_open = False
        self._build_ui()

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
        from PyQt5.QtGui import QPixmap
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
