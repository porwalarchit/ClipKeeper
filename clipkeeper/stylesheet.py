def build_stylesheet(theme: str, font_size: int) -> str:
    """Return a complete QSS string for the given theme and font size.
    All UI text sizes scale proportionally from font_size via five tiers."""
    fs_sm   = max(7,  round(font_size * 0.75))
    fs_md   = max(8,  round(font_size * 0.85))
    fs_icon = max(14, round(font_size * 1.6))

    if theme == 'light':
        c = {
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
    font-size: 9pt;
    font-weight: bold;
    font-family: 'Courier New', monospace;
    letter-spacing: 2px;
    padding: 0 4px;
}}
QLabel#count {{
    color: {c['text_dim']};
    font-size: {fs_md}pt;
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
    font-size: 9pt;
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
    font-size: {fs_md}pt;
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
    font-size: {fs_md}pt;
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
    font-size: {fs_icon}pt;
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
    font-size: {fs_sm}pt;
    font-family: 'Courier New', monospace;
    padding: 5px 12px;
    border-top: 1px solid {c['status_bdr']};
}}

/* Row labels */
QLabel#idx {{
    color: {c['idx_color']};
    font-size: {fs_sm}pt;
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
    font-size: {fs_sm}pt;
    font-family: 'Courier New', monospace;
}}

/* Pinned section */
QWidget#pinned_section {{
    background-color: {c['pinned_bg']};
    border-bottom: 1px solid {c['border2']};
}}
QLabel#section_title {{
    color: {c['section_title']};
    font-size: {fs_md}pt;
    font-weight: bold;
    font-family: 'Courier New', monospace;
    letter-spacing: 1px;
}}
QLabel#section_meta {{
    color: {c['section_meta']};
    font-size: {fs_sm}pt;
    font-family: 'Courier New', monospace;
}}

/* Settings dialog */
QDialog {{
    background-color: {c['dialog_bg']};
}}
QLabel#settings_label {{
    color: {c['settings_lbl']};
    font-size: 9pt;
    font-family: 'Courier New', monospace;
}}
QLabel#settings_section {{
    color: {c['accent']};
    font-size: 8pt;
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
    font-size: 9pt;
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
    font-size: 9pt;
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
    font-size: 9pt;
    font-family: 'Courier New', monospace;
}}
QPushButton#primary_btn:hover {{
    background-color: {c['accent_hover']};
    border-color: {c['accent_hover']};
}}
"""
