from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QWidget, QSpinBox,
)
from PyQt5.QtCore import Qt

from .settings import settings
from .stylesheet import build_stylesheet


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

        header = QWidget()
        header.setObjectName('header')
        header.setFixedHeight(46)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        lbl = QLabel(title)
        lbl.setObjectName('title')
        hl.addWidget(lbl)
        layout.addWidget(header)

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
        parent = self.parent()
        if parent:
            pg = parent.frameGeometry()
            self.move(
                pg.x() + (pg.width() - self.width()) // 2,
                pg.y() + (pg.height() - self.height()) // 2,
            )


class SettingsDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle('ClipKeeper — Settings')
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.setFixedWidth(420)

        self._orig = dict(settings._data)

        self._build()
        self.setStyleSheet(build_stylesheet(settings.theme, settings.font_size))

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setObjectName('header')
        header.setFixedHeight(46)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)
        title = QLabel('[ SETTINGS ]')
        title.setObjectName('title')
        hl.addWidget(title)
        layout.addWidget(header)

        body = QWidget()
        body.setObjectName('root')
        bl = QVBoxLayout(body)
        bl.setSpacing(14)
        bl.setContentsMargins(20, 20, 20, 20)

        bl.addWidget(self._section_label('APPEARANCE'))
        bl.addLayout(self._row('Theme', self._theme_toggle()))

        bl.addWidget(self._section_label('CONTENT'))
        bl.addLayout(self._row('Font size (scales all UI text)', self._spin('font_size', 8, 24, ' pt')))
        bl.addLayout(self._row('Max history items', self._spin('max_items', 10, 1000)))
        bl.addLayout(self._row('Max pinned items', self._spin('max_pinned', 1, 50)))
        bl.addLayout(self._row('Show item metadata', self._metadata_toggle()))
        bl.addLayout(self._row('Word wrap text items', self._wordwrap_toggle()))

        bl.addWidget(self._section_label('LAYOUT'))
        bl.addLayout(self._row('Panel width', self._spin('panel_width', 25, 60, ' %')))
        bl.addLayout(self._row('Panel height', self._spin('panel_height', 50, 100, ' %')))

        sep = QFrame()
        sep.setObjectName('separator')
        sep.setFrameShape(QFrame.HLine)
        bl.addSpacing(4)
        bl.addWidget(sep)
        bl.addSpacing(4)

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

    def _apply_stylesheet(self):
        qss = build_stylesheet(settings.theme, settings.font_size)
        QApplication.instance().setStyleSheet(qss)
        self.setStyleSheet(qss)
        if self.manager.window:
            self.manager.window.setStyleSheet(qss)

    def _apply_and_close(self):
        settings.save()
        self._apply_stylesheet()
        if self.manager.window:
            self.manager._position_window()
            self.manager.window.refresh()
        self.accept()

    def _cancel(self):
        settings._data.update(self._orig)
        self._apply_stylesheet()
        self.reject()
